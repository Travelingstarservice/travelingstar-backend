"""
Rate limiting implementation for API endpoints.

This module provides:
- In-memory rate limiting with IP-based tracking
- Automatic IP blocking for excessive requests
- Configurable rate limits per endpoint
- Decorator-based rate limiting application
- Rate limit headers in responses
"""

import time
from collections import defaultdict
from flask import request, jsonify
from functools import wraps


class RateLimiter:
    """
    In-memory rate limiter with IP-based tracking and automatic blocking.
    
    Features:
    - Tracks requests per IP within time windows
    - Automatically blocks IPs exceeding rate limits
    - Configurable limits and time windows
    - Temporary blocking with automatic unblocking
    """
    
    def __init__(self):
        # Dictionary to store request timestamps: {ip: [timestamp1, timestamp2, ...]}
        self.requests = defaultdict(list)
        # Dictionary to store blocked IPs: {ip: blocked_until_timestamp}
        self.blocked_ips = {}
        
        # Rate limiting configuration
        self.max_requests = 10  # max requests per window
        self.window_seconds = 60  # time window in seconds
        self.block_duration = 300  # block duration in seconds (5 minutes)
    
    def _get_client_ip(self):
        """Get client IP address from request."""
        # Check for proxy headers first
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        if request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        return request.remote_addr
    
    def _cleanup_old_requests(self, ip):
        """Remove requests older than the time window."""
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        self.requests[ip] = [
            timestamp for timestamp in self.requests[ip] 
            if timestamp > cutoff_time
        ]
    
    def _check_blocked(self, ip):
        """Check if IP is currently blocked."""
        if ip in self.blocked_ips:
            if time.time() < self.blocked_ips[ip]:
                return True
            else:
                # Block expired, remove it
                del self.blocked_ips[ip]
        return False
    
    def _record_request(self, ip):
        """Record a request for the given IP."""
        current_time = time.time()
        self.requests[ip].append(current_time)
    
    def _block_ip(self, ip):
        """Block an IP for the configured duration."""
        self.blocked_ips[ip] = time.time() + self.block_duration
    
    def is_allowed(self, ip=None):
        """Check if a request from the given IP is allowed."""
        if ip is None:
            ip = self._get_client_ip()
        
        # Check if IP is blocked
        if self._check_blocked(ip):
            return False, "IP address is temporarily blocked due to excessive requests"
        
        # Clean up old requests
        self._cleanup_old_requests(ip)
        
        # Check if under rate limit
        if len(self.requests[ip]) >= self.max_requests:
            self._block_ip(ip)
            return False, "Rate limit exceeded. IP temporarily blocked."
        
        # Record this request
        self._record_request(ip)
        return True, None
    
    def get_remaining_requests(self, ip=None):
        """Get remaining requests for the given IP."""
        if ip is None:
            ip = self._get_client_ip()
        
        self._cleanup_old_requests(ip)
        return max(0, self.max_requests - len(self.requests[ip]))


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(max_requests=None, window_seconds=None):
    """
    Decorator to apply rate limiting to a route.
    
    Args:
        max_requests: Maximum number of requests allowed (optional, uses default if not provided)
        window_seconds: Time window in seconds (optional, uses default if not provided)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Custom limits if provided
            if max_requests is not None:
                original_max = rate_limiter.max_requests
                rate_limiter.max_requests = max_requests
            
            if window_seconds is not None:
                original_window = rate_limiter.window_seconds
                rate_limiter.window_seconds = window_seconds
            
            # Check rate limit
            allowed, message = rate_limiter.is_allowed()
            
            # Restore original limits if they were changed
            if max_requests is not None:
                rate_limiter.max_requests = original_max
            if window_seconds is not None:
                rate_limiter.window_seconds = original_window
            
            if not allowed:
                response = jsonify({
                    'error': 'rate_limit_exceeded',
                    'message': message
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(rate_limiter.block_duration)
                return response
            
            # Add rate limit headers
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(rate_limiter.max_requests)
                response.headers['X-RateLimit-Remaining'] = str(rate_limiter.get_remaining_requests())
                response.headers['X-RateLimit-Window'] = str(rate_limiter.window_seconds)
            
            return response
        
        return decorated_function
    return decorator


def auth_rate_limit():
    """Rate limiting specifically for authentication endpoints (stricter limits)."""
    return rate_limit(max_requests=5, window_seconds=60)
