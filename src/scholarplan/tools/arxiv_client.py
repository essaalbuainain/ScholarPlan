from __future__ import annotations
from typing import List, Dict, Any
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

NS = {"a": "http://www.w3.org/2005/Atom"}

def search_arxiv(query: str, max_results: int = 5, timeout: int = 20) -> List[Dict[str, Any]]:
    params = urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
    })
    req = urllib.request.Request(
        f"https://export.arxiv.org/api/query?{params}",
        headers={"User-Agent": "ScholarPlan/0.1 (academic demonstration)"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        xml = response.read()
    root = ET.fromstring(xml)
    out = []
    for entry in root.findall("a:entry", NS):
        id_url = entry.findtext("a:id", default="", namespaces=NS)
        arxiv_id = id_url.rsplit("/", 1)[-1] if id_url else None
        published = entry.findtext("a:published", default="", namespaces=NS)
        authors = ", ".join(
            a.findtext("a:name", default="", namespaces=NS)
            for a in entry.findall("a:author", NS)
        )
        out.append({
            "title": " ".join((entry.findtext("a:title", default="", namespaces=NS) or "").split()),
            "authors": authors,
            "year": int(published[:4]) if published[:4].isdigit() else None,
            "abstract": " ".join((entry.findtext("a:summary", default="", namespaces=NS) or "").split()),
            "doi": None,
            "arxiv_id": arxiv_id,
            "source_api": "arXiv",
            "url": id_url or None,
        })
    return out
