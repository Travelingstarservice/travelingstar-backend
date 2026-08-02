from decimal import Decimal, InvalidOperation
from datetime import datetime

from flask import Blueprint, jsonify, request

payment_bp = Blueprint('payment_bp', __name__)

ALLOWED_METHODS = {'ach', 'bank', 'wire', 'link'}
PROCESSOR_LABELS = {
    'ach': 'ACH Transfer Gateway',
    'bank': 'Bank Account Transfer Gateway',
    'wire': 'Wire Transfer Gateway',
    'link': 'Secure Payment Link Gateway'
}


def _parse_amount(raw_amount):
    try:
        amount = Decimal(str(raw_amount or 50))
    except (InvalidOperation, TypeError, ValueError):
        return None

    if amount <= 0:
        return None

    return float(amount)


@payment_bp.post('')
@payment_bp.post('/')
def pay():
    data = request.get_json() or {}
    method = (data.get('method') or 'bank').lower()
    booking_id = data.get('booking_id')
    amount = _parse_amount(data.get('amount', 50))

    if method not in ALLOWED_METHODS:
        return jsonify({'status': 'failed', 'message': 'Unsupported payment method'}), 400

    if amount is None:
        return jsonify({'status': 'failed', 'message': 'Amount must be greater than zero'}), 400

    payment_ref = f"BANK-{method.upper()}-{booking_id or 'BOOKING'}-{int(datetime.utcnow().timestamp())}"

    transfer_instructions = {
        'bank_name': data.get('bank_name') or 'Business account details available by phone',
        'bank_account_holder': data.get('bank_account_holder') or 'Traveling Star Service',
        'bank_reference': data.get('bank_reference') or 'Reference line for booking confirmation',
        'wire_destination': data.get('wire_destination') or 'Call or text 252 886-5996 to receive destination details securely',
        'payment_link_email': data.get('payment_link_email') or 'booking@travelingstar.com'
    }

    return jsonify({
        'status': 'pending',
        'processor': 'bank-account',
        'message': f'{PROCESSOR_LABELS[method]} is now configured for secure bank-account settlement. Please confirm transfer details by calling or texting 252 886-5996.',
        'method': method,
        'booking_id': booking_id,
        'amount': amount,
        'currency': 'USD',
        'payment_reference': payment_ref,
        'transfer_instructions': transfer_instructions,
        'processed_at': datetime.utcnow().isoformat()
    })
