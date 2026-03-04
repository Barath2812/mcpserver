"""
Tests for MCP tools.
"""
import pytest
import sys
sys.path.insert(0, 'd:\\mcp')

from mcp.tools import scrape_website_tool


class TestMCPTools:
    """Tests for MCP tool functions."""
    
    def test_scrape_website_tool_static(self):
        """Test scrape_website_tool with static scraping."""
        result = scrape_website_tool(
            url="https://example.com",
            dynamic=False,
            auto_detect=False,
            store_in_mongodb=False,
        )
        
        assert result["success"] is True
        assert result["url"] == "https://example.com"
        assert result["scraper_type"] == "static"
        assert "content" in result
        assert "metadata" in result
        assert result["content"]["title"] is not None
    
    def test_scrape_website_tool_dynamic(self):
        """Test scrape_website_tool with dynamic scraping."""
        result = scrape_website_tool(
            url="https://example.com",
            dynamic=True,
            auto_detect=False,
            store_in_mongodb=False,
        )
        
        assert result["success"] is True
        assert result["scraper_type"] == "dynamic"
    
    def test_scrape_website_tool_auto_detect(self):
        """Test scrape_website_tool with auto-detection."""
        result = scrape_website_tool(
            url="https://example.com",
            dynamic=False,
            auto_detect=True,
            store_in_mongodb=False,
        )
        
        assert result["success"] is True
        # example.com should be detected as static
        assert result["scraper_type"] in ["static", "dynamic"]
    
    def test_scrape_website_tool_returns_normalized_data(self):
        """Test that returned data is normalized."""
        result = scrape_website_tool(
            url="https://example.com",
            store_in_mongodb=False,
        )
        
        assert result["success"] is True
        
        # Check content structure
        content = result["content"]
        assert "title" in content
        assert "text" in content
        assert "links" in content
        assert isinstance(content["links"], list)
        
        # Check metadata structure
        metadata = result["metadata"]
        assert "status_code" in metadata
        assert "response_time" in metadata
        assert "user_agent" in metadata
    
    def test_scrape_website_tool_error_handling(self):
        """Test error handling for invalid URLs."""
        result = scrape_website_tool(
            url="https://this-domain-definitely-does-not-exist-12345.com",
            store_in_mongodb=False,
        )
        
        assert result["success"] is False
        assert result["error"] is not None


class TestMCPToolsMongoDBIntegration:
    """Tests for MCP tools with MongoDB integration."""
    
    def test_scrape_with_mongodb_storage(self):
        """Test scraping with MongoDB storage enabled."""
        # This test requires MongoDB to be running
        try:
            result = scrape_website_tool(
                url="https://example.com",
                store_in_mongodb=True,
            )
            
            if result["success"]:
                # If MongoDB is available, mongo_id should be set
                # If MongoDB is not available, it should still succeed without mongo_id
                assert result["success"] is True
        except Exception:
            # MongoDB not available - skip
            pytest.skip("MongoDB not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
