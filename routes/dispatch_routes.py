from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required

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
        'dispatchPhone': business_settings.get('phone', '252 886-5996'),
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
    }


@dispatch_bp.get('/config')
def public_dispatch_config():
    dispatch = _dispatch_config()
    return jsonify({
        'enabled': bool(dispatch.get('enabled', True)),
        'acceptLocalCalls': bool(dispatch.get('acceptLocalCalls', True)),
        'serviceAreas': dispatch.get('serviceAreas', []),
        'dispatchPhone': dispatch.get('dispatchPhone') or business_settings.get('phone', '252 886-5996'),
    })


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
