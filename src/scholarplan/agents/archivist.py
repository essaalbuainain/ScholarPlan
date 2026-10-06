from __future__ import annotations
from pathlib import Path
import json
import html
import re
from ..blackboard import Blackboard
from ..relevance import relevance_score


def _clean_title(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(value.split())


class ArchivistAgent:
    def __init__(self, board: Blackboard, publication_relevance_gate: float = 0.25):
        self.board = board
        self.publication_relevance_gate = publication_relevance_gate

    def export(self, run_id: int, output_dir: str):
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        preliminary_trace = self.board.export_trace(run_id)
        goal = preliminary_trace["run"]["goal"]
        accepted_claims = self.board.get_supported_claims(run_id)

        published = []
        for claim in accepted_claims:
            score = relevance_score(goal, claim["title"], claim["abstract"] or "")
            if score >= self.publication_relevance_gate:
                published.append((score, claim))

        lines = [
            "# ScholarPlan Research Output",
            "",
            f"**Goal:** {goal}",
            "",
            f"**Evidence-verified claims:** {len(accepted_claims)}",
            f"**Published after relevance gate ({self.publication_relevance_gate:.2f}):** {len(published)}",
            "",
            "## Verified and Relevant Findings",
            "",
        ]
        for i, (score, claim) in enumerate(published, 1):
            ident = claim["doi"] or claim["arxiv_id"] or claim["url"] or "source"
            lines += [
                f"{i}. {claim['text']}  ",
                f"   - Source: {_clean_title(claim['title'])} ({ident})",
                f"   - Relevance score: {score:.2f}",
            ]
        if not published:
            lines.append("No claims passed both evidence verification and the relevance gate.")

        used_source_ids = {int(claim["source_id"]) for _, claim in published}
        bib = []
        for source in preliminary_trace["sources"]:
            if int(source["id"]) not in used_source_ids:
                continue
            key = f"source{source['id']}"
            title = _clean_title(source["title"]).replace("{", "").replace("}", "")
            bib.append(
                "@misc{" + key + ",\n"
                f"  title = {{{title}}},\n"
                f"  author = {{{source['authors'] or ''}}},\n"
                f"  year = {{{source['year'] or 'n.d.'}}},\n"
                f"  url = {{{source['url'] or ''}}}\n"
                "}\n"
            )

        report_path = out / "report.md"
        bib_path = out / "bibliography.bib"
        trace_path = out / "execution_trace.json"
        report_path.write_text("\n".join(lines), encoding="utf-8")
        bib_path.write_text("\n".join(bib), encoding="utf-8")

        # Record the Archivist action before taking the final trace snapshot.
        self.board.send_message(
            run_id, None, "Archivist", "User", "inform",
            {
                "report": str(report_path),
                "bibliography": str(bib_path),
                "trace": str(trace_path),
                "accepted_claims": len(accepted_claims),
                "published_claims": len(published),
            },
        )
        self.board.log_event(
            run_id, "Archivist", "export_completed",
            {
                "output_dir": str(out),
                "accepted_claims": len(accepted_claims),
                "published_claims": len(published),
            },
        )

        final_trace = self.board.export_trace(run_id)
        trace_path.write_text(
            json.dumps(final_trace, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return out
