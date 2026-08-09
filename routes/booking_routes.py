from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.booking import Booking
from models.user import User
from extensions import db
from utils.validators import validate_positive_number, validate_date_string, sanitize_string, validate_string_length

booking_bp = Blueprint('booking_bp', __name__)

def _require_admin():
    """Check if current user is admin."""
    try:
        claims = get_jwt()
        if (claims.get('role') or '').lower() != 'admin':
            return False
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        return user and (user.role or '').lower() == 'admin'
    except:
        return False

@booking_bp.post('')
@booking_bp.post('/')
def create_booking():
    try:
        data = request.get_json() or {}
        
        # Validate event_id
        event_id = data.get('event_id')
        if event_id is None:
            return jsonify({'error': 'event_id is required'}), 400
        
        # Validate event_id is positive integer
        valid_event_id, event_id = validate_positive_number(event_id, 'event_id')
        if not valid_event_id:
            return jsonify({'error': event_id}), 400

        user_id = data.get('user_id') or 0
        if user_id:
            valid_user_id, user_id = validate_positive_number(user_id, 'user_id')
            if not valid_user_id:
                return jsonify({'error': user_id}), 400

        # Validate date
        booking_date = data.get('date', '2026-08-01')
        valid_date, booking_date = validate_date_string(booking_date, 'date')
        if not valid_date:
            return jsonify({'error': booking_date}), 400

        # Validate optional location fields
        pickup_location = None
        if data.get('pickup_location'):
            pickup_valid, pickup_location = validate_string_length(
                sanitize_string(data.get('pickup_location', ''), 255), 
                0, 255, 'pickup_location'
            )
            if not pickup_valid:
                return jsonify({'error': pickup_location}), 400

        dropoff_location = None
        if data.get('dropoff_location'):
            dropoff_valid, dropoff_location = validate_string_length(
                sanitize_string(data.get('dropoff_location', ''), 255), 
                0, 255, 'dropoff_location'
            )
            if not dropoff_valid:
                return jsonify({'error': dropoff_location}), 400

        booking = Booking(
            user_id=int(user_id), 
            event_id=int(event_id), 
            date=booking_date,
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            status='pending'
        )
        db.session.add(booking)
        db.session.commit()

        return jsonify({
            'id': booking.id,
            'event_id': booking.event_id,
            'date': booking.date,
            'status': booking.status,
            'pickup_location': booking.pickup_location,
            'dropoff_location': booking.dropoff_location,
            'message': 'Booking received. Call or text 252 886-5996 for immediate assistance.'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create booking', 'details': str(e)}), 500

@booking_bp.get('')
@booking_bp.get('/')
@jwt_required()
def list_bookings():
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'Invalid user identity'}), 401
        
        bookings = Booking.query.filter_by(user_id=user_id).all()
        return jsonify([
            {
                'id': b.id, 
                'event_id': b.event_id, 
                'date': b.date,
                'status': b.status,
                'pickup_location': b.pickup_location,
                'dropoff_location': b.dropoff_location,
                'created_at': b.created_at.isoformat() if b.created_at else None,
                'updated_at': b.updated_at.isoformat() if b.updated_at else None
            }
            for b in bookings
        ])
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve bookings', 'details': str(e)}), 500

@booking_bp.get('/<int:booking_id>')
@jwt_required()
def get_booking(booking_id):
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'Invalid user identity'}), 401
        
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Only allow users to see their own bookings, admins can see all
        if not _require_admin() and booking.user_id != int(user_id):
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({
            'id': booking.id,
            'event_id': booking.event_id,
            'date': booking.date,
            'status': booking.status,
            'notes': booking.notes,
            'pickup_location': booking.pickup_location,
            'dropoff_location': booking.dropoff_location,
            'created_at': booking.created_at.isoformat() if booking.created_at else None,
            'updated_at': booking.updated_at.isoformat() if booking.updated_at else None
        })
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve booking', 'details': str(e)}), 500

@booking_bp.put('/<int:booking_id>/status')
@jwt_required()
def update_booking_status(booking_id):
    try:
        if not _require_admin():
            return jsonify({'error': 'Admin access required'}), 403
        
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        data = request.get_json() or {}
        new_status = data.get('status')
        
        valid_statuses = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        booking.status = new_status
        if data.get('notes'):
            notes_valid, notes = validate_string_length(
                sanitize_string(data.get('notes', ''), 2000), 
                0, 2000, 'notes'
            )
            if not notes_valid:
                return jsonify({'error': notes}), 400
            booking.notes = notes
        
        db.session.commit()
        
        return jsonify({
            'id': booking.id,
            'status': booking.status,
            'notes': booking.notes,
            'updated_at': booking.updated_at.isoformat() if booking.updated_at else None,
            'message': 'Booking status updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update booking status', 'details': str(e)}), 500

@booking_bp.get('/admin/all')
@jwt_required()
def list_all_bookings():
    try:
        if not _require_admin():
            return jsonify({'error': 'Admin access required'}), 403
        
        status_filter = request.args.get('status')
        query = Booking.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        bookings = query.order_by(Booking.created_at.desc()).all()
        return jsonify([
            {
                'id': b.id,
                'user_id': b.user_id,
                'event_id': b.event_id,
                'date': b.date,
                'status': b.status,
                'notes': b.notes,
                'pickup_location': b.pickup_location,
                'dropoff_location': b.dropoff_location,
                'created_at': b.created_at.isoformat() if b.created_at else None,
                'updated_at': b.updated_at.isoformat() if b.updated_at else None
            }
            for b in bookings
        ])
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve bookings', 'details': str(e)}), 500
