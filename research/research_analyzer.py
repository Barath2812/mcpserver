"""
Research Intelligence Analyzer

Uses Google Gemini to perform deep analysis of research papers:
- Deep paper analysis (contributions, limitations, future work)
- Literature review synthesis
- Research gap identification
- Novel research idea generation
- Full research advisory

These functions power the MCP tools that Claude uses for research support.
"""

import os
from typing import List, Dict, Any, Optional

import sys
sys.path.insert(0, 'd:\\mcp')

from config import GROQ_API_KEY
import time
from groq import Groq

def _call_groq_with_retry(prompt, model_name="llama-3.3-70b-versatile", max_retries=5, base_delay=4.0):
    """Call Groq API with robust exponential backoff to handle 429 Rate Limits."""
    client = Groq(api_key=GROQ_API_KEY)
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model_name,
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


def deep_analyze_paper(
    text: str,
    title: str = "",
    abstract: str = "",
    max_input_chars: int = 12000,
) -> Dict[str, Any]:
    """
    Deep-read a research paper and extract structured analysis.

    Returns:
        Dict with: overview, contributions, methodology, key_results,
                   limitations, future_work, related_work_patterns,
                   practical_applications, novelty_assessment
    """
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY not configured. Set it in .env file.", "raw": ""}

    content = text[:max_input_chars] if text else abstract
    if not content:
        return {"error": "No text or abstract provided for analysis.", "raw": ""}

    title_ctx = f"Paper Title: {title}\n\n" if title else ""

    prompt = f"""You are a senior research scientist. Perform a deep, thorough analysis of this research paper.

{title_ctx}Paper Content:
{content}

Provide your analysis in this EXACT structure (use these exact headings):

## Overview
A comprehensive summary of what this paper is about and why it matters (4-6 sentences).

## Novel Contributions
What NEW things does this paper bring to the field? List each specific contribution.
- Contribution 1: description
- Contribution 2: description

## Methodology
Detailed breakdown of the research methodology:
- Approach: overall approach taken
- Data: datasets, data collection methods
- Techniques: specific algorithms, models, or methods used
- Evaluation: how results were evaluated

## Key Results
The most important quantitative and qualitative results:
- Result 1
- Result 2

## Limitations
Critical limitations and weaknesses of this work:
- Limitation 1
- Limitation 2

## Future Work Directions
What the authors suggest or what logically follows as next steps:
- Direction 1
- Direction 2

## Related Work Patterns
What existing work does this build upon? What are the main research threads this connects to?

## Practical Applications
Real-world applications and implications of this research.

## Novelty Assessment
Rate the novelty on a scale of 1-10 and explain why. How does this compare to existing work in the field?

Be thorough, critical, and objective. Focus on what truly matters scientifically."""

    try:
        response_text = _call_groq_with_retry(prompt)
        if response_text:
            return _parse_deep_analysis(response_text)
        return {"error": "LLM returned empty response.", "raw": ""}
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}", "raw": ""}


def generate_literature_review(
    papers: List[Dict[str, Any]],
    topic: str,
) -> Dict[str, Any]:
    """
    Synthesize multiple papers into a structured literature review.

    Args:
        papers: List of paper dicts with title, abstract, authors, year, summary
        topic: The research topic

    Returns:
        Dict with: overview, themes, timeline, key_authors,
                   methodological_trends, consensus, controversies,
                   most_cited, recommendations
    """
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY not configured.", "raw": ""}

    # Build papers context
    papers_text = _format_papers_for_prompt(papers)

    prompt = f"""You are an expert academic researcher. Based on the following {len(papers)} research papers on the topic of "{topic}", write a comprehensive literature review.

{papers_text}

Structure your review with these EXACT sections:

## Literature Overview
A comprehensive overview of the current state of research on "{topic}" based on these papers (6-10 sentences). What is the field about? Why does it matter?

## Major Research Themes
Identify and describe the 3-5 main research themes or directions found across these papers:
### Theme 1: [Name]
Description and which papers contribute to this theme.
### Theme 2: [Name]
...

## Timeline & Evolution
How has this field evolved? What are the earlier foundational works vs. the latest advances?

## Key Authors & Groups
Who are the most influential researchers/groups in this area? What are their key contributions?

## Methodological Trends
What methodologies dominate? (e.g., deep learning, statistical methods, simulations, etc.)
- Common approaches
- Emerging techniques
- Evaluation metrics used

## Consensus & Established Knowledge
What do most researchers agree on? What is considered "settled science"?

## Open Debates & Controversies
Where do researchers disagree or where are there competing approaches?

## Research Maturity Assessment
Rate the maturity of this field (Emerging / Growing / Mature / Declining) and explain why.

Be thorough and cite specific papers by title where relevant."""

    try:
        response_text = _call_groq_with_retry(prompt)
        if response_text:
            return {"review": response_text, "topic": topic, "papers_analyzed": len(papers)}
        return {"error": "LLM returned empty response.", "raw": ""}
    except Exception as e:
        return {"error": f"Literature review failed: {str(e)}", "raw": ""}


