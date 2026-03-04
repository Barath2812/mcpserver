"""
Dynamic web scraper using Playwright for JavaScript-rendered pages.
"""
import asyncio
import time
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import sys
sys.path.insert(0, 'd:\\mcp')

from antigravity.throttle import async_random_delay, get_rate_limiter
from antigravity.robots_validator import is_allowed
from antigravity.stealth import (
    get_stealth_browser_config,
    get_stealth_context_config,
    apply_stealth_scripts,
)


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


class DynamicScraper:
    """
    Dynamic web scraper using Playwright.
    Handles JavaScript-rendered pages with stealth mode.
    """
    
    def __init__(
        self,
        respect_robots: bool = True,
        use_delays: bool = True,
        use_rate_limiting: bool = True,
    ):
        """
        Initialize the dynamic scraper.
        
        Args:
            respect_robots: Whether to respect robots.txt
            use_delays: Whether to use random delays
            use_rate_limiting: Whether to use rate limiting
        """
        self.respect_robots = respect_robots
        self.use_delays = use_delays
        self.use_rate_limiting = use_rate_limiting
        self.rate_limiter = get_rate_limiter()
        self._browser = None
        self._playwright = None
    
    async def _ensure_browser(self):
        """Ensure browser is initialized."""
        if self._browser is None:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            browser_config = get_stealth_browser_config()
            self._browser = await self._playwright.chromium.launch(**browser_config)
    
    async def _extract_content(self, page, url: str) -> ScrapedContent:
        """
        Extract content from page.
        
        Args:
            page: Playwright page object
            url: Original URL
        
        Returns:
            ScrapedContent with extracted data
        """
        # Extract title
        title = await page.title()
        
        # Extract visible text
        text = await page.evaluate("""
            () => {
                // Remove script and style elements
                const elementsToRemove = document.querySelectorAll('script, style, nav, footer, header, aside, noscript');
                elementsToRemove.forEach(el => el.remove());
                
                // Get body text
                return document.body ? document.body.innerText : '';
            }
        """)
        
        # Clean up text
        text = " ".join(text.split())
        
        # Extract links
        links = await page.evaluate("""
            (baseUrl) => {
                const links = [];
                const anchors = document.querySelectorAll('a[href]');
                anchors.forEach(a => {
                    let href = a.href;
                    if (href && href.startsWith('http')) {
                        links.push(href);
                    }
                });
                return [...new Set(links)];  // Remove duplicates
            }
        """, url)
        
        return ScrapedContent(title=title, text=text, links=links)
    
    async def scrape_async(self, url: str) -> ScrapeResult:
        """
        Scrape a URL using Playwright (async).
        
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
                scraper_type="dynamic",
                content=ScrapedContent(),
                metadata=ScrapedMetadata(),
                success=False,
                error="URL disallowed by robots.txt"
            )
        
        # Check rate limiting
        if self.use_rate_limiting:
            await self.rate_limiter.wait_if_needed(url)
        
        # Apply random delay
        if self.use_delays:
            await async_random_delay()
        
        context_config = get_stealth_context_config()
        user_agent = context_config.get("user_agent", "")
        
        try:
            await self._ensure_browser()
            
            # Create new context with stealth settings
            context = await self._browser.new_context(**context_config)
            page = await context.new_page()
            
            # Apply stealth scripts
            await apply_stealth_scripts(page)
            
            start_time = time.time()
            
            # Navigate to URL
            response = await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for dynamic content
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(1)  # Extra wait for JS rendering
            
            response_time = time.time() - start_time
            
            # Record request for rate limiting
            if self.use_rate_limiting:
                self.rate_limiter.record_request(url)
            
            # Extract content
            content = await self._extract_content(page, url)
            
            status_code = response.status if response else 0
            
            metadata = ScrapedMetadata(
                status_code=status_code,
                response_time=round(response_time, 3),
                user_agent=user_agent
            )
            
            await context.close()
            
            return ScrapeResult(
                url=url,
                scraped_at=scraped_at,
                scraper_type="dynamic",
                content=content,
                metadata=metadata,
                success=True
            )
            
        except Exception as e:
            return ScrapeResult(
                url=url,
                scraped_at=scraped_at,
                scraper_type="dynamic",
                content=ScrapedContent(),
                metadata=ScrapedMetadata(user_agent=user_agent),
                success=False,
                error=str(e)
            )
    
    def scrape(self, url: str) -> ScrapeResult:
        """
        Scrape a URL using Playwright (sync wrapper).
        
        Args:
            url: The URL to scrape
        
        Returns:
            ScrapeResult with content and metadata
        """
        return asyncio.get_event_loop().run_until_complete(self.scrape_async(url))
    
    async def close_async(self) -> None:
        """Close browser and playwright (async)."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
    
    def close(self) -> None:
        """Close browser and playwright."""
        if self._browser or self._playwright:
            asyncio.get_event_loop().run_until_complete(self.close_async())


# Convenience function
def scrape_dynamic(url: str) -> ScrapeResult:
    """
    Scrape a URL using the dynamic scraper.
    
    Args:
        url: The URL to scrape
    
    Returns:
        ScrapeResult with content and metadata
    """
    async def _scrape():
        scraper = DynamicScraper()
        try:
            return await scraper.scrape_async(url)
        finally:
            await scraper.close_async()
    
    # Check if there's already a running event loop (e.g., from FastAPI)
    try:
        loop = asyncio.get_running_loop()
        # If we're in an existing loop, use nest_asyncio to allow nested runs
        import nest_asyncio
        nest_asyncio.apply()
        return loop.run_until_complete(_scrape())
    except RuntimeError:
        # No running loop, safe to use asyncio.run()
        return asyncio.run(_scrape())
