from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

VALID_TASK_STATUSES = {
    "pending", "retrieving", "processing", "verifying",
    "accepted", "replan_required", "unresolvable", "failed"
}

@dataclass
class Task:
    id: Optional[int]
    run_id: int
    task_key: str
    description: str
    status: str = "pending"
    attempt: int = 0

    def validate(self) -> None:
        if not self.task_key.strip():
            raise ValueError("task_key must not be empty")
        if not self.description.strip():
            raise ValueError("description must not be empty")
        if self.status not in VALID_TASK_STATUSES:
            raise ValueError(f"invalid task status: {self.status}")
        if self.attempt < 0:
            raise ValueError("attempt must be >= 0")

@dataclass
class SourceRecord:
    id: Optional[int]
    run_id: int
    task_id: int
    title: str
    authors: str
    year: Optional[int]
    abstract: str
    doi: Optional[str]
    arxiv_id: Optional[str]
    source_api: str
    url: Optional[str] = None
    relevance: float = 0.0

    @property
    def stable_id(self) -> str:
        if self.doi:
            return f"doi:{self.doi.lower().strip()}"
        if self.arxiv_id:
            return f"arxiv:{self.arxiv_id.lower().strip()}"
        return f"title:{' '.join(self.title.lower().split())}"

@dataclass
class Claim:
    id: Optional[int]
    run_id: int
    task_id: int
    source_id: int
    text: str
    evidence: str
    status: str = "pending"

@dataclass
class Verdict:
    id: Optional[int]
    claim_id: int
    label: str
    confidence: float
    rationale: str

    def validate(self) -> None:
        if self.label not in {"SUPPORTED", "UNSUPPORTED"}:
            raise ValueError("verdict label must be SUPPORTED or UNSUPPORTED")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