def identify_research_gaps(
    papers: List[Dict[str, Any]],
    topic: str,
) -> Dict[str, Any]:
    """
    Analyze existing research to identify gaps and underexplored areas.

    Returns:
        Dict with: gaps, underexplored_areas, limitations_patterns,
                   contradictions, missing_perspectives,
                   uniqueness_opportunities
    """
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY not configured.", "raw": ""}

    papers_text = _format_papers_for_prompt(papers)

    prompt = f"""You are a research strategy consultant. Analyze these {len(papers)} papers on "{topic}" and identify ALL research gaps and opportunities.

{papers_text}

Provide your analysis with these EXACT sections:

## Identified Research Gaps
List every gap you can find — areas that NO existing paper adequately addresses:
1. **[Gap Name]**: Description of what's missing and why it matters
2. **[Gap Name]**: ...

## Underexplored Areas
Sub-topics or angles within "{topic}" that have received minimal attention:
1. **[Area]**: What exists vs. what's missing
2. ...

## Common Limitations Patterns
What limitations appear across MULTIPLE papers? These represent systematic weaknesses:
1. **[Pattern]**: Which papers share this limitation
2. ...

## Contradictions & Disagreements
Where do papers disagree or present conflicting results?
1. **[Contradiction]**: Paper A says X, Paper B says Y
2. ...

## Missing Perspectives
What viewpoints, datasets, populations, or use-cases are absent?
1. ...

## How YOU Can Be Unique — Uniqueness Opportunities
Based on all the above analysis, here are concrete ways a new researcher can differentiate their work:
1. **[Opportunity]**: What to do + why it would be novel + feasibility (High/Medium/Low)
2. **[Opportunity]**: ...
3. **[Opportunity]**: ...

Be specific and actionable. Don't give vague suggestions — provide concrete research directions that would fill real gaps."""

    try:
        response_text = _call_groq_with_retry(prompt)
        if response_text:
            return {"gaps_analysis": response_text, "topic": topic, "papers_analyzed": len(papers)}
        return {"error": "LLM returned empty response.", "raw": ""}
    except Exception as e:
        return {"error": f"Gap analysis failed: {str(e)}", "raw": ""}


def generate_research_ideas(
    papers: List[Dict[str, Any]],
    topic: str,
    gaps_analysis: str = "",
    user_goal: str = "",
) -> Dict[str, Any]:
    """
    Generate novel research project ideas based on the landscape and gaps.

    Args:
        papers: Analyzed papers
        topic: Research topic
        gaps_analysis: Previously identified gaps (optional)
        user_goal: What the user wants to achieve (optional)

    Returns:
        Dict with: ideas (list of structured project proposals)
    """
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY not configured.", "raw": ""}

    papers_text = _format_papers_for_prompt(papers)
    gaps_ctx = f"\n\nPreviously identified gaps:\n{gaps_analysis}" if gaps_analysis else ""
    user_ctx = f"\n\nThe researcher's specific goal: {user_goal}" if user_goal else ""

    prompt = f"""You are a research innovation advisor. Based on the existing research landscape on "{topic}", generate 5 novel, feasible, and impactful research project ideas.

{papers_text}{gaps_ctx}{user_ctx}

For EACH idea, provide this EXACT structure:

## Idea 1: [Title]
**Novelty**: What makes this unique — how is it different from ALL existing papers listed above?
**Problem Statement**: The specific problem this addresses
**Proposed Approach**: How you would solve it (methodology)
**Why It Matters**: Impact and significance
**Required Resources**: Data, compute, tools needed
**Feasibility**: High / Medium / Low — with justification
**Estimated Timeline**: Rough time needed
**Potential Venues**: Where to publish (conferences, journals)
**Risk Factors**: What could go wrong

## Idea 2: [Title]
...

## Idea 3: [Title]
...

## Idea 4: [Title]
...

## Idea 5: [Title]
...

Requirements for EVERY idea:
- Must be genuinely novel (not a rehash of existing work)
- Must address a real gap identified from the papers
- Must be feasible for a single researcher or small team
- Must have clear differentiation from existing approaches
- Include specific technical details, not vague handwaving"""

    try:
        response_text = _call_groq_with_retry(prompt)
        if response_text:
            return {"ideas": response_text, "topic": topic, "papers_analyzed": len(papers)}
        return {"error": "LLM returned empty response.", "raw": ""}
    except Exception as e:
        return {"error": f"Idea generation failed: {str(e)}", "raw": ""}


