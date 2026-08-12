"""
Authentication routes for user registration, login, and password management.

This module provides endpoints for:
- User registration with 4-digit PINs
- Login with PIN or email/password
- Password changes
- Admin password management with strong password support
- Admin access control (lock/unlock)
- Admin recovery mechanism
"""

import re
import uuid
import os
import hmac

from flask import Blueprint, request
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
from models.user import User
from extensions import db
from utils.validators import validate_4digit_password, validate_email, sanitize_string, validate_password_strength
from utils.rate_limiter import auth_rate_limit

auth_bp = Blueprint('auth_bp', __name__)


def _normalize_password(password):
    return str(password or '').strip()


def _build_email(password):
    base = re.sub(r'[^a-z0-9]+', '', password.lower())[:24] or 'user'
    return f'{base}-{uuid.uuid4().hex[:6]}@travelingstar.local'


def _admin_pin():
    configured = _normalize_password(os.getenv('ADMIN_PIN', '1234'))
    return configured if re.fullmatch(r'\d{4}', configured) else '1234'


def _owner_recovery_secret():
    return str(os.getenv('OWNER_RECOVERY_SECRET') or '').strip()


def _get_admin_user():
    admin = User.query.filter_by(role='admin').first()
    if admin:
        return admin
    return User.query.filter_by(email='admin@travelingstar.com').first()


def _get_current_user():
    user_id = get_jwt_identity()
    if not user_id:
        return None
    try:
        return User.query.get(int(user_id))
    except (TypeError, ValueError):
        return None


def _require_admin_user():
    claims = get_jwt()
    if (claims.get('role') or '').lower() != 'admin':
        return None, ({'error': 'admin access required'}, 403)

    user = _get_current_user()
    if not user:
        return None, ({'error': 'user not found'}, 401)
    if (user.role or '').lower() != 'admin':
        return None, ({'error': 'admin access required'}, 403)
    return user, None


@auth_bp.post('/register')
def register():
    try:
        data = request.get_json() or {}

        # Validate password
        password_valid, password = validate_4digit_password(data.get('password'))
        if not password_valid:
            return {'error': password}, 400

        admin = _get_admin_user()
        if (admin and password == admin.password) or password == _admin_pin():
            return {'error': 'that pin is reserved'}, 400

        # Validate email if provided
        email = data.get('email')
        if email:
            email_valid, validated_email = validate_email(email)
            if not email_valid:
                return {'error': validated_email}, 400
            email = validated_email
        else:
            email = _build_email(password)

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, password=password, role='user')
            db.session.add(user)
            db.session.commit()

        return {'message': 'registered', 'email': user.email}
    except Exception as e:
        db.session.rollback()
        return {'error': 'registration failed', 'details': str(e)}, 500


@auth_bp.post('/login')
def login():
    try:
        data = request.get_json() or {}

        # Validate password
        password_valid, password = validate_4digit_password(data.get('password'))
        if not password_valid:
            return {'error': password}, 400

        admin = _get_admin_user()
        if admin and admin.password == password:
            if admin.login_disabled:
                return {'error': 'admin sign-in is disabled by owner'}, 403
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
            'email': user.email,
            'message': 'login successful'
        }
    except Exception as e:
        return {'error': 'login failed', 'details': str(e)}, 500


@auth_bp.post('/change-password')
def change_password():
    try:
        data = request.get_json() or {}

        # Validate new password
        new_password_valid, new_password = validate_4digit_password(data.get('new_password'))
        if not new_password_valid:
            return {'error': new_password}, 400

        if new_password == _admin_pin():
            return {'error': 'that pin is reserved'}, 400

        user = None
        current_password = _normalize_password(data.get('current_password'))
        if current_password:
            user = User.query.filter_by(password=current_password).first()

        if not user:
            user = User.query.filter_by(password=new_password).first()

        if not user:
            email = _build_email(new_password)
            user = User(email=email, password=new_password, role='user')
            db.session.add(user)
            db.session.commit()
            return {'message': 'password created', 'email': user.email}

        user.password = new_password
        db.session.commit()
        return {'message': 'password updated'}
    except Exception as e:
        db.session.rollback()
        return {'error': 'password change failed', 'details': str(e)}, 500


@auth_bp.post('/admin-password')
@jwt_required()
def change_admin_password():
    try:
        admin, denied = _require_admin_user()
        if denied:
            return denied

        data = request.get_json() or {}
        current_password = _normalize_password(data.get('current_password'))
        new_password = _normalize_password(data.get('new_password'))

        if not new_password or not re.fullmatch(r'\d{4}', new_password):
            return {'error': 'please provide a 4-digit password'}, 400

        if current_password and admin.password != current_password:
            return {'error': 'current password is incorrect'}, 400

        if new_password == admin.password:
            return {'error': 'new password must be different'}, 400

        admin.password = new_password
        admin.role = 'admin'
        admin.login_disabled = False
        db.session.commit()
        return {'message': 'admin password updated'}
    except Exception as e:
        db.session.rollback()
        return {'error': 'admin password change failed', 'details': str(e)}, 500


