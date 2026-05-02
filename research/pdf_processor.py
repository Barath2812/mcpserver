"""
PDF Processor

Downloads open-access PDFs and extracts text content using PyMuPDF.
"""

import os
import re
import requests
import fitz  # PyMuPDF
from typing import Optional, Tuple
from urllib.parse import urlparse

import sys
sys.path.insert(0, 'd:\\mcp')

from config import PAPERS_DOWNLOAD_DIR


def download_pdf(
    pdf_url: str,
    save_dir: str = PAPERS_DOWNLOAD_DIR,
    filename: Optional[str] = None,
) -> Optional[str]:
    """
    Download a PDF from the given URL.

    Args:
        pdf_url: URL of the PDF to download
        save_dir: Directory to save the PDF (default: papers/)
        filename: Custom filename (auto-generated if not provided)

    Returns:
        Path to the downloaded PDF file, or None if download failed
    """
    if not pdf_url:
        return None

    # Ensure save directory exists
    os.makedirs(save_dir, exist_ok=True)

    # Generate filename if not provided
    if not filename:
        filename = _url_to_filename(pdf_url)

    filepath = os.path.join(save_dir, filename)

    # Skip if already downloaded
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        print(f"[=] PDF already exists: {filename}")
        return filepath

    try:
        print(f"[*] Downloading: {pdf_url}")
        response = requests.get(
            pdf_url,
            timeout=60,
            headers={
                "User-Agent": "Mozilla/5.0 (Research Assistant Bot; academic use)"
            },
            stream=True,
        )
        response.raise_for_status()

        # Verify it's actually a PDF
        content_type = response.headers.get("Content-Type", "")
        if "pdf" not in content_type and not pdf_url.endswith(".pdf"):
            # Check first bytes for PDF magic number
            first_bytes = response.content[:5]
            if first_bytes != b"%PDF-":
                print(f"[!] Not a PDF: {pdf_url} (Content-Type: {content_type})")
                return None

        with open(filepath, "wb") as f:
            f.write(response.content)

        file_size = os.path.getsize(filepath)
        print(f"[+] Downloaded: {filename} ({file_size / 1024:.1f} KB)")
        return filepath

    except requests.RequestException as e:
        print(f"[!] PDF download failed: {e}")
        return None
    except IOError as e:
        print(f"[!] Failed to save PDF: {e}")
        return None


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text content from a PDF file using PyMuPDF.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text as a string
    """
    if not pdf_path or not os.path.exists(pdf_path):
        return ""

    try:
        doc = fitz.open(pdf_path)
        text_parts = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(page_text)

        doc.close()

        full_text = "\n\n".join(text_parts)

        # Clean up the text
        full_text = _clean_extracted_text(full_text)

        return full_text

    except Exception as e:
        print(f"[!] PDF text extraction failed for {pdf_path}: {e}")
        return ""


def download_and_extract(
    pdf_url: str,
    save_dir: str = PAPERS_DOWNLOAD_DIR,
) -> Tuple[Optional[str], str]:
    """
    Download a PDF and extract its text in one step.

    Args:
        pdf_url: URL of the PDF
        save_dir: Directory to save the PDF

    Returns:
        Tuple of (local_path, extracted_text)
    """
    local_path = download_pdf(pdf_url, save_dir)

    if local_path:
        text = extract_text_from_pdf(local_path)
        return local_path, text

    return None, ""


def _url_to_filename(url: str) -> str:
    """Generate a safe filename from a URL."""
    parsed = urlparse(url)
    path = parsed.path.strip("/")

    # For arXiv URLs, use the paper ID
    if "arxiv" in parsed.hostname or "":
        # e.g., /pdf/2301.12345v1.pdf -> 2301.12345v1.pdf
        filename = path.split("/")[-1]
        if not filename.endswith(".pdf"):
            filename += ".pdf"
        return filename

    # Generic: use last path segment
    filename = path.replace("/", "_")
    if not filename.endswith(".pdf"):
        filename += ".pdf"

    # Sanitize filename
    filename = re.sub(r'[<>:"|?*]', '_', filename)
    return filename[:200]  # Limit length


def _clean_extracted_text(text: str) -> str:
    """Clean up extracted PDF text."""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove page headers/footers (common patterns)
    text = re.sub(r'\n\d+\n', '\n', text)
    # Fix hyphenated line breaks
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    return text.strip()
