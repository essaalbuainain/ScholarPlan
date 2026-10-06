from __future__ import annotations
from typing import List, Dict, Any
from .http import get_json

def search_openalex(query: str, per_page: int = 5, timeout: int = 20) -> List[Dict[str, Any]]:
    data = get_json("https://api.openalex.org/works", {"search": query, "per-page": per_page}, timeout)
    out = []
    for item in data.get("results", []):
        inv = item.get("abstract_inverted_index") or {}
        abstract = ""
        if inv:
            positions = []
            for word, pos_list in inv.items():
                for pos in pos_list:
                    positions.append((pos, word))
            abstract = " ".join(word for _, word in sorted(positions))
        doi = (item.get("doi") or "").replace("https://doi.org/", "") or None
        authors = ", ".join(
            a.get("author", {}).get("display_name", "")
            for a in item.get("authorships", [])[:8]
            if a.get("author", {}).get("display_name")
        )
        out.append({
            "title": item.get("title") or "",
            "authors": authors,
            "year": item.get("publication_year"),
            "abstract": abstract,
            "doi": doi,
            "arxiv_id": None,
            "source_api": "OpenAlex",
            "url": (item.get("primary_location") or {}).get("landing_page_url"),
        })
    return out
