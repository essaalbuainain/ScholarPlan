from __future__ import annotations
import json
import os
import re
from typing import Dict, Any, List
from .base import LLMProvider

class LMStudioProvider(LLMProvider):
    """
    Live local LLM provider using LM Studio's OpenAI-compatible API.

    Reliability strategy:
    1) request JSON mode;
    2) parse strict JSON;
    3) repair malformed JSON with json-repair;
    4) normalise list-vs-object outputs;
    5) for Processor only, fall back to source sentences if formatting still fails.

    The fallback is deliberately source-grounded, so malformed model formatting
    cannot invent claims or crash the whole run.
    """

    def __init__(self):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install the 'openai' package to use LM Studio mode.") from exc

        self.base_url = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
        self.model = os.getenv("LM_STUDIO_MODEL", "qwen2.5-3b-instruct")
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=os.getenv("LM_STUDIO_API_KEY", "lm-studio"),
        )

    @staticmethod
    def _strip_fences(text: str) -> str:
        text = (text or "").strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    @classmethod
    def _parse_json(cls, text: str, expected_key: str | None = None) -> Dict[str, Any]:
        text = cls._strip_fences(text)

        # Strict JSON first.
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            obj = None

        # Try the outermost object/list if the model added prose.
        if obj is None:
            candidates = []
            a, b = text.find("{"), text.rfind("}")
            if a != -1 and b > a:
                candidates.append(text[a:b+1])
            a, b = text.find("["), text.rfind("]")
            if a != -1 and b > a:
                candidates.append(text[a:b+1])

            for candidate in candidates:
                try:
                    obj = json.loads(candidate)
                    break
                except json.JSONDecodeError:
                    continue

        # Repair common small-model mistakes such as missing ] or trailing commas.
        if obj is None:
            try:
                from json_repair import repair_json
                repaired = repair_json(text)
                obj = json.loads(repaired)
            except Exception:
                obj = None

        if obj is None:
            raise ValueError(f"Could not parse model JSON. Raw output: {text[:1200]}")

        # Qwen sometimes returns the requested array as the root value.
        if expected_key and isinstance(obj, list):
            obj = {expected_key: obj}

        if not isinstance(obj, dict):
            raise ValueError(
                f"Expected a JSON object but received {type(obj).__name__}: {str(obj)[:500]}"
            )

        return obj

    def _chat(self, system: str, user: str) -> str:
        kwargs = dict(
            model=self.model,
            temperature=0.0,
            max_tokens=900,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        try:
            kwargs["response_format"] = {"type": "json_object"}
            response = self.client.chat.completions.create(**kwargs)
        except Exception:
            kwargs.pop("response_format", None)
            response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    def _json_call(self, system: str, user: str, expected_key: str | None = None) -> Dict[str, Any]:
        raw = self._chat(system, user)
        try:
            return self._parse_json(raw, expected_key=expected_key)
        except Exception:
            # One controlled repair retry.
            repair_system = (
                "Return ONLY one valid JSON object. Fix syntax only. "
                "Do not explain, do not use Markdown, and preserve the intended values."
            )
            repaired_raw = self._chat(
                repair_system,
                "Repair this malformed JSON output:\n\n" + raw[:5000],
            )
            return self._parse_json(repaired_raw, expected_key=expected_key)

    def create_plan(self, goal: str, feedback: List[str] | None = None) -> Dict[str, Any]:
        system = (
            "You are ScholarPlan's Planner. Return ONLY valid JSON. "
            "Schema: {\"goal\":\"...\",\"subtasks\":["
            "{\"key\":\"scope\",\"description\":\"...\"},"
            "{\"key\":\"evidence\",\"description\":\"...\"},"
            "{\"key\":\"synthesis\",\"description\":\"...\"}]}. "
            "Produce exactly 3 concise, non-overlapping academic research subtasks."
        )
        data = self._json_call(
            system,
            f"Research goal: {goal}\nPrior feedback: {feedback or []}",
            expected_key="subtasks",
        )
        if not isinstance(data.get("subtasks"), list):
            raise ValueError("Planner output is missing the subtasks list.")
        return data

    @staticmethod
    def _source_sentence_fallback(abstract: str) -> List[Dict[str, str]]:
        """
        Safe degradation path for malformed Processor output.

        Claims are copied from the retrieved source rather than invented, so the
        Critic can still verify them and the run remains auditable.
        """
        sentences = [
            s.strip()
            for s in re.split(r"(?<=[.!?])\s+", abstract)
            if len(s.strip().split()) >= 6
        ]
        return [{"claim": s, "evidence": s} for s in sentences[:2]]

    def extract_claims(self, task: str, source: Dict[str, Any]) -> List[Dict[str, str]]:
        abstract = (source.get("abstract") or "").strip()
        if not abstract:
            return []

        system = (
            "You are ScholarPlan's Processor. Return ONLY valid JSON. "
            "Schema: {\"claims\":[{\"claim\":\"...\",\"evidence\":\"...\"}]}. "
            "Return at most 2 claims. Each claim must be directly supported by the abstract. "
            "Keep each evidence field to ONE source sentence."
        )
        user = (
            f"Task: {task}\n"
            f"Title: {source.get('title', '')}\n"
            f"Abstract: {abstract}"
        )

        try:
            data = self._json_call(system, user, expected_key="claims")
            claims = data.get("claims", [])
        except Exception:
            # Non-deterministic local-model formatting must not terminate the run.
            return self._source_sentence_fallback(abstract)

        if not isinstance(claims, list):
            return self._source_sentence_fallback(abstract)

        clean = []
        for item in claims[:2]:
            if not isinstance(item, dict):
                continue
            claim = str(item.get("claim", "")).strip()
            evidence = str(item.get("evidence", "")).strip()
            if claim and evidence:
                clean.append({"claim": claim, "evidence": evidence})

        return clean or self._source_sentence_fallback(abstract)

    def verify_claim(self, claim: str, evidence: str) -> Dict[str, Any]:
        system = (
            "You are ScholarPlan's independent Critic. Return ONLY valid JSON. "
            "Schema: {\"label\":\"SUPPORTED\",\"confidence\":0.95,\"rationale\":\"...\"}. "
            "label must be SUPPORTED or UNSUPPORTED. confidence must be from 0 to 1. "
            "Judge only the supplied evidence."
        )
        try:
            data = self._json_call(
                system,
                f"Claim: {claim}\nEvidence: {evidence}",
            )
        except Exception:
            # Conservative failure policy: malformed Critic output never passes a claim.
            return {
                "label": "UNSUPPORTED",
                "confidence": 0.0,
                "rationale": "Critic output could not be parsed; conservative rejection applied.",
            }

        label = str(data.get("label", "UNSUPPORTED")).upper().strip()
        if label not in {"SUPPORTED", "UNSUPPORTED"}:
            label = "UNSUPPORTED"

        try:
            confidence = float(data.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0

        return {
            "label": label,
            "confidence": max(0.0, min(1.0, confidence)),
            "rationale": str(data.get("rationale", "")).strip(),
        }
