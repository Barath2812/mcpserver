"""
Research Pipeline Orchestrator

Combines arXiv + Semantic Scholar search, PDF download, text extraction,
and AI summarization into a single intelligent pipeline.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from difflib import SequenceMatcher

import sys
sys.path.insert(0, 'd:\\mcp')

from research.arxiv_client import search_arxiv
from research.semantic_scholar_client import search_semantic_scholar
from research.pdf_processor import download_and_extract
from research.summarizer import summarize_text, summarize_abstract
from database.mongodb import get_mongodb_client
from config import DEFAULT_MAX_PAPER_RESULTS


def search_all_sources(
    query: str,
    max_results: int = DEFAULT_MAX_PAPER_RESULTS,
    sources: str = "both",
) -> List[Dict[str, Any]]:
    """
    Search for papers across multiple sources.

    Args:
        query: Search query string
        max_results: Max results per source
        sources: "arxiv", "semantic_scholar", or "both"

    Returns:
        Deduplicated list of paper dicts
    """
    all_papers = []

    if sources in ("arxiv", "both"):
        print(f"[*] Searching arXiv for: '{query}'...")
        arxiv_results = search_arxiv(query, max_results=max_results)
        print(f"  [+] Found {len(arxiv_results)} papers on arXiv")
        all_papers.extend(arxiv_results)

    if sources in ("semantic_scholar", "both"):
        print(f"[*] Searching Semantic Scholar for: '{query}'...")
        ss_results = search_semantic_scholar(query, limit=max_results)
        print(f"  [+] Found {len(ss_results)} papers on Semantic Scholar")
        all_papers.extend(ss_results)

    # Deduplicate
    unique_papers = _deduplicate_papers(all_papers)
    print(f"[*] Total unique papers: {len(unique_papers)}")

    return unique_papers


def process_papers(
    papers: List[Dict[str, Any]],
    download_pdfs: bool = True,
    extract_text: bool = True,
) -> List[Dict[str, Any]]:
    """
    Process papers: download PDFs and extract text.

    Args:
        papers: List of paper dicts from search
        download_pdfs: Whether to download PDFs
        extract_text: Whether to extract text from PDFs

    Returns:
        Updated papers with local_path and extracted_text
    """
    processed = []

    for i, paper in enumerate(papers):
        print(f"[*] Processing [{i+1}/{len(papers)}]: {paper['title'][:60]}...")

        paper = dict(paper)  # Don't mutate original

        if download_pdfs and paper.get("pdf_url"):
            local_path, extracted = download_and_extract(paper["pdf_url"])
            paper["local_path"] = local_path
            if extract_text and extracted:
                paper["extracted_text"] = extracted
                print(f"  [+] Extracted {len(extracted)} chars of text")
            else:
                paper["extracted_text"] = ""
        else:
            paper["local_path"] = None
            paper["extracted_text"] = ""

        processed.append(paper)

    return processed


def summarize_papers(
    papers: List[Dict[str, Any]],
    full_summary: bool = False,
) -> List[Dict[str, Any]]:
    """
    Add AI summaries to papers.

    Args:
        papers: List of paper dicts (should have extracted_text or abstract)
        full_summary: If True, summarize full text; if False, summarize abstract only

    Returns:
        Papers with summary field added
    """
    summarized = []

    for i, paper in enumerate(papers):
        paper = dict(paper)
        title = paper.get("title", "")
        print(f"[*] Summarizing [{i+1}/{len(papers)}]: {title[:60]}...")

        if full_summary and paper.get("extracted_text"):
            # Full paper summarization
            summary_result = summarize_text(
                paper["extracted_text"],
                title=title,
            )
            paper["summary"] = summary_result
        elif paper.get("abstract"):
            # Quick abstract summarization
            quick_summary = summarize_abstract(paper["abstract"], title=title)
            paper["summary"] = {
                "summary": quick_summary,
                "key_findings": "",
                "methodology": "",
                "conclusions": "",
                "raw_summary": quick_summary,
            }
        else:
            paper["summary"] = {
                "summary": "No abstract or text available for summarization.",
                "key_findings": "",
                "methodology": "",
                "conclusions": "",
                "raw_summary": "",
            }

        summarized.append(paper)

    return summarized


def store_papers(
    papers: List[Dict[str, Any]],
    topic: str,
) -> List[str]:
    """
    Store processed papers in MongoDB.

    Args:
        papers: List of processed paper dicts
        topic: The search topic/query

    Returns:
        List of MongoDB document IDs
    """
    client = get_mongodb_client()
    stored_ids = []

    for paper in papers:
        doc = {
            "title": paper.get("title", ""),
            "authors": paper.get("authors", []),
            "abstract": paper.get("abstract", ""),
            "source": paper.get("source", ""),
            "pdf_url": paper.get("pdf_url"),
            "local_path": paper.get("local_path"),
            "extracted_text": paper.get("extracted_text", ""),
            "summary": paper.get("summary", {}),
            "topic": topic,
            "year": paper.get("year"),
            "citation_count": paper.get("citation_count"),
            "categories": paper.get("categories", []),
            "paper_id": paper.get("paper_id", ""),
            "arxiv_id": paper.get("arxiv_id"),
            "published": paper.get("published"),
            "stored_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            mongo_id = client.insert_paper(doc)
            stored_ids.append(mongo_id)
        except Exception as e:
            print(f"[!] Failed to store paper '{paper.get('title', '')}': {e}")

    print(f"[+] Stored {len(stored_ids)} papers in MongoDB")
    return stored_ids


def run_research_pipeline(
    query: str,
    max_results: int = DEFAULT_MAX_PAPER_RESULTS,
    sources: str = "both",
    download_pdfs: bool = True,
    summarize: bool = True,
    store: bool = True,
) -> Dict[str, Any]:
    """
    Run the full research pipeline.

    Flow: Search -> Deduplicate -> Download PDFs -> Extract Text -> Summarize -> Store

    Args:
        query: Search query
        max_results: Max results per source
        sources: "arxiv", "semantic_scholar", or "both"
        download_pdfs: Whether to download PDFs
        summarize: Whether to generate AI summaries
        store: Whether to store results in MongoDB

    Returns:
        Dict with pipeline results and stats
    """
    print(f"\n{'='*60}")
    print(f"[*] AI Research Pipeline: '{query}'")
    print(f"{'='*60}\n")

    start_time = datetime.now(timezone.utc)

    # Step 1: Search
    papers = search_all_sources(query, max_results=max_results, sources=sources)

    if not papers:
        return {
            "success": False,
            "query": query,
            "message": "No papers found for the given query.",
            "papers": [],
            "stats": {"total": 0},
        }

    # Step 2: Process (download + extract)
    if download_pdfs:
        papers = process_papers(papers, download_pdfs=True, extract_text=True)

    # Step 3: Summarize
    if summarize:
        papers = summarize_papers(papers, full_summary=download_pdfs)

    # Step 4: Store in MongoDB
    stored_ids = []
    if store:
        try:
            stored_ids = store_papers(papers, topic=query)
        except Exception as e:
            print(f"[!] MongoDB storage failed: {e}")

    # Build stats
    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()

    arxiv_count = sum(1 for p in papers if p.get("source") == "arxiv")
    ss_count = sum(1 for p in papers if p.get("source") == "semantic_scholar")
    pdf_count = sum(1 for p in papers if p.get("local_path"))
    summarized_count = sum(1 for p in papers if p.get("summary", {}).get("summary"))

    # Clean papers for response (remove large text fields)
    response_papers = []
    for p in papers:
        clean_paper = {k: v for k, v in p.items() if k != "extracted_text"}
        # Include a preview of extracted text
        if p.get("extracted_text"):
            clean_paper["text_preview"] = p["extracted_text"][:500] + "..."
            clean_paper["text_length"] = len(p["extracted_text"])
        response_papers.append(clean_paper)

    print(f"\n{'='*60}")
    print(f"[+] Pipeline complete in {duration:.1f}s")
    print(f"   Papers: {len(papers)} | PDFs: {pdf_count} | Summarized: {summarized_count}")
    print(f"{'='*60}\n")

    return {
        "success": True,
        "query": query,
        "papers": response_papers,
        "stats": {
            "total": len(papers),
            "arxiv": arxiv_count,
            "semantic_scholar": ss_count,
            "pdfs_downloaded": pdf_count,
            "summarized": summarized_count,
            "stored": len(stored_ids),
            "duration_seconds": round(duration, 2),
        },
    }


def _deduplicate_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate papers based on title similarity and arXiv ID matching.
    Prefers Semantic Scholar entries (more metadata) over arXiv.
    """
    unique = []
    seen_arxiv_ids = set()
    seen_titles = []

    # Sort: Semantic Scholar first (richer metadata), then arXiv
    sorted_papers = sorted(papers, key=lambda p: p.get("source", "") != "semantic_scholar")

    for paper in sorted_papers:
        # Check arXiv ID match
        arxiv_id = paper.get("arxiv_id")
        if arxiv_id and arxiv_id in seen_arxiv_ids:
            continue

        # Check title similarity
        title = paper.get("title", "").lower().strip()
        is_duplicate = False
        for seen_title in seen_titles:
            similarity = SequenceMatcher(None, title, seen_title).ratio()
            if similarity > 0.85:
                is_duplicate = True
                break

        if is_duplicate:
            continue

        unique.append(paper)
        seen_titles.append(title)
        if arxiv_id:
            seen_arxiv_ids.add(arxiv_id)

    return unique


