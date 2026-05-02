"""
MCP (Model Context Protocol) tool definitions.

Includes both web scraping tools (original) and AI research tools (new).
"""
from typing import Optional, Dict, Any
from dataclasses import asdict
import sys
sys.path.insert(0, 'd:\\mcp')

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json

from scraper.static_scraper import scrape_static, ScrapeResult
from scraper.dynamic_scraper import scrape_dynamic
from scraper.strategy_selector import auto_scrape
from database.mongodb import get_mongodb_client
from utils.normalizer import normalize_scraped_data
from research.pipeline import (
    search_all_sources,
    process_papers,
    summarize_papers,
    store_papers,
    run_research_pipeline,
    run_deep_analysis_pipeline,
)
from research.summarizer import summarize_text
from research.research_analyzer import (
    deep_analyze_paper,
    generate_literature_review,
    identify_research_gaps,
    generate_research_ideas,
    full_research_advisory,
)


def _result_to_dict(result: ScrapeResult) -> Dict[str, Any]:
    """Convert ScrapeResult to dictionary."""
    return {
        "url": result.url,
        "scraped_at": result.scraped_at,
        "scraper_type": result.scraper_type,
        "content": {
            "title": result.content.title,
            "text": result.content.text,
            "links": result.content.links,
        },
        "metadata": {
            "status_code": result.metadata.status_code,
            "response_time": result.metadata.response_time,
            "user_agent": result.metadata.user_agent,
        },
        "success": result.success,
        "error": result.error,
    }


def scrape_website_tool(
    url: str,
    dynamic: bool = False,
    auto_detect: bool = True,
    store_in_mongodb: bool = True,
) -> Dict[str, Any]:
    """
    Scrapes public web data ethically and stores it in MongoDB.
    
    This tool is exposed via MCP for LLM invocation.
    
    Args:
        url: The URL to scrape
        dynamic: Force use of dynamic scraper (Playwright)
        auto_detect: Automatically detect if JavaScript rendering is needed
        store_in_mongodb: Whether to store results in MongoDB
    
    Returns:
        Dictionary with scraped content and metadata
    """
    # Select scraping strategy
    if dynamic:
        result = scrape_dynamic(url)
    elif auto_detect:
        result = auto_scrape(url)
    else:
        result = scrape_static(url)
    
    # Convert to dictionary
    result_dict = _result_to_dict(result)
    
    # Normalize the data
    result_dict = normalize_scraped_data(result_dict)
    
    # Store in MongoDB
    mongo_id = None
    if store_in_mongodb and result.success:
        try:
            client = get_mongodb_client()
            
            # Prepare document for MongoDB (without success/error fields)
            mongo_doc = {
                "url": result_dict["url"],
                "scraped_at": result_dict["scraped_at"],
                "scraper_type": result_dict["scraper_type"],
                "content": result_dict["content"],
                "metadata": result_dict["metadata"],
            }
            
            mongo_id = client.insert_scraped_data(mongo_doc)
            
            # Log the scrape
            client.insert_log(url, success=True)
            
        except Exception as e:
            # Log failure but don't fail the scrape
            try:
                client = get_mongodb_client()
                client.insert_log(url, success=False, error=str(e))
            except:
                pass
    
    # Add MongoDB ID to result
    result_dict["mongo_id"] = mongo_id
    
    return result_dict


