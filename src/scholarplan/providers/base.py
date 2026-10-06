from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class LLMProvider(ABC):
    @abstractmethod
    def create_plan(self, goal: str, feedback: List[str] | None = None) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def extract_claims(self, task: str, source: Dict[str, Any]) -> List[Dict[str, str]]:
        raise NotImplementedError

    @abstractmethod
    def verify_claim(self, claim: str, evidence: str) -> Dict[str, Any]:
        raise NotImplementedError
