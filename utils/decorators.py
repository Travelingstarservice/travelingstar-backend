from functools import wraps
from flask import request, jsonify

def require_json(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'JSON required'}), 400
        return fn(*args, **kwargs)
    return wrapper
