"""
Static web scraper using Requests and BeautifulSoup.
"""
import time
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
import sys
sys.path.insert(0, 'd:\\mcp')
from antigravity.user_agents import get_random_user_agent
from antigravity.throttle import random_delay, get_rate_limiter
from antigravity.robots_validator import is_allowed
3

@dataclass
class ScrapedContent:
    """Data class for scraped content."""
    title: str = ""
    text: str = ""
    links: list[str] = field(default_factory=list)


@dataclass
class ScrapedMetadata:
    """Data class for scrape metadata."""
    status_code: int = 0
    response_time: float = 0.0
    user_agent: str = ""


@dataclass
class ScrapeResult:
    """Complete scrape result."""
    url: str
    scraped_at: str
    scraper_type: str
    content: ScrapedContent
    metadata: ScrapedMetadata
    success: bool = True
    error: Optional[str] = None


class StaticScraper:
    """
    Static web scraper using Requests and BeautifulSoup.
    Implements anti-bot measures and ethical scraping.
    """
    
    def __init__(
        self,
        respect_robots: bool = True,
        use_delays: bool = True,
        use_rate_limiting: bool = True,
    ):
        """
        Initialize the static scraper.
        
        Args:
            respect_robots: Whether to respect robots.txt
            use_delays: Whether to use random delays
            use_rate_limiting: Whether to use rate limiting
        """
        self.respect_robots = respect_robots
        self.use_delays = use_delays
        self.use_rate_limiting = use_rate_limiting
        self.session = requests.Session()
        self.rate_limiter = get_rate_limiter()
        self._last_user_agent: Optional[str] = None
    
    def _get_headers(self) -> dict[str, str]:
        """Get request headers with rotated User-Agent."""
        user_agent = get_random_user_agent(exclude=self._last_user_agent)
        self._last_user_agent = user_agent
        
        return {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
    
    def _extract_content(self, soup: BeautifulSoup, url: str) -> ScrapedContent:
        """
        Extract content from parsed HTML.
        
        Args:
            soup: BeautifulSoup object
            url: Original URL (for resolving relative links)
        
        Returns:
            ScrapedContent with extracted data
        """
        # Extract title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""
        
        # Extract main text (remove script and style elements)
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
        
        # Get visible text
        text = soup.get_text(separator=" ", strip=True)
        # Clean up whitespace
        text = " ".join(text.split())
        
        # Extract links
        links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            # Convert relative URLs to absolute
            if href.startswith("/"):
                from urllib.parse import urljoin
                href = urljoin(url, href)
            if href.startswith("http"):
                links.append(href)
        
        # Remove duplicates while preserving order
        links = list(dict.fromkeys(links))
        
        return ScrapedContent(title=title, text=text, links=links)
    
    def scrape(self, url: str) -> ScrapeResult:
        """
        Scrape a URL using static methods.
        
        Args:
            url: The URL to scrape
        
        Returns:
            ScrapeResult with content and metadata
        """
        scraped_at = datetime.now(timezone.utc).isoformat()
        
        # Check robots.txt
        if self.respect_robots and not is_allowed(url):
            return ScrapeResult(
                url=url,
                scraped_at=scraped_at,
                scraper_type="static",
                content=ScrapedContent(),
                metadata=ScrapedMetadata(),
                success=False,
                error="URL disallowed by robots.txt"
            )
        
        # Check rate limiting
        if self.use_rate_limiting and not self.rate_limiter.can_make_request(url):
            wait_time = self.rate_limiter.time_until_available(url)
            time.sleep(wait_time)
        
        # Apply random delay
        if self.use_delays:
            random_delay()
        
        headers = self._get_headers()
        
        try:
            start_time = time.time()
            response = self.session.get(url, headers=headers, timeout=30)
            response_time = time.time() - start_time
            
            # Record the request for rate limiting
            if self.use_rate_limiting:
                self.rate_limiter.record_request(url)
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "lxml")
            content = self._extract_content(soup, url)
            
            metadata = ScrapedMetadata(
                status_code=response.status_code,
                response_time=round(response_time, 3),
                user_agent=headers["User-Agent"]
            )
            
            return ScrapeResult(
                url=url,
                scraped_at=scraped_at,
                scraper_type="static",
                content=content,
                metadata=metadata,
                success=True
            )
            
        except requests.RequestException as e:
            return ScrapeResult(
                url=url,
                scraped_at=scraped_at,
                scraper_type="static",
                content=ScrapedContent(),
                metadata=ScrapedMetadata(user_agent=headers["User-Agent"]),
                success=False,
                error=str(e)
            )
    
    def close(self) -> None:
        """Close the session."""
        self.session.close()


# Convenience function
def scrape_static(url: str) -> ScrapeResult:
    """
    Scrape a URL using the static scraper.
    
    Args:
        url: The URL to scrape
    
    Returns:
        ScrapeResult with content and metadata
    """
    scraper = StaticScraper()
    try:
        return scraper.scrape(url)
    finally:
        scraper.close()
