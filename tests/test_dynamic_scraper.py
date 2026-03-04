"""
Tests for the dynamic scraper.
"""
import pytest
import asyncio
import sys
sys.path.insert(0, 'd:\\mcp')

from scraper.dynamic_scraper import DynamicScraper, scrape_dynamic


class TestDynamicScraper:
    """Tests for DynamicScraper class."""
    
    @pytest.mark.asyncio
    async def test_scrape_example_com_async(self):
        """Test async scraping of example.com."""
        scraper = DynamicScraper(use_delays=False, use_rate_limiting=False)
        
        try:
            result = await scraper.scrape_async("https://example.com")
            
            assert result.success is True
            assert result.url == "https://example.com"
            assert result.scraper_type == "dynamic"
            assert result.content.title is not None
            assert "Example" in result.content.title
            assert len(result.content.text) > 0
            assert result.metadata.status_code == 200
        finally:
            await scraper.close_async()
    
    def test_scrape_example_com_sync(self):
        """Test sync wrapper for scraping."""
        result = scrape_dynamic("https://example.com")
        
        assert result.success is True
        assert result.scraper_type == "dynamic"
        assert "Example" in result.content.title
    
    def test_scrape_js_heavy_site(self):
        """Test scraping a JavaScript-heavy site."""
        # httpbin.org has some JavaScript content
        result = scrape_dynamic("https://httpbin.org/html")
        
        assert result.success is True
        assert result.scraper_type == "dynamic"
        assert len(result.content.text) > 0
    
    def test_scrape_invalid_url(self):
        """Test handling of invalid URL."""
        result = scrape_dynamic("https://this-domain-definitely-does-not-exist-12345.com")
        
        assert result.success is False
        assert result.error is not None


class TestDynamicScraperContent:
    """Tests for dynamic content extraction."""
    
    def test_link_extraction(self):
        """Test link extraction from dynamic pages."""
        result = scrape_dynamic("https://example.com")
        
        assert result.success is True
        assert isinstance(result.content.links, list)
    
    def test_metadata_capture(self):
        """Test metadata is captured correctly."""
        result = scrape_dynamic("https://example.com")
        
        assert result.success is True
        assert result.metadata.status_code == 200
        assert result.metadata.response_time > 0
        assert result.metadata.user_agent is not None
        assert len(result.metadata.user_agent) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
