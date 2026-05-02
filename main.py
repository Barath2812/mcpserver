"""
AI Research Assistant & Web Data Extraction Platform

FastAPI server with MCP integration for web scraping + intelligent research pipeline.
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
from database.models import (
    ScrapeRequest, ScrapeResponse, ContentModel, MetadataModel,
    ResearchRequest, ResearchResponse,
)
from database.mongodb import get_mongodb_client
from scraper_mcp.tools import scrape_website_tool
from utils.exporter import export_to_csv, export_to_json
from research.pipeline import (
    search_all_sources,
    run_research_pipeline,
    run_deep_analysis_pipeline,
)
from research.summarizer import summarize_text
from research.research_analyzer import deep_analyze_paper


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("[*] Starting AI Research Assistant Server...")
    print(f"[-] MongoDB: Connecting...")
    
    try:
        client = get_mongodb_client()
        client.connect()
        print("[+] MongoDB: Connected")
    except Exception as e:
        print(f"[!] MongoDB: Connection failed - {e}")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    client = get_mongodb_client()
    client.disconnect()


# Create FastAPI app
app = FastAPI(
    title="AI Research Assistant & Web Data Extraction Platform",
    description="""
    A production-grade AI research assistant with MCP integration.
    
    ## Features
    
    ### 🧠 Research Assistant (NEW)
    - **arXiv Search**: Search 2M+ open-access papers
    - **Semantic Scholar**: AI-ranked paper search with citations
    - **PDF Processing**: Download & extract text from papers
    - **AI Summarization**: Generate intelligent summaries with Gemini
    - **Full Pipeline**: One-click research from query to summary
    
    ### 🌐 Web Scraper (Original)
    - **Static Scraping**: Requests + BeautifulSoup for HTML pages
    - **Dynamic Scraping**: Playwright for JavaScript-rendered pages
    - **Auto-Detection**: Automatically selects the appropriate scraper
    - **Anti-Bot Protection**: User-Agent rotation, rate limiting
    - **MongoDB Storage**: Stores all data with metadata
    - **MCP Integration**: Expose as tools for LLM invocation
    """,
    version="2.0.0",
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
        "name": "AI Research Assistant",
        "version": "2.0.0",
        "status": "running",
    }


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "name": "AI Research Assistant & Web Data Extraction Platform",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "scrape": "/scrape",
            "research_search": "/research/search",
            "research_run": "/research/run",
            "research_papers": "/research/papers",
            "research_stats": "/research/stats",
            "stats": "/stats",
            "recent": "/recent",
            "docs": "/docs",
        }
    }


# ===================================
# RESEARCH ENDPOINTS (NEW)
# ===================================

@app.post("/research/search")
async def research_search(request: ResearchRequest):
    """
    Search for academic papers across arXiv and Semantic Scholar.
    Returns paper metadata without downloading PDFs.
    """
    try:
        papers = search_all_sources(
            query=request.query,
            max_results=request.max_results,
            sources=request.sources,
        )
        return {
            "success": True,
            "query": request.query,
            "total": len(papers),
            "papers": papers,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research/run")
async def research_run(request: ResearchRequest):
    """
    Run the full research pipeline:
    Search → Download PDFs → Extract Text → AI Summarize → Store in MongoDB
    """
    try:
        result = run_research_pipeline(
            query=request.query,
            max_results=request.max_results,
            sources=request.sources,
            download_pdfs=request.download_pdfs,
            summarize=request.summarize,
            store=True,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/research/papers")
async def get_research_papers(
    topic: Optional[str] = Query(None, description="Filter by topic"),
    search: Optional[str] = Query(None, description="Search in titles/abstracts"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
):
    """Get stored research papers."""
    try:
        client = get_mongodb_client()
        if search:
            papers = client.search_papers_text(search, limit=limit)
        elif topic:
            papers = client.get_papers_by_topic(topic, limit=limit)
        else:
            papers = client.get_recent_papers(limit=limit)
        return {"success": True, "total": len(papers), "papers": papers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/research/paper/{paper_id}")
async def get_research_paper(paper_id: str):
    """Get a single research paper by ID."""
    try:
        client = get_mongodb_client()
        paper = client.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        return {"success": True, "paper": paper}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research/summarize")
async def summarize_paper_text(
    paper_id: Optional[str] = Query(None, description="Paper MongoDB ID to summarize"),
    text: Optional[str] = None,
):
    """Summarize a paper by ID or provided text."""
    try:
        if paper_id:
            client = get_mongodb_client()
            paper = client.get_paper_by_id(paper_id)
            if not paper:
                raise HTTPException(status_code=404, detail="Paper not found")
            text_to_summarize = paper.get("extracted_text") or paper.get("abstract", "")
            title = paper.get("title", "")
        elif text:
            text_to_summarize = text
            title = ""
        else:
            raise HTTPException(status_code=400, detail="Provide paper_id or text")

        summary = summarize_text(text_to_summarize, title=title)
        return {"success": True, "summary": summary}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/research/stats")
async def get_research_stats():
    """Get research statistics."""
    try:
        client = get_mongodb_client()
        return client.get_research_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================================
# ORIGINAL SCRAPER ENDPOINTS
# ===================================

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_website(request: ScrapeRequest):
    """Scrape a website and store the results in MongoDB."""
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
    """Scrape a website using GET request (convenience endpoint)."""
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
        client.db.command("ping")
        mongodb_status = "connected"
    except:
        mongodb_status = "disconnected"
    
    return {
        "status": "healthy",
        "mongodb": mongodb_status,
        "version": "2.0.0",
    }


# ===== RESEARCH INTELLIGENCE ENDPOINTS =====

@app.post("/research/analyze/{paper_id}")
async def analyze_paper(paper_id: str):
    """Deep-analyze a stored paper by its MongoDB ID."""
    try:
        client = get_mongodb_client()
        paper = client.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        text = paper.get("extracted_text") or paper.get("abstract", "")
        title = paper.get("title", "")
        
        result = deep_analyze_paper(text, title=title)
        return {"paper_id": paper_id, "title": title, "analysis": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research/literature-review")
async def generate_lit_review(
    topic: str = Query(..., description="Research topic"),
    max_papers: int = Query(15, ge=1, le=30, description="Papers to analyze"),
):
    """Generate a literature review on a topic."""
    try:
        result = run_deep_analysis_pipeline(
            query=topic,
            max_results=max_papers,
            analysis_type="literature_review",
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research/gaps")
async def find_gaps(
    topic: str = Query(..., description="Research topic"),
    max_papers: int = Query(15, ge=1, le=30, description="Papers to analyze"),
):
    """Find research gaps and opportunities for uniqueness."""
    try:
        result = run_deep_analysis_pipeline(
            query=topic,
            max_results=max_papers,
            analysis_type="gaps",
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research/ideas")
async def generate_ideas(
    topic: str = Query(..., description="Research topic"),
    user_goal: str = Query("", description="User's specific goal"),
    max_papers: int = Query(15, ge=1, le=30, description="Papers to analyze"),
):
    """Generate novel research ideas based on gaps and landscape."""
    try:
        result = run_deep_analysis_pipeline(
            query=topic,
            max_results=max_papers,
            user_goal=user_goal,
            analysis_type="ideas",
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research/advisor")
async def research_advisor(
    topic: str = Query(..., description="Research topic"),
    user_goal: str = Query("", description="User's specific goal"),
    max_papers: int = Query(15, ge=1, le=30, description="Papers to analyze"),
):
    """Full research advisory: landscape + gaps + uniqueness + ideas + action plan."""
    try:
        result = run_deep_analysis_pipeline(
            query=topic,
            max_results=max_papers,
            user_goal=user_goal,
            analysis_type="full",
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
