"""
Semantic Scholar API Client

Searches Semantic Scholar for academic papers with AI-based relevance ranking.
API docs: https://api.semanticscholar.org/api-docs/
"""

import requests
from typing import List, Dict, Any, Optional
import time

import sys
sys.path.insert(0, 'd:\\mcp')

from config import SEMANTIC_SCHOLAR_API_URL, DEFAULT_MAX_PAPER_RESULTS


def search_semantic_scholar(
    query: str,
    limit: int = DEFAULT_MAX_PAPER_RESULTS,
    year: Optional[str] = None,
    fields_of_study: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Search Semantic Scholar for papers matching the query.

    Args:
        query: Search query string
        limit: Maximum number of results
        year: Filter by year range (e.g., "2020-2024" or "2023-")
        fields_of_study: Filter by fields (e.g., ["Computer Science"])

    Returns:
        List of paper dicts with keys:
            title, authors, abstract, url, pdf_url, year,
            citation_count, paper_id, source
    """
    fields = "title,abstract,authors,url,openAccessPdf,year,citationCount,externalIds,fieldsOfStudy"

    params = {
        "query": query,
        "limit": min(limit, 100),  # API max is 100
        "fields": fields,
    }

    if year:
        params["year"] = year
    if fields_of_study:
        params["fieldsOfStudy"] = ",".join(fields_of_study)

    try:
        response = requests.get(
            f"{SEMANTIC_SCHOLAR_API_URL}/paper/search",
            params=params,
            timeout=30,
        )

        if response.status_code == 429:
            # Rate limited — wait and retry once
            print("[~] Semantic Scholar rate limited, waiting 3s...")
            time.sleep(3)
            response = requests.get(
                f"{SEMANTIC_SCHOLAR_API_URL}/paper/search",
                params=params,
                timeout=30,
            )

        response.raise_for_status()
        data = response.json()

    except requests.RequestException as e:
        print(f"[!] Semantic Scholar API request failed: {e}")
        return []

    return _parse_results(data)


def _parse_results(data: Dict) -> List[Dict[str, Any]]:
    """Parse Semantic Scholar API response into structured paper data."""
    papers = []
    results = data.get("data", [])

    for item in results:
        paper = _parse_paper(item)
        if paper:
            papers.append(paper)

    return papers


def _parse_paper(item: Dict) -> Optional[Dict[str, Any]]:
    """Parse a single Semantic Scholar result into a paper dict."""
    try:
        title = item.get("title", "")
        if not title:
            return None

        # Extract authors
        authors_data = item.get("authors", [])
        authors = [a.get("name", "") for a in authors_data if a.get("name")]

        # Extract abstract
        abstract = item.get("abstract") or ""

        # Extract PDF URL (only open access)
        open_access_pdf = item.get("openAccessPdf")
        pdf_url = None
        if open_access_pdf and isinstance(open_access_pdf, dict):
            pdf_url = open_access_pdf.get("url")

        # Extract external IDs
        external_ids = item.get("externalIds") or {}
        arxiv_id = external_ids.get("ArXiv")
        doi = external_ids.get("DOI")

        # If no PDF from Semantic Scholar but has arXiv ID, build arXiv PDF URL
        if not pdf_url and arxiv_id:
            pdf_url = f"http://arxiv.org/pdf/{arxiv_id}.pdf"

        # Extract fields of study
        fields = item.get("fieldsOfStudy") or []

        # Paper ID
        paper_id = item.get("paperId", "")

        return {
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "url": item.get("url", ""),
            "pdf_url": pdf_url,
            "year": item.get("year"),
            "citation_count": item.get("citationCount", 0),
            "paper_id": paper_id,
            "arxiv_id": arxiv_id,
            "doi": doi,
            "categories": fields,
            "source": "semantic_scholar",
            "published": None,
            "updated": None,
            "primary_category": fields[0] if fields else "",
        }

    except Exception as e:
        print(f"[!] Failed to parse Semantic Scholar paper: {e}")
        return None
