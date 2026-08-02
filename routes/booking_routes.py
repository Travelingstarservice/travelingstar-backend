from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.booking import Booking
from extensions import db

booking_bp = Blueprint('booking_bp', __name__)

@booking_bp.post('')
@booking_bp.post('/')
def create_booking():
    data = request.get_json() or {}
    event_id = data.get('event_id')
    if event_id is None:
        return {'error': 'event_id is required'}, 400

    user_id = data.get('user_id') or 0
    booking_date = data.get('date', '2026-08-01')
    booking = Booking(user_id=user_id, event_id=event_id, date=booking_date)
    db.session.add(booking)
    db.session.commit()

    return {
        'id': booking.id,
        'event_id': booking.event_id,
        'date': booking.date,
        'status': 'accepted',
        'message': 'Booking received. Call or text 252 886-5996 for immediate assistance.'
    }

@booking_bp.get('')
@booking_bp.get('/')
@jwt_required()
def list_bookings():
    user_id = get_jwt_identity()
    bookings = Booking.query.filter_by(user_id=user_id).all()
    return [
        {'id': b.id, 'event_id': b.event_id, 'date': b.date}
        for b in bookings
    ]
