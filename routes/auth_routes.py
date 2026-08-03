import re
import uuid
import os

from flask import Blueprint, request
from flask_jwt_extended import create_access_token, get_jwt, jwt_required
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


def _get_admin_user():
    admin = User.query.filter_by(role='admin').first()
    if admin:
        return admin
    return User.query.filter_by(email='admin@travelingstar.com').first()


def _require_admin_claims():
    claims = get_jwt()
    if (claims.get('role') or '').lower() != 'admin':
        return {'error': 'admin access required'}, 403
    return None


@auth_bp.post('/register')
def register():
    data = request.get_json() or {}
    password = _normalize_password(data.get('password'))

    if not password or not re.fullmatch(r'\d{4}', password):
        return {'error': 'please provide a 4-digit password'}, 400

    admin = _get_admin_user()
    if (admin and password == admin.password) or password == _admin_pin():
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

    admin = _get_admin_user()
    if admin and admin.password == password:
        user = admin
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


@auth_bp.post('/admin-password')
@jwt_required()
def change_admin_password():
    denied = _require_admin_claims()
    if denied:
        return denied

    data = request.get_json() or {}
    current_password = _normalize_password(data.get('current_password'))
    new_password = _normalize_password(data.get('new_password'))

    if not new_password or not re.fullmatch(r'\d{4}', new_password):
        return {'error': 'please provide a 4-digit password'}, 400

    admin = _get_admin_user()
    if not admin:
        return {'error': 'admin account not found'}, 404

    if current_password and admin.password != current_password:
        return {'error': 'current password is incorrect'}, 400

    if new_password == admin.password:
        return {'error': 'new password must be different'}, 400

    admin.password = new_password
    admin.role = 'admin'
    db.session.commit()
    return {'message': 'admin password updated'}


@auth_bp.get('/owner/users')
@jwt_required()
def list_owner_users():
    denied = _require_admin_claims()
    if denied:
        return denied

    users = User.query.order_by(User.id.asc()).all()
    return {
        'users': [
            {
                'id': user.id,
                'email': user.email,
                'role': user.role,
            }
            for user in users
        ]
    }


@auth_bp.post('/owner/users')
@jwt_required()
def create_owner_user():
    denied = _require_admin_claims()
    if denied:
        return denied

    data = request.get_json() or {}
    email = str(data.get('email') or '').strip().lower()
    password = _normalize_password(data.get('password'))
    role = str(data.get('role') or 'user').strip().lower() or 'user'

    if not email:
        return {'error': 'email is required'}, 400
    if role not in {'user', 'admin'}:
        return {'error': 'role must be user or admin'}, 400
    if not password or not re.fullmatch(r'\d{4}', password):
        return {'error': 'please provide a 4-digit password'}, 400

    existing = User.query.filter_by(email=email).first()
    if existing:
        return {'error': 'email already exists'}, 400

    user = User(email=email, password=password, role=role)
    db.session.add(user)
    db.session.commit()
    return {
        'message': 'owner user created',
        'user': {'id': user.id, 'email': user.email, 'role': user.role}
    }, 201


@auth_bp.put('/owner/users/<int:user_id>/password')
@jwt_required()
def update_owner_user_password(user_id):
    denied = _require_admin_claims()
    if denied:
        return denied

    data = request.get_json() or {}
    new_password = _normalize_password(data.get('new_password'))
    if not new_password or not re.fullmatch(r'\d{4}', new_password):
        return {'error': 'please provide a 4-digit password'}, 400

    user = User.query.get_or_404(user_id)
    user.password = new_password
    db.session.commit()
    return {'message': 'user password updated'}


@auth_bp.delete('/owner/users/<int:user_id>')
@jwt_required()
def delete_owner_user(user_id):
    denied = _require_admin_claims()
    if denied:
        return denied

    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        return {'error': 'cannot delete admin account'}, 400

    db.session.delete(user)
    db.session.commit()
    return {'message': 'user deleted'}
