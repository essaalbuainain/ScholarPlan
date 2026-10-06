from scholarplan.blackboard import Blackboard
from scholarplan.providers.mock import MockLLMProvider
from scholarplan.agents.planner import PlannerAgent

def test_planner_returns_valid_tasks(tmp_path):
    board = Blackboard(str(tmp_path / "db.sqlite"))
    run_id = board.create_run("Study hallucination mitigation")
    planner = PlannerAgent(board, MockLLMProvider())
    ids = planner.plan(run_id, "Study hallucination mitigation")
    assert len(ids) == 3
    tasks = board.get_tasks(run_id)
    assert all(t["description"] for t in tasks)
    assert all(t["task_key"] for t in tasks)
    board.close()
