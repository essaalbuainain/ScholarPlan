from __future__ import annotations
from difflib import SequenceMatcher
from typing import List, Dict, Any, Callable
from ..models import SourceRecord
from ..blackboard import Blackboard
from ..relevance import source_relevance


class RetrieverAgent:
    def __init__(self, board: Blackboard, similarity_threshold: float = 0.90,
                 min_relevance: float = 0.25):
        self.board = board
        self.similarity_threshold = similarity_threshold
        self.min_relevance = min_relevance

    @staticmethod
    def title_similarity(a: str, b: str) -> float:
        aa = " ".join((a or "").lower().split())
        bb = " ".join((b or "").lower().split())
        return SequenceMatcher(None, aa, bb).ratio()

    def _deduplicate(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        kept, seen_ids = [], set()
        for item in items:
            doi = (item.get("doi") or "").lower().strip()
            arxiv_id = (item.get("arxiv_id") or "").lower().strip()
            stable = f"doi:{doi}" if doi else (f"arxiv:{arxiv_id}" if arxiv_id else None)
            if stable and stable in seen_ids:
                continue
            if any(
                self.title_similarity(item.get("title", ""), other.get("title", "")) >= self.similarity_threshold
                for other in kept
            ):
                continue
            kept.append(item)
            if stable:
                seen_ids.add(stable)
        return kept

    def retrieve(self, run_id: int, task_id: int, query: str,
                 fetchers: List[Callable[[str], List[Dict[str, Any]]]],
                 limit: int = 5) -> List[int]:
        self.board.update_task(task_id, status="retrieving")
        combined: List[Dict[str, Any]] = []
        for fetch in fetchers:
            try:
                combined.extend(fetch(query))
            except Exception as exc:
                self.board.log_event(
                    run_id, "Retriever", "source_error",
                    {"query": query, "fetcher": getattr(fetch, "__name__", "fetcher"), "error": str(exc)},
                )

        unique = self._deduplicate(combined)
        scored = [(source_relevance(query, item), item) for item in unique]
        scored.sort(key=lambda pair: pair[0], reverse=True)

        # Prefer sources above the relevance gate. If a very unusual query yields
        # none, keep the best ranked records rather than forcing an empty result.
        relevant = [(score, item) for score, item in scored if score >= self.min_relevance]
        selected = (relevant if relevant else scored)[:limit]

        ids = []
        for score, item in selected:
            source = SourceRecord(
                None, run_id, task_id,
                item.get("title", ""), item.get("authors", ""),
                item.get("year"), item.get("abstract", ""),
                item.get("doi"), item.get("arxiv_id"),
                item.get("source_api", "unknown"), item.get("url"),
                score,
            )
            ids.append(self.board.add_source(source))

        self.board.send_message(
            run_id, task_id, "Retriever", "Processor", "inform",
            {
                "source_ids": ids,
                "unique_sources": len(ids),
                "relevance_gate": self.min_relevance,
            },
        )
        self.board.log_event(
            run_id, "Retriever", "retrieval_completed",
            {
                "task_id": task_id,
                "source_count": len(ids),
                "relevance_gate": self.min_relevance,
            },
        )
        return ids
