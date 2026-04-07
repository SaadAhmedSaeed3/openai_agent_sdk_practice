"""
tools/web_search_tools.py
-------------------------
LangSearch API wrapper + research text persistence tools.
"""

import os
import re
from pathlib import Path

import httpx
from agents import function_tool

RESEARCH_DIR = Path("presentation_creator/refrence_txt")
LANGSEARCH_URL = "https://api.langsearch.com/v1/web-search"


@function_tool
def web_search(query: str, count: int = 10) -> str:
    """
    Search the web using the LangSearch API. Returns a formatted list of
    results with title, URL, and snippet for each hit.

    Args:
        query: The search query string.
        count: Number of results to return (1-10, default 10).
    """
    api_key = os.getenv("LANGSEARCH_API_KEY")
    if not api_key:
        return "ERROR: LANGSEARCH_API_KEY not set in environment."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {"query": query, "count": min(max(count, 1), 10)}

    try:
        resp = httpx.post(LANGSEARCH_URL, json=body, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except httpx.TimeoutException:
        return "ERROR: LangSearch request timed out."
    except httpx.HTTPStatusError as e:
        return f"ERROR: LangSearch HTTP {e.response.status_code}: {e.response.text[:300]}"
    except Exception as e:
        return f"ERROR: {e}"

    results = data.get("webPages", {}).get("value", data.get("results", []))
    if not results:
        return f"No results found for: {query}"

    lines = [f"Search results for: {query}\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r.get('name', r.get('title', '(no title)'))}")
        lines.append(f"    URL: {r.get('url', '')}")
        snippet = r.get("snippet", r.get("description", r.get("summary", "(no snippet)")))
        lines.append(f"    {snippet}")
        lines.append("")
    return "\n".join(lines)


@function_tool
def save_research_text(topic_slug: str, content: str) -> str:
    """
    Save a research article to presentation_creator/refrence_txt/{topic_slug}.txt.

    Args:
        topic_slug: Filename slug (e.g. "ai_software_business"). Use only
                    lowercase letters, digits, and underscores.
        content: The full research article text.
    """
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    safe_slug = re.sub(r"[^\w]", "_", topic_slug).lower().strip("_")
    path = RESEARCH_DIR / f"{safe_slug}.txt"
    path.write_text(content, encoding="utf-8")
    return f"Saved research ({len(content)} chars) -> {path.resolve()}"


@function_tool
def read_research_text(filename: str) -> str:
    """
    Read a research article from presentation_creator/refrence_txt/.

    Args:
        filename: The .txt filename (e.g. "ai_software_business.txt").
    """
    path = RESEARCH_DIR / filename
    if not path.exists():
        available = [f.name for f in RESEARCH_DIR.glob("*.txt")]
        return (
            f"ERROR: '{filename}' not found in {RESEARCH_DIR}.\n"
            f"Available files: {available}"
        )
    return path.read_text(encoding="utf-8")
