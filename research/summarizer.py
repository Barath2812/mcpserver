"""
AI Summarizer

Uses Google Gemini API to generate intelligent summaries of research papers.
"""

import os
from typing import Optional, Dict, Any

import sys
sys.path.insert(0, 'd:\\mcp')

from config import GROQ_API_KEY
import time
from groq import Groq

def _call_groq_with_retry(prompt, max_retries=5, base_delay=4.0):
    """Call Groq API with robust exponential backoff to handle 429 Rate Limits."""
    client = Groq(api_key=GROQ_API_KEY)
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            # Add a small mandatory delay even on success to prevent spiking the RPM limit
            time.sleep(base_delay)
            return response.choices[0].message.content
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate limit" in error_str.lower():
                if attempt == max_retries - 1:
                    print(f"[!] Groq Rate limit hit and max retries ({max_retries}) exceeded.")
                    raise e
                
                # Exponential backoff with longer waits for 429s
                sleep_time = base_delay * (2 ** attempt)
                print(f"[*] Groq rate limit hit (429). Waiting {sleep_time}s before retry {attempt+1}/{max_retries}...")
                time.sleep(sleep_time)
            else:
                # Re-raise non-rate-limit errors
                print(f"[!] Groq API Error: {error_str}")
                raise e


def summarize_text(
    text: str,
    title: str = "",
    max_input_chars: int = 8000,
) -> Dict[str, Any]:
    """
    Summarize research paper text using Google Gemini.

    Args:
        text: The paper text to summarize
        title: Optional paper title for context
        max_input_chars: Maximum characters to send to the LLM

    Returns:
        Dict with keys: summary, key_findings, methodology, conclusions
    """
    if not text or not text.strip():
        return _empty_summary("No text provided for summarization.")

    if not GROQ_API_KEY:
        return _empty_summary("GROQ_API_KEY not configured. Set it in .env file.")

    # Truncate text to avoid token limits
    truncated_text = text[:max_input_chars]

    prompt = _build_prompt(truncated_text, title)

    try:
        response_text = _call_groq_with_retry(prompt)

        if response_text:
            return _parse_summary_response(response_text)
        else:
            return _empty_summary("LLM returned empty response.")

    except ImportError:
        return _empty_summary(
            "groq package not installed. Run: pip install groq"
        )
    except Exception as e:
        print(f"[!] Summarization failed: {e}")
        return _empty_summary(f"Summarization error: {str(e)}")


def summarize_abstract(abstract: str, title: str = "") -> str:
    """
    Generate a quick one-paragraph summary from just the abstract.
    Lighter-weight than full summarization.

    Args:
        abstract: Paper abstract
        title: Paper title

    Returns:
        Summary string
    """
    if not abstract:
        return ""

    if not GROQ_API_KEY:
        return abstract  # Fall back to the abstract itself

    try:
        prompt = (
            f"Summarize this research paper abstract in 2-3 clear sentences "
            f"that a graduate student would understand.\n\n"
            f"Title: {title}\n\n"
            f"Abstract: {abstract}"
        )

        response_text = _call_groq_with_retry(prompt, base_delay=3.0)
        return response_text.strip() if response_text else abstract

    except Exception as e:
        print(f"[!] Abstract summarization failed: {e}")
        return abstract


def _build_prompt(text: str, title: str) -> str:
    """Build the summarization prompt."""
    title_section = f"Paper Title: {title}\n\n" if title else ""

    return f"""You are an expert research paper analyst. Analyze the following academic paper and provide a structured summary.

{title_section}Paper Content:
{text}

Provide your analysis in this exact format:

## Summary
A clear 3-5 sentence overview of the paper's main contribution and findings.

## Key Findings
- Finding 1
- Finding 2
- Finding 3

## Methodology
Brief description of the methods and approach used.

## Conclusions
The main conclusions and their implications.

Keep the language clear and accessible. Focus on the most important aspects."""


def _parse_summary_response(response_text: str) -> Dict[str, Any]:
    """Parse the LLM response into structured sections."""
    sections = {
        "summary": "",
        "key_findings": "",
        "methodology": "",
        "conclusions": "",
        "raw_summary": response_text,
    }

    current_section = "summary"
    lines = response_text.split("\n")

    for line in lines:
        line_lower = line.lower().strip()

        if "## summary" in line_lower or "**summary**" in line_lower:
            current_section = "summary"
            continue
        elif "## key finding" in line_lower or "**key finding" in line_lower:
            current_section = "key_findings"
            continue
        elif "## methodolog" in line_lower or "**methodolog" in line_lower:
            current_section = "methodology"
            continue
        elif "## conclusion" in line_lower or "**conclusion" in line_lower:
            current_section = "conclusions"
            continue

        if current_section in sections:
            sections[current_section] += line + "\n"

    # Clean up each section
    for key in sections:
        if key != "raw_summary":
            sections[key] = sections[key].strip()

    return sections


def _empty_summary(reason: str) -> Dict[str, Any]:
    """Return an empty summary structure with a reason."""
    return {
        "summary": reason,
        "key_findings": "",
        "methodology": "",
        "conclusions": "",
        "raw_summary": reason,
    }
