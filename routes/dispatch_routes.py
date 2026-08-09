from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required
from datetime import datetime

from extensions import db
from models.fleet_job import FleetJob
from routes.settings_routes import business_settings


dispatch_bp = Blueprint('dispatch_bp', __name__)


def _is_admin():
    claims = get_jwt()
    return (claims.get('role') or '').lower() == 'admin'


def _require_admin():
    if not _is_admin():
        return jsonify({'error': 'admin access required'}), 403
    return None


def _dispatch_config():
    dispatch = business_settings.setdefault('dispatch', {
        'enabled': True,
        'acceptLocalCalls': True,
        'serviceAreas': ['Rocky Mount', 'Nash County', 'Wilson', 'Greenville'],
        'fleetSources': ['Amazon Flex', 'Local Taxi', 'Airport Shuttle', 'Medical Ride'],
        'partnerChannels': ['uber_partner', 'lyft_partner', 'local_transport', 'amazon_flex'],
        'dispatchPhone': business_settings.get('phone', '252 886-5996'),
        'promotionMessage': 'Ride with Traveling Star Service for fast local dispatch and reliable pickup windows.',
        'promotionCampaigns': [],
        'meter': {
            'baseFare': 4.5,
            'perMile': 2.75,
            'perMinute': 0.55,
            'minimumFare': 9.0,
            'surgeMultiplier': 1.0,
            'bookingFee': 1.5
        }
    })
    meter = dispatch.setdefault('meter', {})
    meter.setdefault('baseFare', 4.5)
    meter.setdefault('perMile', 2.75)
    meter.setdefault('perMinute', 0.55)
    meter.setdefault('minimumFare', 9.0)
    meter.setdefault('surgeMultiplier', 1.0)
    meter.setdefault('bookingFee', 1.5)
    dispatch.setdefault('partnerChannels', ['uber_partner', 'lyft_partner', 'local_transport', 'amazon_flex'])
    dispatch.setdefault('promotionMessage', 'Ride with Traveling Star Service for fast local dispatch and reliable pickup windows.')
    dispatch.setdefault('promotionCampaigns', [])
    return dispatch


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _calc_meter(distance_miles, duration_minutes, surge_multiplier=None):
    dispatch = _dispatch_config()
    meter = dispatch['meter']

    base_fare = _to_float(meter.get('baseFare'), 4.5)
    per_mile = _to_float(meter.get('perMile'), 2.75)
    per_minute = _to_float(meter.get('perMinute'), 0.55)
    minimum_fare = _to_float(meter.get('minimumFare'), 9.0)
    booking_fee = _to_float(meter.get('bookingFee'), 1.5)
    default_surge = _to_float(meter.get('surgeMultiplier'), 1.0)
    surge = _to_float(surge_multiplier, default_surge) if surge_multiplier is not None else default_surge

    subtotal = base_fare + (per_mile * max(distance_miles, 0.0)) + (per_minute * max(duration_minutes, 0.0)) + booking_fee
    total = max(minimum_fare, subtotal) * max(surge, 0.1)
    return round(total, 2)


def _serialize_job(job):
    return {
        'id': job.id,
        'customer_name': job.customer_name,
        'customer_phone': job.customer_phone,
        'pickup': job.pickup,
        'dropoff': job.dropoff,
        'area': job.area,
        'job_type': job.job_type,
        'source': job.source,
        'status': job.status,
        'driver_name': job.driver_name,
        'vehicle_id': job.vehicle_id,
        'distance_miles': job.distance_miles,
        'duration_minutes': job.duration_minutes,
        'meter_amount': job.meter_amount,
        'notes': job.notes,
        'created_at': job.created_at.isoformat() if job.created_at else None,
        'updated_at': job.updated_at.isoformat() if job.updated_at else None,
        'job_app_source': job.job_app_source,
        'job_app_id': job.job_app_id,
        'job_app_url': job.job_app_url,
        'job_app_status': job.job_app_status,
        'earnings': job.earnings,
        'rating': job.rating,
        'tips': job.tips,
    }


