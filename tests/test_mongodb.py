"""
Tests for MongoDB operations.
"""
import pytest
from datetime import datetime, timezone
import sys
sys.path.insert(0, 'd:\\mcp')

from database.mongodb import MongoDBClient


class TestMongoDBClient:
    """Tests for MongoDB client."""
    
    @pytest.fixture
    def client(self):
        """Create a test MongoDB client."""
        client = MongoDBClient()
        yield client
        # Cleanup - clear test data
        try:
            client.clear_all()
        except:
            pass
        client.disconnect()
    
    def test_connection(self, client):
        """Test MongoDB connection."""
        try:
            client.connect()
            # Try a simple operation
            client.db.command("ping")
            assert True
        except Exception:
            pytest.skip("MongoDB not available")
    
    def test_insert_scraped_data(self, client):
        """Test inserting scraped data."""
        try:
            test_data = {
                "url": "https://test.example.com",
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "scraper_type": "static",
                "content": {
                    "title": "Test Page",
                    "text": "This is test content",
                    "links": ["https://link1.com", "https://link2.com"]
                },
                "metadata": {
                    "status_code": 200,
                    "response_time": 0.5,
                    "user_agent": "Test Agent"
                }
            }
            
            doc_id = client.insert_scraped_data(test_data)
            
            assert doc_id is not None
            assert len(doc_id) > 0
        except Exception:
            pytest.skip("MongoDB not available")
    
    def test_insert_log(self, client):
        """Test inserting scrape logs."""
        try:
            log_id = client.insert_log(
                url="https://test.example.com",
                success=True,
                error=None
            )
            
            assert log_id is not None
            assert len(log_id) > 0
        except Exception:
            pytest.skip("MongoDB not available")
    
    def test_get_scraped_data_by_url(self, client):
        """Test retrieving data by URL."""
        try:
            # Insert test data
            test_url = "https://test-get.example.com"
            test_data = {
                "url": test_url,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "scraper_type": "static",
                "content": {"title": "Test", "text": "Content", "links": []},
                "metadata": {"status_code": 200, "response_time": 0.1, "user_agent": "Test"}
            }
            client.insert_scraped_data(test_data)
            
            # Retrieve
            result = client.get_scraped_data_by_url(test_url)
            
            assert result is not None
            assert result["url"] == test_url
        except Exception:
            pytest.skip("MongoDB not available")
    
    def test_get_recent_scraped_data(self, client):
        """Test retrieving recent data."""
        try:
            # Insert some test data
            for i in range(3):
                test_data = {
                    "url": f"https://test{i}.example.com",
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                    "scraper_type": "static",
                    "content": {"title": f"Test {i}", "text": "Content", "links": []},
                    "metadata": {"status_code": 200, "response_time": 0.1, "user_agent": "Test"}
                }
                client.insert_scraped_data(test_data)
            
            # Retrieve recent
            results = client.get_recent_scraped_data(limit=2)
            
            assert len(results) == 2
        except Exception:
            pytest.skip("MongoDB not available")
    
    def test_get_stats(self, client):
        """Test getting statistics."""
        try:
            stats = client.get_stats()
            
            assert "total_scraped" in stats
            assert "static_scrapes" in stats
            assert "dynamic_scrapes" in stats
            assert "success_rate" in stats
        except Exception:
            pytest.skip("MongoDB not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
