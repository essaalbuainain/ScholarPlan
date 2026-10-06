from scholarplan.blackboard import Blackboard
from scholarplan.models import Task

def test_blackboard_persists_task(tmp_path):
    board = Blackboard(str(tmp_path / "test.db"))
    run_id = board.create_run("test goal")
    task_id = board.add_task(Task(None, run_id, "t1", "test task"))
    rows = board.get_tasks(run_id)
    assert len(rows) == 1
    assert rows[0]["id"] == task_id
    assert rows[0]["status"] == "pending"
    board.close()
