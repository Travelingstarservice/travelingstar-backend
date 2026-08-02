from flask import Blueprint, request, jsonify
from models.support_message import SupportMessage
from extensions import db

support_bp = Blueprint('support_bp', __name__)

@support_bp.post('/')
def send_support():
    data = request.get_json() or {}
    phone = data.get('phone', '')
    message = data.get('message', '')

    support_message = SupportMessage(phone=phone, message=message)
    db.session.add(support_message)
    db.session.commit()

    return jsonify({
        'message': f'Support request sent to {phone}',
        'id': support_message.id
    })

@support_bp.get('/')
def list_support_messages():
    messages = SupportMessage.query.order_by(SupportMessage.id.desc()).all()
    return jsonify([
        {
            'id': msg.id,
            'phone': msg.phone,
            'message': msg.message
        }
        for msg in messages
    ])
