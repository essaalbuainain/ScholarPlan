from __future__ import annotations
from typing import List, Dict, Any
from .http import get_json
import re
import html

def _clean_text(text: str) -> str:
    cleaned = html.unescape(text or "")
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    return " ".join(cleaned.split())

def _clean_abstract(text: str) -> str:
    return _clean_text(text)

def search_crossref(query: str, rows: int = 5, timeout: int = 20) -> List[Dict[str, Any]]:
    data = get_json(
        "https://api.crossref.org/works",
        {"query.bibliographic": query, "rows": rows},
        timeout,
    )
    out = []
    for item in data.get("message", {}).get("items", []):
        title = _clean_text((item.get("title") or [""])[0])
        authors = ", ".join(
            " ".join(filter(None, [a.get("given"), a.get("family")]))
            for a in item.get("author", [])[:8]
        )
        parts = (item.get("published-print") or item.get("published-online") or {}).get("date-parts", [[]])
        year = parts[0][0] if parts and parts[0] else None
        out.append({
            "title": title,
            "authors": authors,
            "year": year,
            "abstract": _clean_abstract(item.get("abstract") or ""),
            "doi": item.get("DOI"),
            "arxiv_id": None,
            "source_api": "Crossref",
            "url": item.get("URL"),
        })
    return out
