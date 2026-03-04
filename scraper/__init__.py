"""
Scraper module - Web scraping engines.
"""
from .static_scraper import scrape_static, StaticScraper
from .dynamic_scraper import scrape_dynamic, DynamicScraper
from .strategy_selector import needs_javascript, select_scraper, auto_scrape

__all__ = [
    "scrape_static",
    "StaticScraper",
    "scrape_dynamic",
    "DynamicScraper",
    "needs_javascript",
    "select_scraper",
    "auto_scrape",
]
