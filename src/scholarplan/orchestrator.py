from __future__ import annotations
from typing import Callable, List, Dict, Any
from .blackboard import Blackboard
from .config import Settings
from .providers import build_provider
from .agents import PlannerAgent, RetrieverAgent, ProcessorAgent, CriticAgent, ArchivistAgent

class ScholarPlan:
    """Blackboard-mediated bounded planning and execution loop."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.board = Blackboard(self.settings.db_path)
        self.provider = build_provider(self.settings.provider)
        self.planner = PlannerAgent(self.board, self.provider)
        self.retriever = RetrieverAgent(
            self.board,
            self.settings.dedup_similarity_threshold,
            self.settings.min_source_relevance,
        )
        self.processor = ProcessorAgent(self.board, self.provider)
        self.critic = CriticAgent(self.board, self.provider)
        self.archivist = ArchivistAgent(self.board)

    def close(self):
        self.board.close()

    def run(self, goal: str, fetchers: List[Callable[[str], List[Dict[str, Any]]]],
            output_dir: str = "outputs") -> int:
        run_id = self.board.create_run(goal)
        steps = 0
        try:
            self.planner.plan(run_id, goal)

            while steps < self.settings.max_steps:
                pending = [
                    t for t in self.board.get_tasks(run_id)
                    if t["status"] in {"pending", "replan_required"}
                ]
                if not pending:
                    break

                task = pending[0]
                task_id = int(task["id"])
                desc = task["description"]
                attempt = int(task["attempt"])
                steps += 1

                source_ids = self.retriever.retrieve(
                    run_id, task_id, desc, fetchers,
                    limit=self.settings.max_sources_per_task,
                )
                if not source_ids:
                    if attempt >= self.settings.max_replans:
                        self.board.update_task(task_id, status="unresolvable")
                    else:
                        self.board.add_feedback(run_id, task_id, "No sources were retrieved.")
                        self.planner.replan_task(
                            run_id, task_id, desc,
                            self.board.get_feedback(task_id),
                            attempt + 1,
                        )
                    continue

                claim_ids = self.processor.process(run_id, task_id, desc)
                if not claim_ids:
                    if attempt >= self.settings.max_replans:
                        self.board.update_task(task_id, status="unresolvable")
                    else:
                        self.board.add_feedback(
                            run_id, task_id, "No source-backed claims were produced."
                        )
                        self.planner.replan_task(
                            run_id, task_id, desc,
                            self.board.get_feedback(task_id),
                            attempt + 1,
                        )
                    continue

                accepted, rejected = self.critic.verify(run_id, task_id)
                if accepted > 0:
                    self.board.update_task(task_id, status="accepted")
                elif attempt >= self.settings.max_replans:
                    # Explicit bounded fallback from Unit 6 improvement feedback.
                    self.board.update_task(task_id, status="unresolvable")
                else:
                    self.planner.replan_task(
                        run_id, task_id, desc,
                        self.board.get_feedback(task_id),
                        attempt + 1,
                    )

            unfinished = [
                t for t in self.board.get_tasks(run_id)
                if t["status"] not in {"accepted", "unresolvable", "failed"}
            ]
            if unfinished and steps >= self.settings.max_steps:
                for t in unfinished:
                    self.board.update_task(int(t["id"]), status="failed")

            # Mark the run complete before export so execution_trace.json
            # records the final lifecycle state rather than "running".
            self.board.set_run_status(run_id, "completed")
            self.archivist.export(run_id, output_dir)
            return run_id
        except Exception:
            self.board.set_run_status(run_id, "failed")
            raise
