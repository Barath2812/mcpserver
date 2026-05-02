"""
AI Research Assistant Module

Intelligent research pipeline integrating arXiv, Semantic Scholar,
PDF processing, and LLM-based summarization.
"""

from research.arxiv_client import search_arxiv
from research.semantic_scholar_client import search_semantic_scholar
from research.pdf_processor import download_pdf, extract_text_from_pdf
from research.summarizer import summarize_text
from research.pipeline import run_research_pipeline

__all__ = [
    "search_arxiv",
    "search_semantic_scholar",
    "download_pdf",
    "extract_text_from_pdf",
    "summarize_text",
    "run_research_pipeline",
]
