"""
Input validation and sanitization utilities.

This module provides comprehensive validation functions for:
- Password validation (4-digit PINs and strong passwords)
- Email validation
- Phone number validation
- Required field validation
- Numeric validation
- Date validation
- String length validation
- Input sanitization
"""

import re
from datetime import datetime


def validate_4digit_password(password):
    """
    Validate that password is a 4-digit string.
    
    Args:
        password: The password to validate
        
    Returns:
        tuple: (is_valid, error_message_or_normalized_password)
    """
    if not password or not isinstance(password, str):
        return False, "Password is required"
    normalized = password.strip()
    if not re.fullmatch(r'\d{4}', normalized):
        return False, "Password must be exactly 4 digits"
    return True, normalized


def validate_password_strength(password, min_length=8):
    """
    Validate password strength.
    
    Requirements:
    - min_length characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    - Not a common weak password
    
    Args:
        password: The password to validate
        min_length: Minimum password length (default: 8)
        
    Returns:
        tuple: (is_valid, error_message_or_validated_password)
    """
    if not password or not isinstance(password, str):
        return False, "Password is required"
    
    password = password.strip()
    
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long"
    
    if len(password) > 128:
        return False, "Password is too long"
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    # Check for at least one digit
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    # Check for common weak passwords
    weak_patterns = [
        r'password', r'123456', r'qwerty', r'admin', r'letmein',
        r'welcome', r'login', r'abc123', r'password1'
    ]
    password_lower = password.lower()
    for pattern in weak_patterns:
        if re.search(pattern, password_lower):
            return False, "Password is too common. Please choose a stronger password"
    
    return True, password


def validate_email(email):
    """Validate email format."""
    if not email or not isinstance(email, str):
        return False, "Email is required"
    email = email.strip()
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return False, "Invalid email format"
    if len(email) > 120:
        return False, "Email is too long"
    return True, email


def validate_phone(phone):
    """Validate phone number format."""
    if not phone or not isinstance(phone, str):
        return False, "Phone number is required"
    phone = phone.strip()
    # Allow various phone formats
    if not re.match(r'^[\d\s\-\+\(\)\.]{10,20}$', phone):
        return False, "Invalid phone number format"
    return True, phone


def validate_required_fields(data, required_fields):
    """Validate that all required fields are present in data."""
    missing = []
    for field in required_fields:
        if field not in data or not data[field]:
            missing.append(field)
    
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    return True, None


def validate_positive_number(value, field_name="value"):
    """Validate that a value is a positive number."""
    try:
        num = float(value)
        if num < 0:
            return False, f"{field_name} must be positive"
        return True, num
    except (TypeError, ValueError):
        return False, f"{field_name} must be a valid number"


def validate_date_string(date_str, field_name="date"):
    """Validate date string format (YYYY-MM-DD)."""
    if not date_str or not isinstance(date_str, str):
        return False, f"{field_name} is required"
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True, date_str
    except ValueError:
        return False, f"{field_name} must be in YYYY-MM-DD format"


def validate_string_length(value, min_length=1, max_length=255, field_name="field"):
    """Validate string length constraints."""
    if not isinstance(value, str):
        return False, f"{field_name} must be a string"
    if len(value) < min_length:
        return False, f"{field_name} must be at least {min_length} characters"
    if len(value) > max_length:
        return False, f"{field_name} must not exceed {max_length} characters"
    return True, value


def sanitize_string(value, max_length=255):
    """Sanitize string input by removing potential dangerous characters."""
    if not isinstance(value, str):
        return ""
    # Remove null bytes and excessive whitespace
    sanitized = value.replace('\x00', '').strip()
    # Truncate to max length
    return sanitized[:max_length]