def full_research_advisory(
    papers: List[Dict[str, Any]],
    topic: str,
    user_goal: str = "",
) -> Dict[str, Any]:
    """
    Generate a comprehensive research advisory report combining all analyses.

    This is the most powerful function — it produces:
    1. Literature landscape overview
    2. What already exists
    3. What's missing (gaps)
    4. How the user's work can be unique
    5. Concrete project/research ideas

    Args:
        papers: List of paper dicts
        topic: Research topic
        user_goal: Optional user-specific goal

    Returns:
        Complete advisory report
    """
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY not configured.", "raw": ""}

    papers_text = _format_papers_for_prompt(papers)
    user_ctx = f"\nThe researcher's specific goal: {user_goal}" if user_goal else ""

    prompt = f"""You are a world-class research advisor. A researcher wants to work on "{topic}".{user_ctx}

Here are {len(papers)} existing papers in this field:

{papers_text}

Produce a COMPREHENSIVE research advisory report with ALL of these sections:

# Research Advisory Report: {topic}

## 1. Field Overview
What is this field about? How mature is it? Why does it matter now? (8-12 sentences)

## 2. What Already Exists
Summarize the key existing work — categorize by approach/theme:
### Theme A: [Name]
- Papers contributing: [list them]
- Key achievements
### Theme B: [Name]
- ...

## 3. Current State-of-the-Art
What is the current best approach/result? Who achieved it and how?

## 4. Research Gaps & Missing Elements
What's NOT being done that should be?
1. **[Gap]**: explanation + why it matters
2. ...

## 5. How YOUR Research Can Be Unique
Specific strategies to differentiate:
1. **[Strategy]**: What to do + why it's novel + difficulty level
2. ...

## 6. Recommended Research Directions
Top 3 most promising directions ranked by impact × feasibility:
### Direction 1: [Title]
- What: specific description
- Why novel: differentiation from existing work
- Approach: suggested methodology
- Impact: expected contribution
- Timeline: estimated duration

### Direction 2: [Title]
...

### Direction 3: [Title]
...

## 7. Recommended Reading List
The 5 most important papers to deeply study from the list above, and why.

## 8. Potential Collaborators & Venues
- Top conferences/journals for this topic
- Research groups to follow
- Industry connections if relevant

## 9. Risk Assessment
- What could make this research outdated?
- Competitive risks
- Technical challenges to anticipate

## 10. Action Plan
Step-by-step roadmap for the researcher:
1. First 2 weeks: ...
2. Month 1: ...
3. Month 2-3: ...
4. Month 4-6: ...

Be extremely thorough, specific, and actionable. Cite specific papers by title. This should be a document the researcher can immediately use to start their work."""

    try:
        response_text = _call_groq_with_retry(prompt)
        if response_text:
            return {
                "advisory_report": response_text,
                "topic": topic,
                "papers_analyzed": len(papers),
                "user_goal": user_goal,
            }
        return {"error": "LLM returned empty response.", "raw": ""}
    except Exception as e:
        return {"error": f"Advisory report failed: {str(e)}", "raw": ""}


# =============================================
# Helper Functions
# =============================================

def _format_papers_for_prompt(papers: List[Dict[str, Any]], max_papers: int = 25) -> str:
    """Format papers into a text block for LLM prompts."""
    lines = []
    for i, p in enumerate(papers[:max_papers]):
        title = p.get("title", "Untitled")
        authors = ", ".join(p.get("authors", [])[:3])
        if len(p.get("authors", [])) > 3:
            authors += " et al."
        year = p.get("year", "N/A")
        abstract = p.get("abstract", "No abstract available.")
        source = p.get("source", "unknown")
        citations = p.get("citation_count", "N/A")

        # Include summary if available
        summary_text = ""
        summary = p.get("summary", {})
        if isinstance(summary, dict) and summary.get("summary"):
            summary_text = f"\n   AI Summary: {summary['summary'][:300]}"

        # Include extracted text preview
        text_preview = ""
        extracted = p.get("extracted_text", "")
        if extracted:
            text_preview = f"\n   Text Preview: {extracted[:400]}..."

        lines.append(
            f"--- Paper {i+1} ---\n"
            f"   Title: {title}\n"
            f"   Authors: {authors}\n"
            f"   Year: {year} | Source: {source} | Citations: {citations}\n"
            f"   Abstract: {abstract[:500]}"
            f"{summary_text}"
            f"{text_preview}\n"
        )

    return "\n".join(lines)


def _parse_deep_analysis(text: str) -> Dict[str, Any]:
    """Parse deep analysis response into sections."""
    sections = {}
    current_key = "overview"
    current_lines = []

    key_map = {
        "overview": "overview",
        "novel contributions": "contributions",
        "methodology": "methodology",
        "key results": "key_results",
        "limitations": "limitations",
        "future work": "future_work",
        "related work": "related_work_patterns",
        "practical applications": "practical_applications",
        "novelty assessment": "novelty_assessment",
    }

    for line in text.split("\n"):
        stripped = line.strip().lower()

        matched = False
        for heading, key in key_map.items():
            if stripped.startswith("##") and heading in stripped:
                if current_lines:
                    sections[current_key] = "\n".join(current_lines).strip()
                current_key = key
                current_lines = []
                matched = True
                break

        if not matched:
            current_lines.append(line)

    if current_lines:
        sections[current_key] = "\n".join(current_lines).strip()

    sections["raw"] = text
    return sections
