"""
Pydantic models for database schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ContentModel(BaseModel):
    """Model for scraped content."""
    title: str = ""
    text: str = ""
    links: List[str] = Field(default_factory=list)


class MetadataModel(BaseModel):
    """Model for scrape metadata."""
    status_code: int = 0
    response_time: float = 0.0
    user_agent: str = ""


class ScrapedDataModel(BaseModel):
    """
    Model for scraped data document.
    
    Matches the MongoDB schema:
    {
        "_id": ObjectId,
        "url": "string",
        "scraped_at": "ISO timestamp",
        "scraper_type": "static | dynamic",
        "content": {
            "title": "string",
            "text": "string",
            "links": ["string"]
        },
        "metadata": {
            "status_code": number,
            "response_time": number,
            "user_agent": "string"
        }
    }
    """
    url: str
    scraped_at: str
    scraper_type: str  # "static" or "dynamic"
    content: ContentModel
    metadata: MetadataModel
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com",
                "scraped_at": "2024-01-15T10:30:00Z",
                "scraper_type": "static",
                "content": {
                    "title": "Example Domain",
                    "text": "This domain is for use in illustrative examples...",
                    "links": ["https://www.iana.org/domains/example"]
                },
                "metadata": {
                    "status_code": 200,
                    "response_time": 0.523,
                    "user_agent": "Mozilla/5.0..."
                }
            }
        }


class ScrapeLogModel(BaseModel):
    """
    Model for scrape log document.
    
    Matches the MongoDB schema:
    {
        "url": "string",
        "timestamp": "ISO timestamp",
        "success": boolean,
        "error": "string | null"
    }
    """
    url: str
    timestamp: str
    success: bool
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com",
                "timestamp": "2024-01-15T10:30:00Z",
                "success": True,
                "error": None
            }
        }


class ScrapeRequest(BaseModel):
    """Request model for scrape endpoint."""
    url: str
    dynamic: bool = False
    auto_detect: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com",
                "dynamic": False,
                "auto_detect": True
            }
        }


class ScrapeResponse(BaseModel):
    """Response model for scrape endpoint."""
    success: bool
    url: str
    scraped_at: str
    scraper_type: str
    content: ContentModel
    metadata: MetadataModel
    error: Optional[str] = None
    mongo_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "url": "https://example.com",
                "scraped_at": "2024-01-15T10:30:00Z",
                "scraper_type": "static",
                "content": {
                    "title": "Example Domain",
                    "text": "This domain is for use in illustrative examples...",
                    "links": ["https://www.iana.org/domains/example"]
                },
                "metadata": {
                    "status_code": 200,
                    "response_time": 0.523,
                    "user_agent": "Mozilla/5.0..."
                },
                "error": None,
                "mongo_id": "65a5b2c3d4e5f6a7b8c9d0e1"
            }
        }