def run_deep_analysis_pipeline(
    query: str,
    max_results: int = 10,
    sources: str = "both",
    user_goal: str = "",
    analysis_type: str = "full",
) -> Dict[str, Any]:
    """
    Run the deep research analysis pipeline.

    This is the brain behind the research_advisor MCP tool.

    Flow: Search -> Download -> Extract -> Deep Analyze -> Gaps -> Ideas -> Advisory

    Args:
        query: Research topic
        max_results: Max papers per source
        sources: "arxiv", "semantic_scholar", or "both"
        user_goal: What the user wants to achieve
        analysis_type: "literature_review", "gaps", "ideas", or "full"

    Returns:
        Complete analysis results
    """
    from research.research_analyzer import (
        generate_literature_review,
        identify_research_gaps,
        generate_research_ideas,
        full_research_advisory,
    )

    print(f"\n{'='*60}")
    print(f"[*] Deep Research Analysis: '{query}'")
    print(f"   Analysis type: {analysis_type}")
    print(f"{'='*60}\n")

    start_time = datetime.now(timezone.utc)

    # Step 1: Search for papers
    papers = search_all_sources(query, max_results=max_results, sources=sources)

    if not papers:
        return {
            "success": False,
            "query": query,
            "message": "No papers found.",
            "papers": [],
        }

    # Step 2: Download & extract text from PDFs
    print(f"\n[*] Downloading and extracting text from {len(papers)} papers...")
    papers = process_papers(papers, download_pdfs=True, extract_text=True)

    # Step 3: Summarize papers (quick abstract summaries for context)
    papers = summarize_papers(papers, full_summary=False)

    # Step 4: Run the requested analysis
    result = {
        "success": True,
        "query": query,
        "user_goal": user_goal,
        "analysis_type": analysis_type,
        "papers_analyzed": len(papers),
    }

    if analysis_type == "literature_review":
        print("\n[*] Generating literature review...")
        review = generate_literature_review(papers, query)
        result["literature_review"] = review

    elif analysis_type == "gaps":
        print("\n[*] Identifying research gaps...")
        gaps = identify_research_gaps(papers, query)
        result["research_gaps"] = gaps

    elif analysis_type == "ideas":
        print("\n[*] Generating research ideas...")
        gaps = identify_research_gaps(papers, query)
        ideas = generate_research_ideas(
            papers, query,
            gaps_analysis=gaps.get("gaps_analysis", ""),
            user_goal=user_goal,
        )
        result["research_gaps"] = gaps
        result["research_ideas"] = ideas

    else:  # "full" — complete advisory
        print("\n[*] Running full research advisory...")
        advisory = full_research_advisory(papers, query, user_goal=user_goal)
        result["advisory_report"] = advisory

    # Store papers if not already stored
    try:
        stored_ids = store_papers(papers, topic=query)
        result["papers_stored"] = len(stored_ids)
    except Exception as e:
        print(f"[!] Storage failed: {e}")
        result["papers_stored"] = 0

    # Add paper summaries for context
    result["papers"] = [
        {
            "title": p.get("title", ""),
            "authors": p.get("authors", []),
            "year": p.get("year"),
            "source": p.get("source", ""),
            "abstract": p.get("abstract", "")[:300],
            "citation_count": p.get("citation_count"),
            "pdf_url": p.get("pdf_url"),
        }
        for p in papers
    ]

    end_time = datetime.now(timezone.utc)
    result["duration_seconds"] = round((end_time - start_time).total_seconds(), 2)

    print(f"\n[+] Deep analysis complete in {result['duration_seconds']}s")
    return result

