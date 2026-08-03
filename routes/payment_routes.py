import os
from decimal import Decimal, InvalidOperation
from datetime import datetime

from flask import Blueprint, jsonify, request
from routes.settings_routes import business_settings

payment_bp = Blueprint('payment_bp', __name__)

ALLOWED_METHODS = {'ach', 'bank', 'wire', 'link', 'credit', 'debit', 'bank_transfer', 'instant_bank_transfer'}
PROCESSOR_LABELS = {
    'ach': 'ACH Transfer Gateway',
    'bank': 'Bank Account Transfer Gateway',
    'wire': 'Wire Transfer Gateway',
    'link': 'Secure Payment Link Gateway',
    'credit': 'Credit Card Checkout',
    'debit': 'Debit Card Checkout',
    'bank_transfer': 'Bank Transfer Checkout',
    'instant_bank_transfer': 'Instant Bank Transfer Checkout'
}


CHECKOUT_LINKS = {
    'credit': os.getenv('PAYMENT_LINK_CREDIT', ''),
    'debit': os.getenv('PAYMENT_LINK_DEBIT', ''),
    'bank_transfer': os.getenv('PAYMENT_LINK_BANK_TRANSFER', ''),
    'instant_bank_transfer': os.getenv('PAYMENT_LINK_INSTANT_BANK_TRANSFER', ''),
    'link': os.getenv('PAYMENT_LINK_DEFAULT', '')
}


def _normalize_method(raw_method):
    method = (raw_method or 'bank').lower()
    if method == 'bank_transfer':
        return 'bank_transfer'
    if method in {'instant_bank', 'instant_bank_transfer'}:
        return 'instant_bank_transfer'
    return method


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
    method = _normalize_method(data.get('method'))
    booking_id = data.get('booking_id')
    amount = _parse_amount(data.get('amount', 50))

    if method not in ALLOWED_METHODS:
        return jsonify({'status': 'failed', 'message': 'Unsupported payment method'}), 400

    payment_controls = business_settings.get('payments', {})
    method_allowed = {
        'debit': bool(payment_controls.get('enableDebit', True)),
        'credit': bool(payment_controls.get('enableCredit', True)),
        'bank_transfer': bool(payment_controls.get('enableInstantBankTransfer', True)),
        'instant_bank_transfer': bool(payment_controls.get('enableInstantBankTransfer', True)),
        'link': bool(payment_controls.get('enableSecureLink', True)),
    }

    if method in method_allowed and not method_allowed[method]:
        return jsonify({'status': 'failed', 'message': f'{method.replace("_", " ").title()} is currently disabled by admin settings'}), 400

    if amount is None:
        return jsonify({'status': 'failed', 'message': 'Amount must be greater than zero'}), 400

    payment_ref = f"BANK-{method.upper()}-{booking_id or 'BOOKING'}-{int(datetime.utcnow().timestamp())}"

    configured_bank_info = business_settings.get('bankInfo', {})
    support_phone = payment_controls.get('supportPhone') or '252 886-5996'

    transfer_instructions = {
        'bank_name': data.get('bank_name') or configured_bank_info.get('bankName') or 'Business account details available by phone',
        'bank_account_holder': data.get('bank_account_holder') or configured_bank_info.get('accountHolder') or 'Traveling Star Service',
        'bank_reference': data.get('bank_reference') or configured_bank_info.get('routingLast4') or 'Reference line for booking confirmation',
        'wire_destination': data.get('wire_destination') or configured_bank_info.get('paymentInstructions') or f'Call or text {support_phone} to receive destination details securely',
        'payment_link_email': data.get('payment_link_email') or business_settings.get('email') or 'booking@travelingstar.com',
        'account_number_last4': configured_bank_info.get('accountNumberLast4') or '',
        'zelle_email': configured_bank_info.get('zelleEmail') or '',
        'cash_app_tag': configured_bank_info.get('cashAppTag') or ''
    }

    checkout_url = CHECKOUT_LINKS.get(method) or CHECKOUT_LINKS.get('link')

    message = (
        f'{PROCESSOR_LABELS[method]} is ready. '
        f'Please confirm final details by calling or texting {support_phone}.'
    )

    if method in {'credit', 'debit', 'bank_transfer', 'link'} and checkout_url:
        message = f'{PROCESSOR_LABELS[method]} is ready. Continue to secure checkout using the provided link.'

    return jsonify({
        'status': 'pending',
        'processor': 'bank-account',
        'message': message,
        'method': method,
        'booking_id': booking_id,
        'amount': amount,
        'currency': 'USD',
        'payment_reference': payment_ref,
        'checkout_url': checkout_url,
        'transfer_instructions': transfer_instructions,
        'processed_at': datetime.utcnow().isoformat()
    })
