import re
import uuid
import os

from flask import Blueprint, request
from flask_jwt_extended import create_access_token
from models.user import User
from extensions import db

auth_bp = Blueprint('auth_bp', __name__)


def _normalize_password(password):
    return str(password or '').strip()


def _build_email(password):
    base = re.sub(r'[^a-z0-9]+', '', password.lower())[:24] or 'user'
    return f'{base}-{uuid.uuid4().hex[:6]}@travelingstar.local'


def _admin_pin():
    configured = _normalize_password(os.getenv('ADMIN_PIN', '1234'))
    return configured if re.fullmatch(r'\d{4}', configured) else '1234'


@auth_bp.post('/register')
def register():
    data = request.get_json() or {}
    password = _normalize_password(data.get('password'))

    if not password or not re.fullmatch(r'\d{4}', password):
        return {'error': 'please provide a 4-digit password'}, 400

    if password == _admin_pin():
        return {'error': 'that pin is reserved'}, 400

    email = data.get('email') or _build_email(password)
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, password=password, role='user')
        db.session.add(user)
        db.session.commit()

    return {'message': 'registered'}


@auth_bp.post('/login')
def login():
    data = request.get_json() or {}
    password = _normalize_password(data.get('password'))

    if not password or not re.fullmatch(r'\d{4}', password):
        return {'error': 'please provide a 4-digit password'}, 400

    # Reserve one PIN for administrator access.
    if password == _admin_pin():
        user = User.query.filter_by(email='admin@travelingstar.com').first()
    else:
        user = User.query.filter_by(password=password, role='user').first()
        if not user:
            email = data.get('email')
            if email:
                user = User.query.filter_by(email=email, role='user').first()

    if not user or user.password != password:
        return {'error': 'invalid credentials'}, 401

    token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role or 'user'}
    )
    role = user.role or ('admin' if user.email.lower() == 'admin@travelingstar.com' else 'user')

    return {
        'token': token,
        'role': role,
        'email': user.email
    }


@auth_bp.post('/change-password')
def change_password():
    data = request.get_json() or {}
    current_password = _normalize_password(data.get('current_password'))
    new_password = _normalize_password(data.get('new_password'))

    if not new_password or not re.fullmatch(r'\d{4}', new_password):
        return {'error': 'please provide a 4-digit password'}, 400

    if new_password == _admin_pin():
        return {'error': 'that pin is reserved'}, 400

    user = None
    if current_password:
        user = User.query.filter_by(password=current_password).first()

    if not user:
        user = User.query.filter_by(password=new_password).first()

    if not user:
        email = _build_email(new_password)
        user = User(email=email, password=new_password, role='user')
        db.session.add(user)
        db.session.commit()
        return {'message': 'password created'}

    user.password = new_password
    db.session.commit()
    return {'message': 'password updated'}
