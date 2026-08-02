import re
import uuid

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


@auth_bp.post('/register')
def register():
    data = request.get_json() or {}
    password = _normalize_password(data.get('password'))

    if not password or not re.fullmatch(r'\d{4}', password):
        return {'error': 'please provide a 4-digit password'}, 400

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

    user = User.query.filter_by(password=password).first()
    if not user:
        email = data.get('email')
        if email:
            user = User.query.filter_by(email=email).first()

    if not user or user.password != password:
        return {'error': 'invalid credentials'}, 401

    token = create_access_token(identity=str(user.id))
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
