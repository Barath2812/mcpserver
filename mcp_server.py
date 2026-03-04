"""
MCP Server Entry Point

This script runs the MCP server for the web scraper.
Use this with Claude Desktop or other MCP-compatible clients.
"""
import asyncio
import sys
sys.path.insert(0, 'd:\\mcp')

from scraper_mcp.tools import run_mcp_server

if __name__ == "__main__":
    asyncio.run(run_mcp_server())
