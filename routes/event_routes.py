from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.event import Event
from models.booking import Booking
from models.user import User
from extensions import db
from utils.validators import validate_string_length, sanitize_string

event_bp = Blueprint('event_bp', __name__)


def _require_admin():
    try:
        identity = get_jwt_identity()
        if not identity:
            return jsonify({'error': 'Authentication required'}), 401
        user = User.query.get(identity)
        if not user or (user.role or '').lower() != 'admin':
            return jsonify({'error': 'admin access required'}), 403
        return None
    except Exception as e:
        return jsonify({'error': 'Authentication failed', 'details': str(e)}), 401

@event_bp.get('/')
def list_events():
    try:
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
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve events', 'details': str(e)}), 500

@event_bp.post('/')
@jwt_required()
def create_event():
    try:
        denied = _require_admin()
        if denied:
            return denied

        data = request.get_json() or {}
        
        # Validate title
        title = sanitize_string(data.get('title', ''), 200)
        if not title:
            return jsonify({'error': 'title is required'}), 400
        
        valid_title, title = validate_string_length(title, 1, 200, 'title')
        if not valid_title:
            return jsonify({'error': title}), 400

        # Validate and sanitize description
        description = sanitize_string(data.get('description', ''), 2000)
        valid_desc, description = validate_string_length(description, 0, 2000, 'description')
        if not valid_desc:
            return jsonify({'error': description}), 400

        # Validate and sanitize image URL
        image = sanitize_string(data.get('image', ''), 500) if data.get('image') else None
        if image:
            valid_image, image = validate_string_length(image, 0, 500, 'image')
            if not valid_image:
                return jsonify({'error': image}), 400
        
        event = Event(
            title=title,
            description=description,
            image=image
        )
        db.session.add(event)
        db.session.commit()
        return jsonify({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'image': event.image,
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create event', 'details': str(e)}), 500

@event_bp.get('/<int:event_id>')
def get_event(event_id):
    try:
        event = Event.query.get(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        return jsonify({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'image': event.image,
        })
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve event', 'details': str(e)}), 500

@event_bp.put('/<int:event_id>')
@jwt_required()
def update_event(event_id):
    try:
        denied = _require_admin()
        if denied:
            return denied

        event = Event.query.get(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        data = request.get_json() or {}
        
        # Validate and update title if provided
        if 'title' in data:
            title = sanitize_string(data.get('title', ''), 200)
            valid_title, title = validate_string_length(title, 1, 200, 'title')
            if not valid_title:
                return jsonify({'error': title}), 400
            event.title = title

        # Validate and update description if provided
        if 'description' in data:
            description = sanitize_string(data.get('description', ''), 2000)
            valid_desc, description = validate_string_length(description, 0, 2000, 'description')
            if not valid_desc:
                return jsonify({'error': description}), 400
            event.description = description

        # Validate and update image if provided
        if 'image' in data:
            image = sanitize_string(data.get('image', ''), 500) if data.get('image') else None
            if image:
                valid_image, image = validate_string_length(image, 0, 500, 'image')
                if not valid_image:
                    return jsonify({'error': image}), 400
            event.image = image

        db.session.commit()
        return jsonify({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'image': event.image,
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update event', 'details': str(e)}), 500

@event_bp.delete('/<int:event_id>')
@jwt_required()
def delete_event(event_id):
    try:
        denied = _require_admin()
        if denied:
            return denied

        event = Event.query.get(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        db.session.delete(event)
        db.session.commit()
        return jsonify({'message': 'Event deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete event', 'details': str(e)}), 500

@event_bp.get('/analytics')
@jwt_required()
def event_analytics():
    try:
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
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve analytics', 'details': str(e)}), 500
