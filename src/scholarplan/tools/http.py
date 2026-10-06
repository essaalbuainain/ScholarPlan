from __future__ import annotations
import json
import urllib.request
import urllib.parse

def get_json(url: str, params: dict | None = None, timeout: int = 20) -> dict:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url, headers={"User-Agent": "ScholarPlan/0.1 (academic demonstration)"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))
