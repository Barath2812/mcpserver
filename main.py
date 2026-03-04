"""
AI-Driven Universal Web Data Extraction Platform

FastAPI server with MCP integration for web scraping.
"""
import asyncio
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os

import sys
sys.path.insert(0, 'd:\\mcp')

from config import SERVER_HOST, SERVER_PORT
from database.models import ScrapeRequest, ScrapeResponse, ContentModel, MetadataModel
from database.mongodb import get_mongodb_client
from scraper_mcp.tools import scrape_website_tool
from utils.exporter import export_to_csv, export_to_json


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("🚀 Starting Web Scraper MCP Server...")
    print(f"📊 MongoDB: Connecting...")
    
    try:
        client = get_mongodb_client()
        client.connect()
        print("✅ MongoDB: Connected")
    except Exception as e:
        print(f"⚠️ MongoDB: Connection failed - {e}")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    client = get_mongodb_client()
    client.disconnect()


# Create FastAPI app
app = FastAPI(
    title="AI-Driven Universal Web Data Extraction Platform",
    description="""
    A production-grade, MCP-enabled universal web scraping platform with MongoDB storage
    and advanced anti-bot (antigravity) mechanisms.
    
    ## Features
    
    - **Static Scraping**: Uses Requests + BeautifulSoup for traditional HTML pages
    - **Dynamic Scraping**: Uses Playwright for JavaScript-rendered pages
    - **Auto-Detection**: Automatically selects the appropriate scraper
    - **Anti-Bot Protection**: User-Agent rotation, rate limiting, robots.txt compliance
    - **MongoDB Storage**: Stores all scraped data with metadata
    - **MCP Integration**: Expose scraping as tools for LLM invocation
    
    ## Ethical Considerations
    
    - Respects robots.txt directives
    - Implements polite crawling with delays
    - Rate limits requests per domain
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def root():
    """Serve the frontend UI."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "name": "AI-Driven Universal Web Data Extraction Platform",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "scrape": "/scrape",
            "stats": "/stats",
            "recent": "/recent",
            "docs": "/docs",
        }
    }


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "name": "AI-Driven Universal Web Data Extraction Platform",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "scrape": "/scrape",
            "stats": "/stats",
            "recent": "/recent",
            "docs": "/docs",
        }
    }


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_website(request: ScrapeRequest):
    """
    Scrape a website and store the results in MongoDB.
    
    This endpoint is also exposed as an MCP tool for LLM invocation.
    """
    try:
        result = scrape_website_tool(
            url=request.url,
            dynamic=request.dynamic,
            auto_detect=request.auto_detect,
            store_in_mongodb=True,
        )
        
        return ScrapeResponse(
            success=result["success"],
            url=result["url"],
            scraped_at=result["scraped_at"],
            scraper_type=result["scraper_type"],
            content=ContentModel(**result["content"]),
            metadata=MetadataModel(**result["metadata"]),
            error=result.get("error"),
            mongo_id=result.get("mongo_id"),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scrape")
async def scrape_website_get(
    url: str = Query(..., description="URL to scrape"),
    dynamic: bool = Query(False, description="Force dynamic scraping"),
    auto_detect: bool = Query(True, description="Auto-detect scraper type"),
):
    """
    Scrape a website using GET request (convenience endpoint).
    """
    try:
        result = scrape_website_tool(
            url=url,
            dynamic=dynamic,
            auto_detect=auto_detect,
            store_in_mongodb=True,
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Get scraping statistics."""
    try:
        client = get_mongodb_client()
        return client.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recent")
async def get_recent_scrapes(
    limit: int = Query(10, ge=1, le=100, description="Number of results")
):
    """Get recently scraped data."""
    try:
        client = get_mongodb_client()
        return client.get_recent_scraped_data(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/logs")
async def get_logs(
    url: Optional[str] = Query(None, description="Filter by URL"),
    success_only: bool = Query(False, description="Only successful scrapes"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results"),
):
    """Get scrape logs."""
    try:
        client = get_mongodb_client()
        return client.get_logs(url=url, success_only=success_only, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export/json")
async def export_json(
    filepath: str = Query(..., description="Output file path"),
    limit: int = Query(100, description="Number of documents to export"),
):
    """Export scraped data to JSON file."""
    try:
        client = get_mongodb_client()
        data = client.get_recent_scraped_data(limit=limit)
        output_path = export_to_json(data, filepath)
        return {"success": True, "filepath": output_path, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export/csv")
async def export_csv(
    filepath: str = Query(..., description="Output file path"),
    limit: int = Query(100, description="Number of documents to export"),
):
    """Export scraped data to CSV file."""
    try:
        client = get_mongodb_client()
        data = client.get_recent_scraped_data(limit=limit)
        output_path = export_to_csv(data, filepath)
        return {"success": True, "filepath": output_path, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        client = get_mongodb_client()
        # Try a simple operation
        client.db.command("ping")
        mongodb_status = "connected"
    except:
        mongodb_status = "disconnected"
    
    return {
        "status": "healthy",
        "mongodb": mongodb_status,
    }


def run_server():
    """Run the FastAPI server."""
    uvicorn.run(
        "main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True,
    )


if __name__ == "__main__":
    run_server()
