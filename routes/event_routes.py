from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.event import Event
from models.booking import Booking
from models.user import User
from extensions import db

event_bp = Blueprint('event_bp', __name__)


def _require_admin():
    identity = get_jwt_identity()
    user = User.query.get(identity)
    if not user or (user.role or '').lower() != 'admin':
        return jsonify({'error': 'admin access required'}), 403
    return None

@event_bp.get('/')
def list_events():
    events = Event.query.all()
    return jsonify([
        {
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'image': event.image,
        }
        for event in events
    ])

@event_bp.post('/')
@jwt_required()
def create_event():
    denied = _require_admin()
    if denied:
        return denied

    data = request.get_json() or {}
    event = Event(
        title=data.get('title', ''),
        description=data.get('description', ''),
        image=data.get('image')
    )
    db.session.add(event)
    db.session.commit()
    return jsonify({
        'id': event.id,
        'title': event.title,
        'description': event.description,
        'image': event.image,
    }), 201

@event_bp.get('/<int:event_id>')
def get_event(event_id):
    event = Event.query.get_or_404(event_id)
    return jsonify({
        'id': event.id,
        'title': event.title,
        'description': event.description,
        'image': event.image,
    })

@event_bp.put('/<int:event_id>')
@jwt_required()
def update_event(event_id):
    denied = _require_admin()
    if denied:
        return denied

    event = Event.query.get_or_404(event_id)
    data = request.get_json() or {}
    event.title = data.get('title', event.title)
    event.description = data.get('description', event.description)
    if 'image' in data:
        event.image = data.get('image')
    db.session.commit()
    return jsonify({
        'id': event.id,
        'title': event.title,
        'description': event.description,
        'image': event.image,
    })

@event_bp.delete('/<int:event_id>')
@jwt_required()
def delete_event(event_id):
    denied = _require_admin()
    if denied:
        return denied

    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return jsonify({'message': 'Event deleted'})

@event_bp.get('/analytics')
@jwt_required()
def event_analytics():
    denied = _require_admin()
    if denied:
        return denied

    bookings_count = Booking.query.count()
    events_count = Event.query.count()
    revenue = bookings_count * 50
    return jsonify({
        'bookings_count': bookings_count,
        'events_count': events_count,
        'revenue': revenue,
    })
