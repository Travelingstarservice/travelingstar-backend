from extensions import db
from datetime import datetime

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    event_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(50), nullable=False, default='2026-08-01')
    status = db.Column(db.String(20), nullable=False, default='pending')
    notes = db.Column(db.Text, nullable=True)
    pickup_location = db.Column(db.String(255), nullable=True)
    dropoff_location = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
