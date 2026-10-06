from __future__ import annotations
import argparse
from pathlib import Path
from .config import Settings
from .orchestrator import ScholarPlan
from .tools.fixtures import load_fixture_sources
from .tools.openalex_client import search_openalex
from .tools.crossref_client import search_crossref
from .tools.arxiv_client import search_arxiv

def main():
    parser = argparse.ArgumentParser(description="ScholarPlan academic research planning agent")
    parser.add_argument("goal", nargs="?", help="Research goal")
    parser.add_argument("--provider", choices=["mock", "lmstudio", "azure"], default="mock")
    parser.add_argument("--mode", choices=["fixture", "live"], default="fixture")
    parser.add_argument("--fixtures", default="fixtures/demo_sources.json")
    parser.add_argument("--db", default="scholarplan.db")
    parser.add_argument("--output", default="outputs")
    args = parser.parse_args()

    goal = args.goal or input("Enter a research goal: ").strip()
    settings = Settings(db_path=args.db, provider=args.provider)
    app = ScholarPlan(settings)
    try:
        if args.mode == "fixture":
            items = load_fixture_sources(args.fixtures)
            fetchers = [lambda _: items]
        else:
            fetchers = [search_openalex, search_crossref, search_arxiv]

        run_id = app.run(goal, fetchers, args.output)
        trace = app.board.export_trace(run_id)
        supported = [c for c in trace["claims"] if c["status"] == "accepted"]

        print("ScholarPlan run completed")
        print(f"Run ID: {run_id}")
        print(f"Tasks: {len(trace['tasks'])}")
        print(f"Sources: {len(trace['sources'])}")
        print(f"Verified claims: {len(supported)}")
        print(f"Output directory: {args.output}")
    finally:
        app.close()

if __name__ == "__main__":
    main()
