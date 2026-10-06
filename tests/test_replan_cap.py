from scholarplan.config import Settings
from scholarplan.orchestrator import ScholarPlan

def test_empty_retrieval_eventually_marks_tasks_unresolvable(tmp_path):
    settings = Settings(
        db_path=str(tmp_path / "run.db"),
        provider="mock",
        max_steps=20,
        max_replans=3,
        max_sources_per_task=5,
    )
    app = ScholarPlan(settings)
    try:
        run_id = app.run("Impossible research goal", [lambda _: []], str(tmp_path / "out"))
        tasks = app.board.get_tasks(run_id)
        assert all(t["status"] == "unresolvable" for t in tasks)
        assert all(t["attempt"] == 3 for t in tasks)
    finally:
        app.close()
