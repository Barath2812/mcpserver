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


# ===============================
# Research Paper Models
# ===============================

class PaperSummaryModel(BaseModel):
    """Model for AI-generated paper summary."""
    summary: str = ""
    key_findings: str = ""
    methodology: str = ""
    conclusions: str = ""
    raw_summary: str = ""


class PaperModel(BaseModel):
    """
    Model for a research paper document stored in MongoDB.
    """
    title: str
    authors: List[str] = Field(default_factory=list)
    abstract: str = ""
    source: str = ""  # "arxiv" or "semantic_scholar"
    pdf_url: Optional[str] = None
    local_path: Optional[str] = None
    extracted_text: str = ""
    summary: Optional[PaperSummaryModel] = None
    topic: str = ""
    year: Optional[int] = None
    citation_count: Optional[int] = None
    categories: List[str] = Field(default_factory=list)
    paper_id: str = ""
    arxiv_id: Optional[str] = None
    published: Optional[str] = None
    stored_at: Optional[str] = None


class ResearchRequest(BaseModel):
    """Request model for research search endpoint."""
    query: str
    max_results: int = 10
    sources: str = "both"  # "arxiv", "semantic_scholar", or "both"
    download_pdfs: bool = True
    summarize: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "query": "computer vision in healthcare",
                "max_results": 10,
                "sources": "both",
                "download_pdfs": True,
                "summarize": True,
            }
        }


class ResearchResponse(BaseModel):
    """Response model for research endpoints."""
    success: bool
    query: str = ""
    papers: List[dict] = Field(default_factory=list)
    stats: dict = Field(default_factory=dict)
    message: str = ""
