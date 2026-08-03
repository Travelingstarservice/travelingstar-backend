from datetime import datetime

from extensions import db


class FleetJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False, default='Walk-in Customer')
    customer_phone = db.Column(db.String(50), nullable=False, default='')
    pickup = db.Column(db.String(255), nullable=False, default='')
    dropoff = db.Column(db.String(255), nullable=False, default='')
    area = db.Column(db.String(120), nullable=False, default='')
    job_type = db.Column(db.String(80), nullable=False, default='local_ride')
    source = db.Column(db.String(80), nullable=False, default='admin')
    status = db.Column(db.String(40), nullable=False, default='new')
    driver_name = db.Column(db.String(120), nullable=True)
    vehicle_id = db.Column(db.String(80), nullable=True)
    distance_miles = db.Column(db.Float, nullable=False, default=0.0)
    duration_minutes = db.Column(db.Float, nullable=False, default=0.0)
    meter_amount = db.Column(db.Float, nullable=False, default=0.0)
    notes = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
