"""
Data normalization utilities.
"""
import re
import html
from typing import Dict, Any


def normalize_text(text: str, max_length: int = 50000) -> str:
    """
    Normalize and clean text content.
    
    Args:
        text: Raw text to normalize
        max_length: Maximum text length
    
    Returns:
        Cleaned and normalized text
    """
    if not text:
        return ""
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove excessive punctuation
    text = re.sub(r'([.,!?;:]){3,}', r'\1\1', text)
    
    # Trim
    text = text.strip()
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text


def normalize_url(url: str) -> str:
    """
    Normalize a URL.
    
    Args:
        url: URL to normalize
    
    Returns:
        Normalized URL
    """
    if not url:
        return ""
    
    # Strip whitespace
    url = url.strip()
    
    # Remove trailing slashes (except for root URLs)
    if url.count('/') > 3:
        url = url.rstrip('/')
    
    return url


def normalize_links(links: list[str]) -> list[str]:
    """
    Normalize and deduplicate a list of URLs.
    
    Args:
        links: List of URLs
    
    Returns:
        Normalized and deduplicated list
    """
    normalized = []
    seen = set()
    
    for link in links:
        norm_link = normalize_url(link)
        if norm_link and norm_link not in seen:
            seen.add(norm_link)
            normalized.append(norm_link)
    
    return normalized


def normalize_scraped_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a scraped data document.
    
    Args:
        data: Raw scraped data
    
    Returns:
        Normalized data
    """
    normalized = data.copy()
    
    # Normalize URL
    if "url" in normalized:
        normalized["url"] = normalize_url(normalized["url"])
    
    # Normalize content
    if "content" in normalized:
        content = normalized["content"]
        
        if "title" in content:
            content["title"] = normalize_text(content["title"], max_length=500)
        
        if "text" in content:
            content["text"] = normalize_text(content["text"])
        
        if "links" in content:
            content["links"] = normalize_links(content["links"])
    
    return normalized
