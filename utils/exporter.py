"""
Data export utilities.
"""
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Union


def export_to_json(
    data: Union[Dict[str, Any], List[Dict[str, Any]]],
    filepath: Union[str, Path],
    indent: int = 2,
) -> str:
    """
    Export data to a JSON file.
    
    Args:
        data: Data to export (single document or list)
        filepath: Output file path
        indent: JSON indentation level
    
    Returns:
        Absolute path to the created file
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
    
    return str(filepath.absolute())


def export_to_csv(
    data: List[Dict[str, Any]],
    filepath: Union[str, Path],
    flatten: bool = True,
) -> str:
    """
    Export data to a CSV file.
    
    Args:
        data: List of documents to export
        filepath: Output file path
        flatten: Whether to flatten nested structures
    
    Returns:
        Absolute path to the created file
    """
    if not data:
        raise ValueError("Cannot export empty data to CSV")
    
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Flatten nested structures if requested
    if flatten:
        flattened_data = [_flatten_dict(doc) for doc in data]
    else:
        flattened_data = data
    
    # Get all unique keys
    all_keys = set()
    for doc in flattened_data:
        all_keys.update(doc.keys())
    
    # Sort keys for consistent output
    fieldnames = sorted(all_keys)
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        
        for doc in flattened_data:
            # Convert non-string values to strings
            row = {}
            for key, value in doc.items():
                if isinstance(value, (list, dict)):
                    row[key] = json.dumps(value, ensure_ascii=False)
                else:
                    row[key] = value
            writer.writerow(row)
    
    return str(filepath.absolute())


def _flatten_dict(
    d: Dict[str, Any],
    parent_key: str = "",
    sep: str = "_"
) -> Dict[str, Any]:
    """
    Flatten a nested dictionary.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator between keys
    
    Returns:
        Flattened dictionary
    """
    items = []
    
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep).items())
        elif isinstance(v, list):
            # Keep lists as JSON strings
            items.append((new_key, v))
        else:
            items.append((new_key, v))
    
    return dict(items)


def format_for_display(data: Dict[str, Any]) -> str:
    """
    Format scraped data for display.
    
    Args:
        data: Scraped data document
    
    Returns:
        Formatted string representation
    """
    lines = [
        f"URL: {data.get('url', 'N/A')}",
        f"Scraped At: {data.get('scraped_at', 'N/A')}",
        f"Scraper Type: {data.get('scraper_type', 'N/A')}",
        "",
        "--- Content ---",
    ]
    
    content = data.get("content", {})
    lines.append(f"Title: {content.get('title', 'N/A')}")
    
    text = content.get("text", "")
    if len(text) > 500:
        text = text[:500] + "..."
    lines.append(f"Text: {text}")
    
    links = content.get("links", [])
    lines.append(f"Links ({len(links)} total):")
    for link in links[:5]:
        lines.append(f"  - {link}")
    if len(links) > 5:
        lines.append(f"  ... and {len(links) - 5} more")
    
    lines.append("")
    lines.append("--- Metadata ---")
    
    metadata = data.get("metadata", {})
    lines.append(f"Status Code: {metadata.get('status_code', 'N/A')}")
    lines.append(f"Response Time: {metadata.get('response_time', 'N/A')}s")
    lines.append(f"User Agent: {metadata.get('user_agent', 'N/A')[:50]}...")
    
    return "\n".join(lines)
