from __future__ import annotations
import re
from typing import Dict, Any, List
from .base import LLMProvider

def _sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "") if s.strip()]

class MockLLMProvider(LLMProvider):
    """Deterministic provider for reproducible tests and demonstrations."""

    def create_plan(self, goal: str, feedback: List[str] | None = None) -> Dict[str, Any]:
        goal = goal.strip()
        if not goal:
            raise ValueError("goal must not be empty")
        suffix = ""
        if feedback:
            suffix = " Focus on alternative evidence because earlier evidence was rejected."
        return {
            "goal": goal,
            "subtasks": [
                {"key": "scope", "description": f"Define the scope and key concepts for: {goal}."},
                {"key": "evidence", "description": f"Retrieve recent scholarly evidence relevant to: {goal}.{suffix}"},
                {"key": "synthesis", "description": f"Compare findings and limitations relevant to: {goal}."},
            ],
        }

    def extract_claims(self, task: str, source: Dict[str, Any]) -> List[Dict[str, str]]:
        abstract = source.get("abstract") or ""
        claims = []
        for sent in _sentences(abstract)[:2]:
            if len(sent.split()) >= 6:
                claims.append({"claim": sent, "evidence": sent})
        return claims

    def verify_claim(self, claim: str, evidence: str) -> Dict[str, Any]:
        claim_tokens = set(re.findall(r"[A-Za-z0-9]+", claim.lower()))
        evidence_tokens = set(re.findall(r"[A-Za-z0-9]+", evidence.lower()))
        overlap = len(claim_tokens & evidence_tokens) / len(claim_tokens) if claim_tokens else 0.0
        supported = overlap >= 0.65
        return {
            "label": "SUPPORTED" if supported else "UNSUPPORTED",
            "confidence": round(min(0.99, 0.55 + overlap * 0.44), 3),
            "rationale": (
                "High evidence overlap in deterministic verifier."
                if supported else
                "Insufficient overlap between claim and cited evidence."
            ),
        }
