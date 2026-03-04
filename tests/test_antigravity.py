"""
Tests for antigravity (anti-bot) layer.
"""
import pytest
import time
import sys
sys.path.insert(0, 'd:\\mcp')

from antigravity.user_agents import get_random_user_agent, get_user_agent_for_platform
from antigravity.throttle import random_delay, RateLimiter
from antigravity.robots_validator import RobotsValidator, is_allowed
from antigravity.stealth import get_stealth_browser_config, get_stealth_context_config


class TestUserAgentRotation:
    """Tests for User-Agent rotation."""
    
    def test_get_random_user_agent(self):
        """Test getting a random User-Agent."""
        ua = get_random_user_agent()
        
        assert ua is not None
        assert len(ua) > 0
        assert "Mozilla" in ua or "Safari" in ua or "Chrome" in ua
    
    def test_user_agent_exclusion(self):
        """Test excluding a specific User-Agent."""
        ua1 = get_random_user_agent()
        
        # Get another, excluding the first
        different_count = 0
        for _ in range(10):
            ua2 = get_random_user_agent(exclude=ua1)
            if ua2 != ua1:
                different_count += 1
        
        # At least some should be different
        assert different_count > 0
    
    def test_platform_specific_user_agent(self):
        """Test getting platform-specific User-Agent."""
        desktop_ua = get_user_agent_for_platform("desktop")
        mobile_ua = get_user_agent_for_platform("mobile")
        
        assert desktop_ua is not None
        assert mobile_ua is not None
        
        # Desktop UAs should contain desktop patterns
        assert any(p in desktop_ua for p in ["Windows", "Macintosh", "X11"])
        
        # Mobile UAs should contain mobile patterns
        assert any(p in mobile_ua for p in ["iPhone", "Android", "Mobile"])


class TestThrottling:
    """Tests for request throttling."""
    
    def test_random_delay(self):
        """Test random delay function."""
        start = time.time()
        delay = random_delay(min_seconds=0.1, max_seconds=0.2)
        elapsed = time.time() - start
        
        assert 0.1 <= delay <= 0.2
        assert 0.1 <= elapsed <= 0.3  # Allow some tolerance
    
    def test_rate_limiter_can_make_request(self):
        """Test rate limiter allows requests."""
        limiter = RateLimiter(max_requests_per_minute=5)
        
        # First request should be allowed
        assert limiter.can_make_request("https://example.com") is True
    
    def test_rate_limiter_blocks_excess(self):
        """Test rate limiter blocks excess requests."""
        limiter = RateLimiter(max_requests_per_minute=2)
        
        # Make requests
        limiter.record_request("https://example.com")
        limiter.record_request("https://example.com")
        
        # Third should be blocked
        assert limiter.can_make_request("https://example.com") is False
    
    def test_rate_limiter_per_domain(self):
        """Test rate limiting is per-domain."""
        limiter = RateLimiter(max_requests_per_minute=2)
        
        # Fill up one domain
        limiter.record_request("https://example.com")
        limiter.record_request("https://example.com")
        
        # Different domain should still be allowed
        assert limiter.can_make_request("https://other.com") is True


class TestRobotsValidator:
    """Tests for robots.txt validation."""
    
    def test_is_allowed_example_com(self):
        """Test robots.txt check for example.com."""
        result = is_allowed("https://example.com")
        
        # example.com allows crawling
        assert result is True
    
    def test_robots_validator_caching(self):
        """Test that robots.txt is cached."""
        validator = RobotsValidator()
        
        # First call fetches
        validator.is_allowed("https://example.com")
        
        # Second call should use cache
        validator.is_allowed("https://example.com/page2")
        
        # Cache should have the domain
        assert "https://example.com" in validator._cache
    
    def test_crawl_delay(self):
        """Test getting crawl delay."""
        validator = RobotsValidator()
        
        # Most sites don't specify crawl delay
        delay = validator.get_crawl_delay("https://example.com")
        
        # Should be None or a number
        assert delay is None or isinstance(delay, float)


class TestStealthConfig:
    """Tests for Playwright stealth configuration."""
    
    def test_browser_config(self):
        """Test stealth browser configuration."""
        config = get_stealth_browser_config()
        
        assert "headless" in config
        assert "args" in config
        assert isinstance(config["args"], list)
        
        # Should have anti-detection args
        args = " ".join(config["args"])
        assert "AutomationControlled" in args
    
    def test_context_config(self):
        """Test stealth context configuration."""
        config = get_stealth_context_config()
        
        assert "viewport" in config
        assert "user_agent" in config
        assert "locale" in config
        assert "extra_http_headers" in config
        
        # Viewport should have width and height
        assert "width" in config["viewport"]
        assert "height" in config["viewport"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