def create_mcp_server() -> Server:
    """
    Create and configure the MCP server with scraping + research tools.
    
    Returns:
        Configured MCP Server instance
    """
    server = Server("ai-research-assistant")
    
    @server.list_tools()
    async def list_tools():
        """List available tools."""
        return [
            # ===== ORIGINAL SCRAPER TOOLS =====
            Tool(
                name="scrape_website",
                description=(
                    "Scrapes public web data ethically and stores it in MongoDB. "
                    "Supports both static HTML pages and JavaScript-rendered pages. "
                    "Returns structured data including title, text content, and links."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL to scrape (must be publicly accessible)"
                        },
                        "dynamic": {
                            "type": "boolean",
                            "description": "Force use of Playwright for JavaScript-rendered pages",
                            "default": False
                        },
                        "auto_detect": {
                            "type": "boolean",
                            "description": "Automatically detect if JavaScript rendering is needed",
                            "default": True
                        },
                        "store_in_mongodb": {
                            "type": "boolean",
                            "description": "Whether to store results in MongoDB",
                            "default": True
                        }
                    },
                    "required": ["url"]
                }
            ),
            Tool(
                name="get_scrape_stats",
                description="Get statistics about scraping operations",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_recent_scrapes",
                description="Get recently scraped data from MongoDB",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 10
                        }
                    },
                    "required": []
                }
            ),

            # ===== NEW RESEARCH TOOLS =====
            Tool(
                name="search_papers",
                description=(
                    "Search for academic research papers across arXiv and Semantic Scholar. "
                    "Returns paper titles, authors, abstracts, and PDF links. "
                    "Use this to find relevant papers on any topic."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (e.g., 'computer vision healthcare', 'transformer attention mechanism')"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum results per source (default: 10)",
                            "default": 10
                        },
                        "sources": {
                            "type": "string",
                            "description": "Which sources to search: 'arxiv', 'semantic_scholar', or 'both'",
                            "default": "both",
                            "enum": ["arxiv", "semantic_scholar", "both"]
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="run_research",
                description=(
                    "Run the full AI research pipeline: search papers → download PDFs → "
                    "extract text → generate AI summaries → store in MongoDB. "
                    "This is the most powerful tool — it does everything in one call."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Research topic query"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum results per source",
                            "default": 5
                        },
                        "sources": {
                            "type": "string",
                            "description": "Sources: 'arxiv', 'semantic_scholar', or 'both'",
                            "default": "both"
                        },
                        "download_pdfs": {
                            "type": "boolean",
                            "description": "Whether to download and extract text from PDFs",
                            "default": True
                        },
                        "summarize": {
                            "type": "boolean",
                            "description": "Whether to generate AI summaries",
                            "default": True
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_research_papers",
                description="Get stored research papers from MongoDB, optionally filtered by topic",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Filter by topic (optional)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 20
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_research_stats",
                description="Get statistics about stored research papers",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),

            # ===== RESEARCH INTELLIGENCE TOOLS =====
            Tool(
                name="analyze_paper",
                description=(
                    "Deep-read and analyze a research paper. Extracts: overview, novel contributions, "
                    "methodology breakdown, key results, limitations, future work directions, "
                    "related work patterns, practical applications, and novelty assessment. "
                    "Use this to thoroughly understand a specific paper."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "paper_id": {
                            "type": "string",
                            "description": "MongoDB ID of a stored paper to analyze (from get_research_papers)"
                        },
                        "title": {
                            "type": "string",
                            "description": "Paper title to search and analyze (alternative to paper_id)"
                        },
                        "text": {
                            "type": "string",
                            "description": "Direct text/abstract to analyze (alternative to paper_id)"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="literature_review",
                description=(
                    "Generate a comprehensive literature review on a topic. Searches papers, "
                    "reads them, and produces: field overview, major research themes, timeline/evolution, "
                    "key authors, methodological trends, consensus vs. open debates, and research maturity. "
                    "Use this to understand what already exists in a research area."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Research topic for the literature review"
                        },
                        "max_papers": {
                            "type": "integer",
                            "description": "How many papers to analyze (default: 15)",
                            "default": 15
                        }
                    },
                    "required": ["topic"]
                }
            ),
            Tool(
                name="find_research_gaps",
                description=(
                    "Analyze existing research to find gaps, underexplored areas, common limitations, "
                    "contradictions between papers, missing perspectives, and concrete opportunities "
                    "for unique contributions. Use this to figure out how your research can be different "
                    "from what already exists."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Research topic to analyze for gaps"
                        },
                        "max_papers": {
                            "type": "integer",
                            "description": "How many papers to analyze (default: 15)",
                            "default": 15
                        }
                    },
                    "required": ["topic"]
                }
            ),
            Tool(
                name="generate_research_ideas",
                description=(
                    "Generate novel, feasible research project ideas based on the existing landscape "
                    "and identified gaps. Each idea includes: novelty justification, problem statement, "
                    "proposed approach, required resources, feasibility, timeline, and publication venues. "
                    "Use this to get concrete project directions that would be genuinely unique."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Research area for idea generation"
                        },
                        "user_goal": {
                            "type": "string",
                            "description": "What the researcher specifically wants to achieve (optional but recommended)"
                        },
                        "max_papers": {
                            "type": "integer",
                            "description": "How many papers to analyze (default: 15)",
                            "default": 15
                        }
                    },
                    "required": ["topic"]
                }
            ),
            Tool(
                name="research_advisor",
                description=(
                    "THE MOST POWERFUL TOOL — Complete research advisory. Searches papers, reads "
                    "them all, analyzes the landscape, and produces a comprehensive report with: "
                    "(1) Field overview & state-of-the-art, (2) What already exists (organized by themes), "
                    "(3) Research gaps & missing elements, (4) How YOUR work can be unique, "
                    "(5) Top 3 recommended directions with methodology, (6) Reading list, "
                    "(7) Venues & collaborators, (8) Risk assessment, (9) Step-by-step action plan. "
                    "Use this when the researcher wants full project/research support."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Research topic for the advisory"
                        },
                        "user_goal": {
                            "type": "string",
                            "description": "What the researcher wants to achieve (e.g., 'publish at CVPR', 'build a startup', 'PhD thesis topic')"
                        },
                        "max_papers": {
                            "type": "integer",
                            "description": "How many papers to analyze (default: 15)",
                            "default": 15
                        }
                    },
                    "required": ["topic"]
                }
            ),
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        """Handle tool calls."""
        # Original scraper tools
        if name == "scrape_website":
            url = arguments.get("url")
            dynamic = arguments.get("dynamic", False)
            auto_detect = arguments.get("auto_detect", True)
            store_in_mongodb = arguments.get("store_in_mongodb", True)
            
            result = scrape_website_tool(
                url=url,
                dynamic=dynamic,
                auto_detect=auto_detect,
                store_in_mongodb=store_in_mongodb
            )
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_scrape_stats":
            client = get_mongodb_client()
            stats = client.get_stats()
            return [TextContent(type="text", text=json.dumps(stats, indent=2))]
        
        elif name == "get_recent_scrapes":
            limit = arguments.get("limit", 10)
            client = get_mongodb_client()
            data = client.get_recent_scraped_data(limit=limit)
            return [TextContent(type="text", text=json.dumps(data, indent=2))]
        
        # New research tools
        elif name == "search_papers":
            query = arguments.get("query", "")
            max_results = arguments.get("max_results", 10)
            sources = arguments.get("sources", "both")
            
            papers = search_all_sources(query, max_results=max_results, sources=sources)
            
            # Clean for output
            result = {
                "query": query,
                "total": len(papers),
                "papers": papers,
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        
        elif name == "run_research":
            query = arguments.get("query", "")
            max_results = arguments.get("max_results", 5)
            sources = arguments.get("sources", "both")
            download_pdfs = arguments.get("download_pdfs", True)
            summarize = arguments.get("summarize", True)
            
            result = run_research_pipeline(
                query=query,
                max_results=max_results,
                sources=sources,
                download_pdfs=download_pdfs,
                summarize=summarize,
                store=True,
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        
        elif name == "get_research_papers":
            topic = arguments.get("topic")
            limit = arguments.get("limit", 20)
            client = get_mongodb_client()
            
            if topic:
                papers = client.get_papers_by_topic(topic, limit=limit)
            else:
                papers = client.get_recent_papers(limit=limit)
            
            return [TextContent(type="text", text=json.dumps(papers, indent=2, default=str))]
        
        elif name == "get_research_stats":
            client = get_mongodb_client()
            stats = client.get_research_stats()
            return [TextContent(type="text", text=json.dumps(stats, indent=2))]
        
        # Research Intelligence tools
        elif name == "analyze_paper":
            paper_id = arguments.get("paper_id")
            title = arguments.get("title", "")
            text = arguments.get("text", "")
            
            # If paper_id provided, fetch from MongoDB
            if paper_id:
                client = get_mongodb_client()
                paper = client.get_paper_by_id(paper_id)
                if not paper:
                    return [TextContent(type="text", text=json.dumps({"error": "Paper not found"}))]
                text = paper.get("extracted_text") or paper.get("abstract", "")
                title = paper.get("title", "")
            elif title and not text:
                # Search for the paper by title
                papers = search_all_sources(title, max_results=3)
                if papers:
                    text = papers[0].get("abstract", "")
                    title = papers[0].get("title", title)
            
            result = deep_analyze_paper(text, title=title)
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        
        elif name == "literature_review":
            topic = arguments.get("topic", "")
            max_papers = arguments.get("max_papers", 15)
            
            result = run_deep_analysis_pipeline(
                query=topic,
                max_results=max_papers,
                analysis_type="literature_review",
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        
        elif name == "find_research_gaps":
            topic = arguments.get("topic", "")
            max_papers = arguments.get("max_papers", 15)
            
            result = run_deep_analysis_pipeline(
                query=topic,
                max_results=max_papers,
                analysis_type="gaps",
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        
        elif name == "generate_research_ideas":
            topic = arguments.get("topic", "")
            user_goal = arguments.get("user_goal", "")
            max_papers = arguments.get("max_papers", 15)
            
            result = run_deep_analysis_pipeline(
                query=topic,
                max_results=max_papers,
                user_goal=user_goal,
                analysis_type="ideas",
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        
        elif name == "research_advisor":
            topic = arguments.get("topic", "")
            user_goal = arguments.get("user_goal", "")
            max_papers = arguments.get("max_papers", 15)
            
            result = run_deep_analysis_pipeline(
                query=topic,
                max_results=max_papers,
                user_goal=user_goal,
                analysis_type="full",
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    return server


async def run_mcp_server():
    """Run the MCP server with stdio transport."""
    from mcp.server.models import InitializationOptions
    from mcp.types import ServerCapabilities
    
    server = create_mcp_server()
    
    # Define initialization options with explicit capabilities
    init_options = InitializationOptions(
        server_name="ai-research-assistant",
        server_version="2.0.0",
        capabilities=ServerCapabilities(
            tools={"listChanged": False}
        )
    )
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init_options)
