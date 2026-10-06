from scholarplan.blackboard import Blackboard
from scholarplan.agents.retriever import RetrieverAgent
from scholarplan.models import Task

def test_retriever_deduplicates_by_doi(tmp_path):
    board = Blackboard(str(tmp_path / "db.sqlite"))
    run_id = board.create_run("goal")
    task_id = board.add_task(Task(None, run_id, "t", "task"))
    agent = RetrieverAgent(board, similarity_threshold=0.90)
    items = [
        {"title": "A study of agents", "authors": "A", "year": 2024, "abstract": "A meaningful abstract about agents and planning.",
         "doi": "10.1/abc", "arxiv_id": None, "source_api": "A", "url": None},
        {"title": "A study of agents", "authors": "A", "year": 2024, "abstract": "A meaningful abstract about agents and planning.",
         "doi": "10.1/abc", "arxiv_id": None, "source_api": "B", "url": None},
    ]
    ids = agent.retrieve(run_id, task_id, "q", [lambda q: items], limit=5)
    assert len(ids) == 1
    stored = board.get_sources(task_id)
    assert stored[0]["title"] == "A study of agents"
    assert 0.0 <= stored[0]["relevance"] <= 1.0
    board.close()
