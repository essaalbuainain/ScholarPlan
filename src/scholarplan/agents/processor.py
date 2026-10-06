from __future__ import annotations
from ..blackboard import Blackboard
from ..models import Claim
from ..providers.base import LLMProvider

class ProcessorAgent:
    def __init__(self, board: Blackboard, provider: LLMProvider):
        self.board = board
        self.provider = provider

    def process(self, run_id: int, task_id: int, task_description: str):
        self.board.update_task(task_id, status="processing")
        claim_ids = []
        for row in self.board.get_sources(task_id):
            source = dict(row)
            for item in self.provider.extract_claims(task_description, source):
                text = str(item.get("claim", "")).strip()
                evidence = str(item.get("evidence", "")).strip()
                if text and evidence:
                    claim_ids.append(
                        self.board.add_claim(
                            Claim(None, run_id, task_id, int(row["id"]), text, evidence)
                        )
                    )
        self.board.send_message(
            run_id, task_id, "Processor", "Critic", "inform",
            {"claim_ids": claim_ids},
        )
        self.board.log_event(
            run_id, "Processor", "processing_completed",
            {"task_id": task_id, "claim_count": len(claim_ids)},
        )
        return claim_ids
