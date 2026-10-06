import json
from pathlib import Path
from scholarplan.config import Settings
from scholarplan.orchestrator import ScholarPlan

def test_end_to_end_fixture_run(tmp_path):
    root = Path(__file__).resolve().parents[1]
    items = json.loads((root / "fixtures" / "demo_sources.json").read_text(encoding="utf-8"))
    settings = Settings(
        db_path=str(tmp_path / "run.db"),
        provider="mock",
        max_steps=20,
        max_replans=3,
        max_sources_per_task=5,
    )
    app = ScholarPlan(settings)
    try:
        run_id = app.run(
            "How can LLM agents reduce hallucinations in academic research?",
            [lambda _: items],
            str(tmp_path / "outputs"),
        )
        trace = app.board.export_trace(run_id)
        assert trace["run"]["status"] == "completed"
        assert len(trace["tasks"]) == 3
        assert any(c["status"] == "accepted" for c in trace["claims"])
        assert (tmp_path / "outputs" / "report.md").exists()
        assert (tmp_path / "outputs" / "execution_trace.json").exists()
    finally:
        app.close()
