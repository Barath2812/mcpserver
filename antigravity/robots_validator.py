"""
robots.txt validator for ethical web scraping.
"""
import time
from typing import Optional
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import requests


class RobotsValidator:
    """
    Validates URLs against robots.txt rules.
    Caches robots.txt per domain for efficiency.
    """
    
    def __init__(self, user_agent: str = "*", cache_ttl: int = 3600):
        """
        Initialize the robots.txt validator.
        
        Args:
            user_agent: User-Agent to check rules for
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        self.user_agent = user_agent
        self.cache_ttl = cache_ttl
        self._cache: dict[str, tuple[RobotFileParser, float]] = {}
    
    def _get_robots_url(self, url: str) -> str:
        """Get the robots.txt URL for a given URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _is_cache_valid(self, domain: str) -> bool:
        """Check if cached robots.txt is still valid."""
        if domain not in self._cache:
            return False
        
        _, cached_time = self._cache[domain]
        return (time.time() - cached_time) < self.cache_ttl
    
    def _fetch_robots(self, url: str) -> Optional[RobotFileParser]:
        """
        Fetch and parse robots.txt for the given URL's domain.
        
        Args:
            url: Any URL from the target domain
        
        Returns:
            RobotFileParser instance or None if fetch failed
        """
        domain = self._get_domain(url)
        
        # Check cache first
        if self._is_cache_valid(domain):
            return self._cache[domain][0]
        
        robots_url = self._get_robots_url(url)
        rp = RobotFileParser()
        
        try:
            # Fetch robots.txt
            response = requests.get(robots_url, timeout=10)
            
            if response.status_code == 200:
                rp.parse(response.text.splitlines())
            elif response.status_code in (404, 403):
                # No robots.txt or forbidden - allow all
                rp.parse([])
            else:
                # Other errors - be conservative, allow all
                rp.parse([])
            
            # Cache the result
            self._cache[domain] = (rp, time.time())
            return rp
            
        except requests.RequestException:
            # On network error, create permissive parser
            rp.parse([])
            self._cache[domain] = (rp, time.time())
            return rp
    
    def is_allowed(self, url: str) -> bool:
        """
        Check if the given URL can be scraped according to robots.txt.
        
        Args:
            url: The URL to check
        
        Returns:
            True if scraping is allowed, False otherwise
        """
        rp = self._fetch_robots(url)
        
        if rp is None:
            # If we couldn't fetch robots.txt, allow by default
            return True
        
        return rp.can_fetch(self.user_agent, url)
    
    def get_crawl_delay(self, url: str) -> Optional[float]:
        """
        Get the crawl delay specified in robots.txt.
        
        Args:
            url: Any URL from the target domain
        
        Returns:
            Crawl delay in seconds, or None if not specified
        """
        rp = self._fetch_robots(url)
        
        if rp is None:
            return None
        
        try:
            delay = rp.crawl_delay(self.user_agent)
            return float(delay) if delay else None
        except AttributeError:
            return None
    
    def clear_cache(self, url: Optional[str] = None) -> None:
        """
        Clear the robots.txt cache.
        
        Args:
            url: If provided, clear only for this URL's domain.
                 If None, clear all cached entries.
        """
        if url:
            domain = self._get_domain(url)
            self._cache.pop(domain, None)
        else:
            self._cache.clear()


# Global validator instance
_global_validator: Optional[RobotsValidator] = None


def get_robots_validator() -> RobotsValidator:
    """Get the global robots.txt validator instance."""
    global _global_validator
    if _global_validator is None:
        _global_validator = RobotsValidator()
    return _global_validator


def is_allowed(url: str) -> bool:
    """
    Convenience function to check if a URL is allowed by robots.txt.
    
    Args:
        url: The URL to check
    
    Returns:
        True if scraping is allowed, False otherwise
    """
    return get_robots_validator().is_allowed(url)
