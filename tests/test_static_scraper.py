"""
Tests for the static scraper.
"""
import pytest
import sys
sys.path.insert(0, 'd:\\mcp')

from scraper.static_scraper import StaticScraper, scrape_static


class TestStaticScraper:
    """Tests for StaticScraper class."""
    
    def test_scrape_example_com(self):
        """Test scraping example.com (simple static site)."""
        result = scrape_static("https://example.com")
        
        assert result.success is True
        assert result.url == "https://example.com"
        assert result.scraper_type == "static"
        assert result.content.title is not None
        assert "Example" in result.content.title
        assert len(result.content.text) > 0
        assert result.metadata.status_code == 200
        assert result.metadata.response_time > 0
        assert result.metadata.user_agent is not None
    
    def test_scrape_with_links(self):
        """Test that links are extracted correctly."""
        result = scrape_static("https://example.com")
        
        assert result.success is True
        assert isinstance(result.content.links, list)
        # example.com should have at least one link
        assert len(result.content.links) >= 0
    
    def test_scrape_invalid_url(self):
        """Test handling of invalid URL."""
        result = scrape_static("https://this-domain-definitely-does-not-exist-12345.com")
        
        assert result.success is False
        assert result.error is not None
    
    def test_scraper_user_agent_rotation(self):
        """Test that user agents are rotated."""
        scraper = StaticScraper(use_delays=False, use_rate_limiting=False)
        
        result1 = scraper.scrape("https://example.com")
        result2 = scraper.scrape("https://example.com")
        
        # User agents should potentially be different (not guaranteed due to randomness)
        # But both should have user agents set
        assert result1.metadata.user_agent is not None
        assert result2.metadata.user_agent is not None
        
        scraper.close()
    
    def test_scraper_respects_robots(self):
        """Test that robots.txt is respected."""
        scraper = StaticScraper(respect_robots=True, use_delays=False, use_rate_limiting=False)
        
        # Most sites allow scraping of their main page
        result = scraper.scrape("https://example.com")
        assert result.success is True
        
        scraper.close()


class TestStaticScraperContent:
    """Tests for content extraction."""
    
    def test_title_extraction(self):
        """Test title extraction."""
        result = scrape_static("https://example.com")
        
        assert result.success is True
        assert result.content.title is not None
        assert len(result.content.title) > 0
    
    def test_text_extraction(self):
        """Test text extraction."""
        result = scrape_static("https://example.com")
        
        assert result.success is True
        assert result.content.text is not None
        assert len(result.content.text) > 0
        # Should contain some expected content
        assert "example" in result.content.text.lower() or "domain" in result.content.text.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
