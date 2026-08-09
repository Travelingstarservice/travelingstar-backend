"""
Unit tests for rate limiting functionality.
"""

import pytest
import time
import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.rate_limiter import RateLimiter, rate_limit


class TestRateLimiter:
    """Test rate limiter functionality."""
    
    def setup_method(self):
        """Setup a fresh rate limiter for each test."""
        self.limiter = RateLimiter()
        self.limiter.max_requests = 5
        self.limiter.window_seconds = 60
    
    def test_initial_state(self):
        """Test initial rate limiter state."""
        assert self.limiter.max_requests == 5
        assert self.limiter.window_seconds == 60
        assert len(self.limiter.requests) == 0
        assert len(self.limiter.blocked_ips) == 0
    
    def test_allowed_request(self):
        """Test that requests within limits are allowed."""
        allowed, message = self.limiter.is_allowed("127.0.0.1")
        assert allowed == True
        assert message is None
    
    def test_multiple_allowed_requests(self):
        """Test multiple requests within limits."""
        for _ in range(5):
            allowed, message = self.limiter.is_allowed("127.0.0.1")
            assert allowed == True
    
    def test_rate_limit_exceeded(self):
        """Test that requests exceeding limits are blocked."""
        # Make 5 allowed requests
        for _ in range(5):
            self.limiter.is_allowed("127.0.0.1")
        
        # 6th request should be blocked
        allowed, message = self.limiter.is_allowed("127.0.0.1")
        assert allowed == False
        assert "blocked" in message.lower()
    
    def test_different_ips_independent(self):
        """Test that different IPs have independent rate limits."""
        # IP1 makes 5 requests
        for _ in range(5):
            self.limiter.is_allowed("192.168.1.1")
        
        # IP1 should be blocked
        allowed1, _ = self.limiter.is_allowed("192.168.1.1")
        assert allowed1 == False
        
        # IP2 should still be allowed
        allowed2, _ = self.limiter.is_allowed("192.168.1.2")
        assert allowed2 == True
    
    def test_old_requests_cleanup(self):
        """Test that old requests are cleaned up."""
        # Make a request
        self.limiter.is_allowed("127.0.0.1")
        
        # Manually set old timestamp
        old_time = time.time() - 120  # 2 minutes ago
        self.limiter.requests["127.0.0.1"][0] = old_time
        
        # Make another request
        allowed, _ = self.limiter.is_allowed("127.0.0.1")
        assert allowed == True
    
    def test_ip_blocking(self):
        """Test that IPs are temporarily blocked."""
        # Exceed rate limit
        for _ in range(6):
            self.limiter.is_allowed("127.0.0.1")
        
        # IP should be blocked
        assert "127.0.0.1" in self.limiter.blocked_ips
    
    def test_block_expiry(self):
        """Test that blocks expire after duration."""
        # Set short block duration for testing
        self.limiter.block_duration = 1  # 1 second
        
        # Exceed rate limit
        for _ in range(6):
            self.limiter.is_allowed("127.0.0.1")
        
        # Should be blocked
        allowed1, _ = self.limiter.is_allowed("127.0.0.1")
        assert allowed1 == False
        
        # Manually expire the block and clear old requests for testing
        self.limiter.blocked_ips["127.0.0.1"] = time.time() - 1
        self.limiter.requests["127.0.0.1"] = []  # Clear old requests
        
        # Should be allowed again
        allowed2, _ = self.limiter.is_allowed("127.0.0.1")
        assert allowed2 == True
    
    def test_remaining_requests(self):
        """Test remaining requests calculation."""
        # Make 2 requests
        for _ in range(2):
            self.limiter.is_allowed("127.0.0.1")
        
        remaining = self.limiter.get_remaining_requests("127.0.0.1")
        assert remaining == 3  # 5 - 2 = 3
    
    def test_custom_limits(self):
        """Test custom rate limits."""
        custom_limiter = RateLimiter()
        custom_limiter.max_requests = 3
        custom_limiter.window_seconds = 30
        
        # Make 3 requests
        for _ in range(3):
            allowed, _ = custom_limiter.is_allowed("127.0.0.1")
            assert allowed == True
        
        # 4th should be blocked
        allowed, _ = custom_limiter.is_allowed("127.0.0.1")
        assert allowed == False


class TestRateLimitDecorator:
    """Test rate limiting decorator."""
    
    @pytest.mark.skip("Requires Flask request context")
    def test_decorator_allows_requests(self):
        """Test that decorator allows requests within limits."""
        @rate_limit(max_requests=3)
        def test_function():
            return "success"
        
        for _ in range(3):
            result = test_function()
            assert result == "success"
    
    @pytest.mark.skip("Requires Flask request context")
    def test_decorator_blocks_requests(self):
        """Test that decorator blocks excessive requests."""
        @rate_limit(max_requests=2)
        def test_function():
            return "success"
        
        # First 2 should succeed
        for _ in range(2):
            result = test_function()
            assert result == "success"
        
        # 3rd should be blocked (would return error response in real usage)
        # For testing, we just check the limiter state
        from utils.rate_limiter import rate_limiter
        allowed, _ = rate_limiter.is_allowed("127.0.0.1")
        assert allowed == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])