import json
from pathlib import Path

def load_fixture_sources(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))