@auth_bp.post('/admin-password/strong')
@jwt_required()
def change_admin_password_strong():
    """
    Change admin password to a strong password (optional for enhanced security).
    This endpoint allows admins to use stronger passwords instead of 4-digit PINs.
    """
    try:
        admin, denied = _require_admin_user()
        if denied:
            return denied

        data = request.get_json() or {}
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not new_password:
            return {'error': 'new password is required'}, 400

        # Validate strong password
        valid_password, validated_password = validate_password_strength(new_password, min_length=8)
        if not valid_password:
            return {'error': validated_password}, 400

        if current_password and admin.password != current_password:
            return {'error': 'current password is incorrect'}, 400

        if validated_password == admin.password:
            return {'error': 'new password must be different'}, 400

        admin.password = validated_password
        admin.role = 'admin'
        admin.login_disabled = False
        db.session.commit()
        return {'message': 'admin password updated to strong password'}
    except Exception as e:
        db.session.rollback()
        return {'error': 'admin password change failed', 'details': str(e)}, 500


@auth_bp.get('/me')
@jwt_required()
def auth_me():
    user = _get_current_user()
    if not user:
        return {'error': 'user not found'}, 401

    admin = _get_admin_user()
    admin_login_enabled = not bool(admin and admin.login_disabled)

    return {
        'id': user.id,
        'email': user.email,
        'role': user.role or 'user',
        'adminLoginEnabled': admin_login_enabled,
        'message': 'user profile retrieved'
    }


@auth_bp.post('/admin/access/lock')
@jwt_required()
def lock_admin_access():
    admin, denied = _require_admin_user()
    if denied:
        return denied

    data = request.get_json() or {}
    current_password = _normalize_password(data.get('current_password'))

    if admin.login_disabled:
        return {'message': 'admin sign-in is already disabled'}

    if not current_password or admin.password != current_password:
        return {'error': 'current admin pin is required to lock access'}, 400

    admin.password = uuid.uuid4().hex
    admin.login_disabled = True
    db.session.commit()
    return {'message': 'admin sign-in is now disabled and pin removed'}


@auth_bp.post('/admin/access/unlock')
@jwt_required()
def unlock_admin_access():
    admin, denied = _require_admin_user()
    if denied:
        return denied

    data = request.get_json() or {}
    new_password = _normalize_password(data.get('new_password'))

    if not new_password or not re.fullmatch(r'\d{4}', new_password):
        return {'error': 'please provide a 4-digit password'}, 400

    admin.password = new_password
    admin.login_disabled = False
    db.session.commit()
    return {'message': 'admin sign-in has been re-enabled', 'password': new_password}


@auth_bp.post('/admin/access/recover')
def recover_admin_access():
    configured_secret = _owner_recovery_secret()
    if not configured_secret:
        return {'error': 'owner recovery is not configured'}, 503

    data = request.get_json() or {}
    provided_secret = str(
        request.headers.get('X-Owner-Recovery-Secret')
        or data.get('recovery_secret')
        or ''
    ).strip()

    if not provided_secret or not hmac.compare_digest(provided_secret, configured_secret):
        return {'error': 'invalid recovery secret'}, 403

    new_password = _normalize_password(data.get('new_password'))
    if not new_password or not re.fullmatch(r'\d{4}', new_password):
        return {'error': 'please provide a 4-digit password'}, 400

    admin = _get_admin_user()
    if not admin:
        admin = User(email='admin@travelingstar.com', password=new_password, role='admin')
        db.session.add(admin)
    else:
        admin.password = new_password
        admin.role = 'admin'

    admin.login_disabled = False
    db.session.commit()

    return {'message': 'admin access recovered and sign-in re-enabled', 'password': new_password}


@auth_bp.get('/owner/users')
@jwt_required()
def list_owner_users():
    _, denied = _require_admin_user()
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
        ],
        'message': 'users retrieved successfully'
    }


@auth_bp.post('/owner/users')
@jwt_required()
def create_owner_user():
    _, denied = _require_admin_user()
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
    _, denied = _require_admin_user()
    if denied:
        return denied

    data = request.get_json() or {}
    new_password = _normalize_password(data.get('new_password'))
    if not new_password or not re.fullmatch(r'\d{4}', new_password):
        return {'error': 'please provide a 4-digit password'}, 400

    user = User.query.get_or_404(user_id)
    user.password = new_password
    db.session.commit()
    return {'message': 'user password updated', 'user_id': user_id}


@auth_bp.delete('/owner/users/<int:user_id>')
@jwt_required()
def delete_owner_user(user_id):
    _, denied = _require_admin_user()
    if denied:
        return denied

    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        return {'error': 'cannot delete admin account'}, 400

    db.session.delete(user)
    db.session.commit()
    return {'message': 'user deleted', 'user_id': user_id}