def _area_coordinates(area_name):
    area_seed = {
        'rocky mount': (35.9382, -77.7905),
        'nash county': (35.9800, -77.9600),
        'wilson': (35.7213, -77.9155),
        'greenville': (35.6127, -77.3664),
    }
    normalized = (area_name or '').strip().lower()
    if normalized in area_seed:
        return area_seed[normalized]

    # Deterministic fallback near regional center for unknown areas.
    offset = (sum(ord(ch) for ch in normalized) % 30) / 1000.0
    return (35.93 + offset, -77.79 + offset)


def _build_locator_points():
    dispatch = _dispatch_config()
    jobs = FleetJob.query.order_by(FleetJob.created_at.desc()).limit(250).all()

    area_counts = {}
    for job in jobs:
        area_key = (job.area or 'unknown').strip() or 'unknown'
        area_counts[area_key] = area_counts.get(area_key, 0) + 1

    points = []
    service_areas = dispatch.get('serviceAreas', []) or []
    channels = dispatch.get('partnerChannels', []) or ['local_transport']
    for idx, area in enumerate(service_areas):
        lat, lng = _area_coordinates(area)
        demand_score = max(1, min(10, area_counts.get(area, 0) + 2))
        eta_minutes = max(4, 16 - demand_score)
        sample_distance = max(1.0, 2.0 + idx * 1.8)
        sample_duration = max(8.0, 12.0 + idx * 3.0)

        points.append({
            'area': area,
            'lat': round(lat, 6),
            'lng': round(lng, 6),
            'demand_score': demand_score,
            'eta_minutes': eta_minutes,
            'suggested_fare': _calc_meter(sample_distance, sample_duration),
            'source_channel': channels[idx % len(channels)]
        })

    # Include top open jobs as immediate rider opportunities.
    for job in jobs[:8]:
        if (job.status or '').lower() in {'completed', 'cancelled'}:
            continue
        area = job.area or 'unknown'
        lat, lng = _area_coordinates(area)
        points.append({
            'area': area,
            'lat': round(lat + 0.002, 6),
            'lng': round(lng - 0.002, 6),
            'demand_score': max(2, min(10, int(job.distance_miles or 0) + 3)),
            'eta_minutes': max(3, 15 - int(job.duration_minutes or 0) // 10),
            'suggested_fare': round(float(job.meter_amount or 0.0), 2),
            'source_channel': (job.source or 'local_transport').lower().replace(' ', '_')
        })

    return points


@dispatch_bp.get('/config')
def public_dispatch_config():
    dispatch = _dispatch_config()
    return jsonify({
        'enabled': bool(dispatch.get('enabled', True)),
        'acceptLocalCalls': bool(dispatch.get('acceptLocalCalls', True)),
        'serviceAreas': dispatch.get('serviceAreas', []),
        'partnerChannels': dispatch.get('partnerChannels', []),
        'dispatchPhone': dispatch.get('dispatchPhone') or business_settings.get('phone', '252 886-5996'),
    })


@dispatch_bp.get('/locator')
@jwt_required()
def ai_locator():
    denied = _require_admin()
    if denied:
        return denied

    points = _build_locator_points()
    return jsonify({
        'generated_at': datetime.utcnow().isoformat(),
        'locator_points': points,
        'total_points': len(points),
        'map_center': {'lat': 35.9382, 'lng': -77.7905},
        'strategy': 'AI demand clustering across service areas and live dispatch queue'
    })


@dispatch_bp.get('/promotions')
@jwt_required()
def list_promotions():
    denied = _require_admin()
    if denied:
        return denied

    dispatch = _dispatch_config()
    return jsonify({
        'promotion_message': dispatch.get('promotionMessage', ''),
        'campaigns': dispatch.get('promotionCampaigns', [])
    })


@dispatch_bp.post('/promotions')
@jwt_required()
def create_promotion_campaign():
    denied = _require_admin()
    if denied:
        return denied

    dispatch = _dispatch_config()
    data = request.get_json() or {}

    channels = data.get('channels') or []
    if not isinstance(channels, list):
        channels = []

    normalized_channels = [str(ch).strip().lower() for ch in channels if str(ch).strip()]
    if not normalized_channels:
        normalized_channels = dispatch.get('partnerChannels', [])

    message = str(data.get('message') or dispatch.get('promotionMessage') or '').strip()
    if not message:
        return jsonify({'error': 'promotion message is required'}), 400

    campaign = {
        'id': f"promo-{int(datetime.utcnow().timestamp())}",
        'created_at': datetime.utcnow().isoformat(),
        'channels': normalized_channels,
        'message': message,
        'target_area': str(data.get('target_area') or 'regional').strip(),
        'status': 'queued',
        'budget': _to_float(data.get('budget'), 0.0)
    }

    campaigns = dispatch.setdefault('promotionCampaigns', [])
    campaigns.insert(0, campaign)
    dispatch['promotionCampaigns'] = campaigns[:25]
    dispatch['promotionMessage'] = message

    return jsonify({'message': 'Dispatcher promotion campaign queued', 'campaign': campaign}), 201


@dispatch_bp.post('/meter/estimate')
def estimate_meter():
    data = request.get_json() or {}
    distance = _to_float(data.get('distance_miles'), 0.0)
    duration = _to_float(data.get('duration_minutes'), 0.0)
    surge = data.get('surge_multiplier')

    return jsonify({
        'estimated_fare': _calc_meter(distance, duration, surge),
        'distance_miles': distance,
        'duration_minutes': duration,
    })


@dispatch_bp.post('/calls')
def create_local_call_job():
    dispatch = _dispatch_config()
    if not bool(dispatch.get('enabled', True)):
        return jsonify({'error': 'Dispatch is currently disabled'}), 403
    if not bool(dispatch.get('acceptLocalCalls', True)):
        return jsonify({'error': 'Local calls are currently disabled'}), 403

    data = request.get_json() or {}
    customer_phone = str(data.get('customer_phone') or '').strip()
    pickup = str(data.get('pickup') or '').strip()
    area = str(data.get('area') or '').strip()

    if not customer_phone:
        return jsonify({'error': 'customer_phone is required'}), 400
    if not pickup:
        return jsonify({'error': 'pickup is required'}), 400
    if not area:
        return jsonify({'error': 'area is required'}), 400

    distance = _to_float(data.get('distance_miles'), 0.0)
    duration = _to_float(data.get('duration_minutes'), 0.0)

    job = FleetJob(
        customer_name=str(data.get('customer_name') or 'Local Caller').strip(),
        customer_phone=customer_phone,
        pickup=pickup,
        dropoff=str(data.get('dropoff') or '').strip(),
        area=area,
        job_type=str(data.get('job_type') or 'local_call').strip(),
        source='local_call',
        status='new',
        notes=str(data.get('notes') or '').strip() or None,
        distance_miles=distance,
        duration_minutes=duration,
        meter_amount=_calc_meter(distance, duration),
    )
    db.session.add(job)
    db.session.commit()

    return jsonify({
        'message': 'Local dispatch request received',
        'job': _serialize_job(job)
    }), 201


@dispatch_bp.get('/jobs')
@jwt_required()
def list_jobs():
    denied = _require_admin()
    if denied:
        return denied

    status = (request.args.get('status') or '').strip().lower()
    query = FleetJob.query
    if status:
        query = query.filter_by(status=status)

    jobs = query.order_by(FleetJob.created_at.desc()).all()
    return jsonify([_serialize_job(job) for job in jobs])


@dispatch_bp.post('/jobs')
@jwt_required()
def create_job():
    denied = _require_admin()
    if denied:
        return denied

    data = request.get_json() or {}
    distance = _to_float(data.get('distance_miles'), 0.0)
    duration = _to_float(data.get('duration_minutes'), 0.0)

    job = FleetJob(
        customer_name=str(data.get('customer_name') or 'Fleet Client').strip(),
        customer_phone=str(data.get('customer_phone') or '').strip(),
        pickup=str(data.get('pickup') or '').strip(),
        dropoff=str(data.get('dropoff') or '').strip(),
        area=str(data.get('area') or '').strip(),
        job_type=str(data.get('job_type') or 'amazon_flex').strip(),
        source=str(data.get('source') or 'admin').strip(),
        status=str(data.get('status') or 'new').strip(),
        driver_name=str(data.get('driver_name') or '').strip() or None,
        vehicle_id=str(data.get('vehicle_id') or '').strip() or None,
        notes=str(data.get('notes') or '').strip() or None,
        distance_miles=distance,
        duration_minutes=duration,
        meter_amount=_calc_meter(distance, duration, data.get('surge_multiplier')),
    )

    db.session.add(job)
    db.session.commit()
    return jsonify({'message': 'Fleet job created', 'job': _serialize_job(job)}), 201


@dispatch_bp.put('/jobs/<int:job_id>')
@jwt_required()
def update_job(job_id):
    denied = _require_admin()
    if denied:
        return denied

    job = FleetJob.query.get_or_404(job_id)
    data = request.get_json() or {}

    for field in ['customer_name', 'customer_phone', 'pickup', 'dropoff', 'area', 'job_type', 'source', 'status', 'driver_name', 'vehicle_id', 'notes']:
        if field in data:
            value = data.get(field)
            setattr(job, field, str(value).strip() if value is not None else None)

    if 'distance_miles' in data:
        job.distance_miles = _to_float(data.get('distance_miles'), job.distance_miles)
    if 'duration_minutes' in data:
        job.duration_minutes = _to_float(data.get('duration_minutes'), job.duration_minutes)

    recalc_meter = bool(data.get('recalculate_meter', True))
    if recalc_meter:
        job.meter_amount = _calc_meter(job.distance_miles, job.duration_minutes, data.get('surge_multiplier'))

    db.session.commit()
    return jsonify({'message': 'Fleet job updated', 'job': _serialize_job(job)})


@dispatch_bp.delete('/jobs/<int:job_id>')
@jwt_required()
def delete_job(job_id):
    denied = _require_admin()
    if denied:
        return denied

    job = FleetJob.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    return jsonify({'message': 'Fleet job deleted'})


@dispatch_bp.get('/job-apps')
@jwt_required()
def get_job_apps():
    denied = _require_admin()
    if denied:
        return denied

    job_apps = [
        {
            'id': 'amazon_flex',
            'name': 'Amazon Flex',
            'icon': '📦',
            'color': '#FF9900',
            'url': 'https://flex.amazon.com',
            'type': 'delivery',
            'features': ['delivery_tracking', 'route_optimization', 'earnings_display']
        },
        {
            'id': 'doordash',
            'name': 'DoorDash',
            'icon': '🍔',
            'color': '#FF3008',
            'url': 'https://doordash.com/dasher',
            'type': 'delivery',
            'features': ['delivery_tracking', 'route_optimization', 'earnings_display']
        },
        {
            'id': 'uber',
            'name': 'Uber',
            'icon': '🚗',
            'color': '#000000',
            'url': 'https://uber.com/drive',
            'type': 'rideshare',
            'features': ['ride_tracking', 'route_optimization', 'earnings_display']
        },
        {
            'id': 'lyft',
            'name': 'Lyft',
            'icon': '🚙',
            'color': '#FF00BF',
            'url': 'https://lyft.com/drive',
            'type': 'rideshare',
            'features': ['ride_tracking', 'route_optimization', 'earnings_display']
        },
        {
            'id': 'grubhub',
            'name': 'Grubhub',
            'icon': '🥡',
            'color': '#F63440',
            'url': 'https://grubhub.com/driver',
            'type': 'delivery',
            'features': ['delivery_tracking', 'route_optimization', 'earnings_display']
        },
        {
            'id': 'instacart',
            'name': 'Instacart',
            'icon': '🛒',
            'color': '#43B02A',
            'url': 'https://instacart.com/shopper',
            'type': 'shopping',
            'features': ['shopping_tracking', 'route_optimization', 'earnings_display']
        },
        {
            'id': 'traveling_star',
            'name': 'Traveling Star',
            'icon': '⭐',
            'color': '#C61E1E',
            'url': 'https://travelingstarservice.github.io',
            'type': 'local',
            'features': ['dispatch_tracking', 'route_optimization', 'earnings_display']
        }
    ]
    
    return jsonify({
        'job_apps': job_apps,
        'total_apps': len(job_apps)
    })


@dispatch_bp.get('/job-apps/dashboard')
@jwt_required()
def get_job_app_dashboard():
    denied = _require_admin()
    if denied:
        return denied

    dispatch = _dispatch_config()
    enabled_apps = dispatch.get('enabledJobApps', ['amazon_flex', 'doordash', 'uber', 'traveling_star'])
    
    # Get recent jobs from all apps
    recent_jobs = FleetJob.query.filter(
        FleetJob.job_app_source.in_(enabled_apps)
    ).order_by(FleetJob.created_at.desc()).limit(20).all()
    
    # Calculate earnings by app
    earnings_by_app = {}
    for job in recent_jobs:
        app = job.job_app_source or 'unknown'
        if app not in earnings_by_app:
            earnings_by_app[app] = {
                'total_earnings': 0.0,
                'total_tips': 0.0,
                'job_count': 0,
                'average_rating': 0.0,
                'ratings': []
            }
        
        earnings_by_app[app]['total_earnings'] += job.earnings or 0.0
        earnings_by_app[app]['total_tips'] += job.tips or 0.0
        earnings_by_app[app]['job_count'] += 1
        if job.rating:
            earnings_by_app[app]['ratings'].append(job.rating)
    
    # Calculate averages
    for app in earnings_by_app:
        ratings = earnings_by_app[app]['ratings']
        earnings_by_app[app]['average_rating'] = sum(ratings) / len(ratings) if ratings else 0.0
        del earnings_by_app[app]['ratings']
    
    return jsonify({
        'enabled_apps': enabled_apps,
        'recent_jobs': [_serialize_job(job) for job in recent_jobs],
        'earnings_by_app': earnings_by_app,
        'dashboard_config': {
            'screen_display_enabled': dispatch.get('screenDisplayEnabled', True),
            'auto_refresh_seconds': dispatch.get('autoRefreshSeconds', 30),
            'show_earnings': dispatch.get('showEarnings', True),
            'show_ratings': dispatch.get('showRatings', True)
        }
    })


@dispatch_bp.post('/job-apps/config')
@jwt_required()
def update_job_app_config():
    denied = _require_admin()
    if denied:
        return denied

    dispatch = _dispatch_config()
    data = request.get_json() or {}
    
    # Update job app configuration
    if 'enabled_apps' in data:
        dispatch['enabledJobApps'] = data['enabled_apps']
    
    if 'screen_display_enabled' in data:
        dispatch['screenDisplayEnabled'] = data['screen_display_enabled']
    
    if 'auto_refresh_seconds' in data:
        dispatch['autoRefreshSeconds'] = data['auto_refresh_seconds']
    
    if 'show_earnings' in data:
        dispatch['showEarnings'] = data['show_earnings']
    
    if 'show_ratings' in data:
        dispatch['showRatings'] = data['show_ratings']
    
    # Save configuration
    business_settings['dispatch'] = dispatch
    
    return jsonify({
        'message': 'Job app configuration updated',
        'config': {
            'enabled_apps': dispatch.get('enabledJobApps', []),
            'screen_display_enabled': dispatch.get('screenDisplayEnabled', True),
            'auto_refresh_seconds': dispatch.get('autoRefreshSeconds', 30),
            'show_earnings': dispatch.get('showEarnings', True),
            'show_ratings': dispatch.get('showRatings', True)
        }
    })


@dispatch_bp.get('/jobs/by-app/<app_id>')
@jwt_required()
def get_jobs_by_app(app_id):
    denied = _require_admin()
    if denied:
        return denied

    jobs = FleetJob.query.filter(
        FleetJob.job_app_source == app_id
    ).order_by(FleetJob.created_at.desc()).limit(50).all()
    
    return jsonify({
        'app_id': app_id,
        'jobs': [_serialize_job(job) for job in jobs],
        'total_jobs': len(jobs)
    })
