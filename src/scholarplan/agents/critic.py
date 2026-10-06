from __future__ import annotations
from ..blackboard import Blackboard
from ..models import Verdict
from ..providers.base import LLMProvider

class CriticAgent:
    def __init__(self, board: Blackboard, provider: LLMProvider):
        self.board = board
        self.provider = provider

    def verify(self, run_id: int, task_id: int):
        self.board.update_task(task_id, status="verifying")
        accepted = rejected = 0
        for claim in self.board.get_claims(task_id):
            if claim["status"] != "pending":
                continue
            result = self.provider.verify_claim(claim["text"], claim["evidence"])
            verdict = Verdict(
                None, int(claim["id"]),
                result.get("label", "UNSUPPORTED"),
                float(result.get("confidence", 0.0)),
                str(result.get("rationale", "")),
            )
            verdict.validate()
            self.board.add_verdict(verdict)
            if verdict.label == "SUPPORTED":
                self.board.set_claim_status(int(claim["id"]), "accepted")
                accepted += 1
            else:
                self.board.set_claim_status(int(claim["id"]), "rejected")
                self.board.add_feedback(
                    run_id, task_id,
                    f"Critic rejected claim {claim['id']}: {verdict.rationale}",
                )
                rejected += 1
        self.board.send_message(
            run_id, task_id, "Critic", "Planner",
            "confirm" if rejected == 0 and accepted > 0 else "reject",
            {"accepted": accepted, "rejected": rejected},
        )
        self.board.log_event(
            run_id, "Critic", "verification_completed",
            {"task_id": task_id, "accepted": accepted, "rejected": rejected},
        )
        return accepted, rejected
