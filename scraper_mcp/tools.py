"""
MCP (Model Context Protocol) tool definitions.
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
    Create and configure the MCP server with scraping tools.
    
    Returns:
        Configured MCP Server instance
    """
    server = Server("web-scraper")
    
    @server.list_tools()
    async def list_tools():
        """List available tools."""
        return [
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
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        """Handle tool calls."""
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
        server_name="web-scraper",
        server_version="1.0.0",
        capabilities=ServerCapabilities(
            tools={"listChanged": False}
        )
    )
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init_options)
