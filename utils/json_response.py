"""
JSON response utilities for consistent API responses.

This module provides helper functions to ensure all API responses
have consistent JSON structure with proper error handling and validation.
"""

from flask import jsonify
from typing import Any, Dict, Optional, Tuple


def success_response(data: Optional[Dict[str, Any]] = None, message: str = "success", status_code: int = 200) -> Tuple[Any, int]:
    """
    Create a standardized success response.
    
    Args:
        data: Optional data payload to include in response
        message: Success message
        status_code: HTTP status code
        
    Returns:
        Tuple of (jsonified response, status_code)
    """
    response = {
        'success': True,
        'message': message
    }
    
    if data:
        response.update(data)
    
    return jsonify(response), status_code


def error_response(message: str, status_code: int = 400, details: Optional[str] = None) -> Tuple[Any, int]:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        details: Optional detailed error information
        
    Returns:
        Tuple of (jsonified response, status_code)
    """
    response = {
        'success': False,
        'error': message
    }
    
    if details:
        response['details'] = details
    
    return jsonify(response), status_code


def validate_json_response(data: Dict[str, Any]) -> bool:
    """
    Validate that a response dictionary has proper structure.
    
    Args:
        data: Response dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(data, dict):
        return False
    
    # Check for either success or error field
    has_success = 'success' in data
    has_error = 'error' in data
    
    if not has_success and not has_error:
        return False
    
    return True
