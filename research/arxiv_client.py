"""
arXiv API Client

Searches arXiv for academic papers and extracts metadata + PDF links.
arXiv API docs: https://info.arxiv.org/help/api/index.html
"""

import requests
import xmltodict
from typing import List, Dict, Any, Optional
from datetime import datetime

import sys
sys.path.insert(0, 'd:\\mcp')

from config import ARXIV_API_URL, DEFAULT_MAX_PAPER_RESULTS


def search_arxiv(
    query: str,
    max_results: int = DEFAULT_MAX_PAPER_RESULTS,
    sort_by: str = "relevance",
    sort_order: str = "descending",
) -> List[Dict[str, Any]]:
    """
    Search arXiv for papers matching the query.

    Args:
        query: Search query string (e.g., "computer vision healthcare")
        max_results: Maximum number of results to return
        sort_by: Sort criterion - "relevance", "lastUpdatedDate", "submittedDate"
        sort_order: "ascending" or "descending"

    Returns:
        List of paper dicts with keys:
            title, authors, abstract, arxiv_id, pdf_url, published,
            updated, categories, source
    """
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": sort_order,
    }

    try:
        response = requests.get(ARXIV_API_URL, params=params, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[!] arXiv API request failed: {e}")
        return []

    return _parse_arxiv_response(response.text)


def _parse_arxiv_response(xml_text: str) -> List[Dict[str, Any]]:
    """Parse arXiv API XML response into structured paper data."""
    try:
        data = xmltodict.parse(xml_text)
    except Exception as e:
        print(f"[!] Failed to parse arXiv XML: {e}")
        return []

    feed = data.get("feed", {})
    entries = feed.get("entry", [])

    # Handle single result (xmltodict returns dict instead of list)
    if isinstance(entries, dict):
        entries = [entries]

    papers = []
    for entry in entries:
        paper = _parse_entry(entry)
        if paper:
            papers.append(paper)

    return papers


def _parse_entry(entry: Dict) -> Optional[Dict[str, Any]]:
    """Parse a single arXiv entry into a paper dict."""
    try:
        # Extract arxiv ID from the entry id URL
        entry_id = entry.get("id", "")
        arxiv_id = entry_id.split("/abs/")[-1] if "/abs/" in entry_id else entry_id

        # Extract title (remove newlines)
        title = entry.get("title", "").replace("\n", " ").strip()

        # Extract authors
        authors_data = entry.get("author", [])
        if isinstance(authors_data, dict):
            authors_data = [authors_data]
        authors = [a.get("name", "") for a in authors_data if isinstance(a, dict)]

        # Extract abstract
        abstract = entry.get("summary", "").replace("\n", " ").strip()

        # Build PDF URL from arxiv ID
        pdf_url = f"http://arxiv.org/pdf/{arxiv_id}.pdf"

        # Extract dates
        published = entry.get("published", "")
        updated = entry.get("updated", "")

        # Extract categories
        categories_data = entry.get("arxiv:primary_category", {})
        primary_category = ""
        if isinstance(categories_data, dict):
            primary_category = categories_data.get("@term", "")

        category_list = entry.get("category", [])
        if isinstance(category_list, dict):
            category_list = [category_list]
        categories = [c.get("@term", "") for c in category_list if isinstance(c, dict)]

        # Extract year from published date
        year = None
        if published:
            try:
                year = int(published[:4])
            except (ValueError, IndexError):
                pass

        return {
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "arxiv_id": arxiv_id,
            "pdf_url": pdf_url,
            "published": published,
            "updated": updated,
            "primary_category": primary_category,
            "categories": categories,
            "year": year,
            "source": "arxiv",
            "citation_count": None,  # arXiv doesn't provide this
            "paper_id": arxiv_id,
        }

    except Exception as e:
        print(f"[!] Failed to parse arXiv entry: {e}")
        return None
