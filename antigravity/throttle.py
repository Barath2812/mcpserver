"""
Request throttling and rate limiting for anti-bot detection.
"""
import asyncio
import random
import time
from collections import defaultdict
from typing import Optional
from urllib.parse import urlparse
import sys
sys.path.insert(0, 'd:\\mcp')
from config import (
    DEFAULT_MIN_DELAY,
    DEFAULT_MAX_DELAY,
    MAX_REQUESTS_PER_DOMAIN_PER_MINUTE,
)


def random_delay(
    min_seconds: float = DEFAULT_MIN_DELAY,
    max_seconds: float = DEFAULT_MAX_DELAY
) -> float:
    """
    Introduce a random delay to simulate human-like behavior.
    
    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
    
    Returns:
        The actual delay time in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
    return delay


async def async_random_delay(
    min_seconds: float = DEFAULT_MIN_DELAY,
    max_seconds: float = DEFAULT_MAX_DELAY
) -> float:
    """
    Async version of random delay.
    
    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
    
    Returns:
        The actual delay time in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)
    return delay


class RateLimiter:
    """
    Rate limiter that tracks requests per domain.
    Implements a sliding window approach.
    """
    
    def __init__(self, max_requests_per_minute: int = MAX_REQUESTS_PER_DOMAIN_PER_MINUTE):
        """
        Initialize the rate limiter.
        
        Args:
            max_requests_per_minute: Maximum requests allowed per domain per minute
        """
        self.max_requests = max_requests_per_minute
        self._request_times: dict[str, list[float]] = defaultdict(list)
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc or parsed.path.split('/')[0]
    
    def _clean_old_requests(self, domain: str) -> None:
        """Remove request timestamps older than 1 minute."""
        current_time = time.time()
        cutoff_time = current_time - 60  # 1 minute ago
        
        self._request_times[domain] = [
            t for t in self._request_times[domain]
            if t > cutoff_time
        ]
    
    def can_make_request(self, url: str) -> bool:
        """
        Check if a request can be made to the given URL.
        
        Args:
            url: The URL to check
        
        Returns:
            True if the request is allowed, False otherwise
        """
        domain = self._get_domain(url)
        self._clean_old_requests(domain)
        
        return len(self._request_times[domain]) < self.max_requests
    
    def record_request(self, url: str) -> None:
        """
        Record a request to the given URL.
        
        Args:
            url: The URL that was requested
        """
        domain = self._get_domain(url)
        self._request_times[domain].append(time.time())
    
    def time_until_available(self, url: str) -> float:
        """
        Get the time in seconds until a request to this URL is allowed.
        
        Args:
            url: The URL to check
        
        Returns:
            Time in seconds until the request is allowed (0 if already allowed)
        """
        if self.can_make_request(url):
            return 0.0
        
        domain = self._get_domain(url)
        self._clean_old_requests(domain)
        
        if not self._request_times[domain]:
            return 0.0
        
        # Time until the oldest request expires
        oldest_request = min(self._request_times[domain])
        return max(0, (oldest_request + 60) - time.time())
    
    async def wait_if_needed(self, url: str) -> float:
        """
        Wait if rate limit would be exceeded.
        
        Args:
            url: The URL to request
        
        Returns:
            Time waited in seconds
        """
        wait_time = self.time_until_available(url)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        return wait_time
    
    def reset(self, url: Optional[str] = None) -> None:
        """
        Reset rate limit tracking.
        
        Args:
            url: If provided, reset only for this URL's domain.
                 If None, reset all domains.
        """
        if url:
            domain = self._get_domain(url)
            self._request_times[domain] = []
        else:
            self._request_times.clear()


# Global rate limiter instance
_global_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter()
    return _global_rate_limiter
