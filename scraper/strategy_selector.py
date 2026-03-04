"""
Strategy selector for automatic scraper type detection.
"""
import re
from typing import Literal
import requests
from bs4 import BeautifulSoup
import sys
sys.path.insert(0, 'd:\\mcp')

from antigravity.user_agents import get_random_user_agent


# Patterns that indicate JavaScript-heavy content
JS_HEAVY_PATTERNS = [
    # React
    r'<div id="root"></div>',
    r'<div id="app"></div>',
    r'react\.production\.min\.js',
    r'react-dom\.production\.min\.js',
    r'_next/static',
    # Vue
    r'v-cloak',
    r'vue\.runtime\.min\.js',
    r'__NUXT__',
    # Angular
    r'ng-version',
    r'ng-app',
    r'angular\.min\.js',
    # Generic SPA indicators
    r'__INITIAL_STATE__',
    r'__PRELOADED_STATE__',
    r'window\.__STATE__',
    r'window\.App\s*=',
    # Empty body with scripts
    r'<body[^>]*>\s*<script',
    # Webpack/bundled apps
    r'webpackJsonp',
    r'__webpack_require__',
]

# Minimum content length to consider page as properly loaded
MIN_CONTENT_LENGTH = 500


def needs_javascript(html: str) -> bool:
    """
    Analyze HTML to determine if JavaScript rendering is needed.
    
    Args:
        html: Raw HTML content
    
    Returns:
        True if JavaScript rendering is likely needed
    """
    # Check for JS-heavy patterns
    for pattern in JS_HEAVY_PATTERNS:
        if re.search(pattern, html, re.IGNORECASE):
            return True
    
    # Parse HTML and check content
    soup = BeautifulSoup(html, "lxml")
    
    # Remove scripts and styles
    for element in soup(["script", "style"]):
        element.decompose()
    
    # Get visible text
    text = soup.get_text(strip=True)
    
    # If very little text content, might be JS-rendered
    if len(text) < MIN_CONTENT_LENGTH:
        # Check if there are many script tags
        script_tags = soup.find_all("script")
        if len(script_tags) > 5:
            return True
    
    # Check for loading/placeholder elements
    loading_indicators = [
        soup.find(class_=re.compile(r'loading|spinner|skeleton', re.I)),
        soup.find(id=re.compile(r'loading|spinner', re.I)),
    ]
    if any(loading_indicators):
        return True
    
    return False


def analyze_url(url: str) -> dict:
    """
    Analyze a URL to determine scraping strategy.
    
    Args:
        url: The URL to analyze
    
    Returns:
        Dictionary with analysis results
    """
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        html = response.text
        
        js_needed = needs_javascript(html)
        
        return {
            "url": url,
            "status_code": response.status_code,
            "content_length": len(html),
            "needs_javascript": js_needed,
            "recommended_scraper": "dynamic" if js_needed else "static",
        }
    except requests.RequestException as e:
        return {
            "url": url,
            "error": str(e),
            "needs_javascript": True,  # Default to dynamic on error
            "recommended_scraper": "dynamic",
        }


def select_scraper(url: str) -> Literal["static", "dynamic"]:
    """
    Select the appropriate scraper type for a URL.
    
    Args:
        url: The URL to scrape
    
    Returns:
        'static' or 'dynamic' based on analysis
    """
    analysis = analyze_url(url)
    return analysis["recommended_scraper"]


def auto_scrape(url: str):
    """
    Automatically scrape a URL using the appropriate scraper.
    
    Args:
        url: The URL to scrape
    
    Returns:
        ScrapeResult from the selected scraper
    """
    from .static_scraper import scrape_static
    from .dynamic_scraper import scrape_dynamic
    
    scraper_type = select_scraper(url)
    
    if scraper_type == "dynamic":
        return scrape_dynamic(url)
    else:
        return scrape_static(url)
