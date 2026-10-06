from __future__ import annotations
import json
import os
from typing import Dict, Any, List
from .base import LLMProvider

class AzureOpenAIProvider(LLMProvider):
    """Live provider for Planner/Processor/Critic using Azure OpenAI deployments."""

    def __init__(self):
        try:
            from openai import AzureOpenAI
        except ImportError as exc:
            raise RuntimeError("Install the 'openai' package to use Azure mode.") from exc

        self.client = AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview"),
        )
        self.planner_model = os.environ["AZURE_OPENAI_PLANNER_DEPLOYMENT"]
        self.critic_model = os.getenv("AZURE_OPENAI_CRITIC_DEPLOYMENT", self.planner_model)

    def _json_call(self, deployment: str, system: str, user: str) -> Dict[str, Any]:
        response = self.client.chat.completions.create(
            model=deployment,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return json.loads(response.choices[0].message.content)

    def create_plan(self, goal: str, feedback: List[str] | None = None) -> Dict[str, Any]:
        system = (
            "You are ScholarPlan's Planner. Return JSON with keys 'goal' and 'subtasks'. "
            "Each subtask must contain 'key' and 'description'. Produce 2-5 non-overlapping "
            "research subtasks. Do not fabricate sources."
        )
        return self._json_call(
            self.planner_model,
            system,
            f"Research goal: {goal}\\nPrior feedback: {feedback or []}",
        )

    def extract_claims(self, task: str, source: Dict[str, Any]) -> List[Dict[str, str]]:
        system = (
            "You are ScholarPlan's Processor. Return JSON {'claims': [...]} where each "
            "item has 'claim' and 'evidence'. Only make claims directly supported by "
            "the supplied abstract/evidence."
        )
        user = f"Task: {task}\\nTitle: {source.get('title')}\\nAbstract: {source.get('abstract')}"
        return self._json_call(self.planner_model, system, user).get("claims", [])

    def verify_claim(self, claim: str, evidence: str) -> Dict[str, Any]:
        system = (
            "You are ScholarPlan's independent Critic. Return JSON with 'label' "
            "(SUPPORTED or UNSUPPORTED), 'confidence' (0-1), and 'rationale'. "
            "Be conservative and judge only the supplied evidence."
        )
        return self._json_call(
            self.critic_model,
            system,
            f"Claim: {claim}\\nEvidence: {evidence}",
        )
