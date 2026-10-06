from __future__ import annotations
from typing import List
from ..models import Task
from ..blackboard import Blackboard
from ..providers.base import LLMProvider


class PlannerAgent:
    def __init__(self, board: Blackboard, provider: LLMProvider):
        self.board = board
        self.provider = provider

    def plan(self, run_id: int, goal: str, feedback: List[str] | None = None) -> List[int]:
        data = self.provider.create_plan(goal, feedback or [])
        subtasks = data.get("subtasks") if isinstance(data, dict) else None

        if not isinstance(subtasks, list) or not subtasks:
            subtasks = [
                {"key": "scope", "description": f"Define the scope, terminology, and evaluation criteria for: {goal}."},
                {"key": "evidence", "description": f"Retrieve and compare scholarly evidence relevant to: {goal}."},
                {"key": "synthesis", "description": f"Synthesise findings, limitations, and implications relevant to: {goal}."},
            ]

        ids: List[int] = []

        for index, item in enumerate(subtasks[:3], start=1):
            if isinstance(item, str):
                key = f"task_{index}"
                description = item.strip()
            elif isinstance(item, dict):
                key = str(
                    item.get("key")
                    or item.get("id")
                    or item.get("name")
                    or f"task_{index}"
                ).strip()
                description = str(
                    item.get("description")
                    or item.get("task")
                    or item.get("objective")
                    or item.get("instruction")
                    or item.get("title")
                    or ""
                ).strip()
            else:
                key = f"task_{index}"
                description = ""

            if not description:
                fallback_descriptions = {
                    1: f"Define the scope and key concepts for: {goal}.",
                    2: f"Retrieve scholarly evidence relevant to: {goal}.",
                    3: f"Compare findings, limitations, and implications relevant to: {goal}.",
                }
                description = fallback_descriptions.get(
                    index,
                    f"Investigate scholarly evidence relevant to: {goal}."
                )

            task = Task(None, run_id, key or f"task_{index}", description)
            task.validate()
            ids.append(self.board.add_task(task))

        while len(ids) < 3:
            index = len(ids) + 1
            task = Task(
                None,
                run_id,
                f"fallback_{index}",
                f"Investigate additional scholarly evidence relevant to: {goal}.",
            )
            task.validate()
            ids.append(self.board.add_task(task))

        self.board.send_message(
            run_id,
            None,
            "Planner",
            "Blackboard",
            "inform",
            {"subtasks": len(ids), "goal": goal},
        )
        self.board.log_event(run_id, "Planner", "plan_created", {"task_ids": ids})
        return ids

    def replan_task(
        self,
        run_id: int,
        task_id: int,
        original_description: str,
        feedback: List[str],
        next_attempt: int,
    ) -> None:
        revised = (
            original_description
            + " | Re-plan using Critic feedback: "
            + " ".join(feedback[-2:])
        )
        self.board.update_task(
            task_id,
            description=revised,
            status="pending",
            attempt=next_attempt,
        )
        self.board.send_message(
            run_id,
            task_id,
            "Planner",
            "Retriever",
            "request",
            {"description": revised, "attempt": next_attempt},
        )
        self.board.log_event(
            run_id,
            "Planner",
            "task_replanned",
            {"task_id": task_id, "attempt": next_attempt},
        )
