from __future__ import annotations
import sqlite3
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from .models import Task, SourceRecord, Claim, Verdict

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    task_key TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    attempt INTEGER NOT NULL DEFAULT 0,
    UNIQUE(run_id, task_key),
    FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    stable_id TEXT NOT NULL,
    title TEXT NOT NULL,
    authors TEXT,
    year INTEGER,
    abstract TEXT,
    doi TEXT,
    arxiv_id TEXT,
    source_api TEXT NOT NULL,
    url TEXT,
    relevance REAL NOT NULL DEFAULT 0,
    UNIQUE(run_id, task_id, stable_id),
    FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    evidence TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY(source_id) REFERENCES sources(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS verdicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER NOT NULL,
    label TEXT NOT NULL,
    confidence REAL NOT NULL,
    rationale TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(claim_id) REFERENCES claims(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    task_id INTEGER,
    sender TEXT NOT NULL,
    receiver TEXT NOT NULL,
    performative TEXT NOT NULL,
    content_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    agent TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
);
"""

class Blackboard:
    """SQLite shared blackboard used by all agents."""

    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def create_run(self, goal: str) -> int:
        if not goal.strip():
            raise ValueError("goal must not be empty")
        cur = self.conn.execute(
            "INSERT INTO runs(goal, status) VALUES (?, ?)", (goal.strip(), "running")
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def set_run_status(self, run_id: int, status: str) -> None:
        if status in {"completed", "failed"}:
            self.conn.execute(
                "UPDATE runs SET status=?, finished_at=CURRENT_TIMESTAMP WHERE id=?",
                (status, run_id),
            )
        else:
            self.conn.execute("UPDATE runs SET status=? WHERE id=?", (status, run_id))
        self.conn.commit()

    def add_task(self, task: Task) -> int:
        task.validate()
        cur = self.conn.execute(
            """INSERT OR IGNORE INTO tasks(run_id, task_key, description, status, attempt)
               VALUES (?, ?, ?, ?, ?)""",
            (task.run_id, task.task_key, task.description, task.status, task.attempt),
        )
        self.conn.commit()
        if cur.lastrowid:
            return int(cur.lastrowid)
        row = self.conn.execute(
            "SELECT id FROM tasks WHERE run_id=? AND task_key=?",
            (task.run_id, task.task_key),
        ).fetchone()
        return int(row["id"])

    def update_task(self, task_id: int, *, status: Optional[str] = None,
                    attempt: Optional[int] = None, description: Optional[str] = None) -> None:
        updates, values = [], []
        if status is not None:
            updates.append("status=?"); values.append(status)
        if attempt is not None:
            updates.append("attempt=?"); values.append(attempt)
        if description is not None:
            updates.append("description=?"); values.append(description)
        if not updates:
            return
        values.append(task_id)
        self.conn.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id=?", values)
        self.conn.commit()

    def get_tasks(self, run_id: int) -> List[sqlite3.Row]:
        return list(self.conn.execute(
            "SELECT * FROM tasks WHERE run_id=? ORDER BY id", (run_id,)
        ))

    def add_source(self, source: SourceRecord) -> int:
        cur = self.conn.execute(
            """INSERT OR IGNORE INTO sources(
               run_id, task_id, stable_id, title, authors, year, abstract,
               doi, arxiv_id, source_api, url, relevance)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                source.run_id, source.task_id, source.stable_id, source.title,
                source.authors, source.year, source.abstract, source.doi,
                source.arxiv_id, source.source_api, source.url, source.relevance
            ),
        )
        self.conn.commit()
        if cur.lastrowid:
            return int(cur.lastrowid)
        row = self.conn.execute(
            "SELECT id FROM sources WHERE run_id=? AND task_id=? AND stable_id=?",
            (source.run_id, source.task_id, source.stable_id),
        ).fetchone()
        return int(row["id"])

    def get_sources(self, task_id: int) -> List[sqlite3.Row]:
        return list(self.conn.execute(
            "SELECT * FROM sources WHERE task_id=? ORDER BY relevance DESC, id",
            (task_id,),
        ))

    def add_claim(self, claim: Claim) -> int:
        cur = self.conn.execute(
            """INSERT INTO claims(run_id, task_id, source_id, text, evidence, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (claim.run_id, claim.task_id, claim.source_id, claim.text, claim.evidence, claim.status),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def get_claims(self, task_id: int) -> List[sqlite3.Row]:
        return list(self.conn.execute(
            "SELECT * FROM claims WHERE task_id=? ORDER BY id", (task_id,)
        ))

    def set_claim_status(self, claim_id: int, status: str) -> None:
        self.conn.execute("UPDATE claims SET status=? WHERE id=?", (status, claim_id))
        self.conn.commit()

    def add_verdict(self, verdict: Verdict) -> int:
        verdict.validate()
        cur = self.conn.execute(
            """INSERT INTO verdicts(claim_id, label, confidence, rationale)
               VALUES (?, ?, ?, ?)""",
            (verdict.claim_id, verdict.label, verdict.confidence, verdict.rationale),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def get_supported_claims(self, run_id: int) -> List[sqlite3.Row]:
        return list(self.conn.execute(
            """SELECT c.*, s.title, s.abstract, s.doi, s.arxiv_id, s.url,
                      s.source_api, s.relevance
               FROM claims c
               JOIN sources s ON s.id=c.source_id
               WHERE c.run_id=? AND c.status='accepted'
               ORDER BY c.task_id, c.id""",
            (run_id,),
        ))

    def add_feedback(self, run_id: int, task_id: int, message: str) -> None:
        self.conn.execute(
            "INSERT INTO feedback(run_id, task_id, message) VALUES (?, ?, ?)",
            (run_id, task_id, message),
        )
        self.conn.commit()

    def get_feedback(self, task_id: int) -> List[str]:
        rows = self.conn.execute(
            "SELECT message FROM feedback WHERE task_id=? ORDER BY id", (task_id,)
        ).fetchall()
        return [r["message"] for r in rows]

    def send_message(self, run_id: int, task_id: Optional[int], sender: str,
                     receiver: str, performative: str, content: Dict[str, Any]) -> None:
        # KQML-inspired performatives preserve Unit 6 communication semantics
        # without hiding the assessed control loop inside a framework.
        self.conn.execute(
            """INSERT INTO messages(run_id, task_id, sender, receiver, performative, content_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (run_id, task_id, sender, receiver, performative,
             json.dumps(content, ensure_ascii=False)),
        )
        self.conn.commit()

    def log_event(self, run_id: int, agent: str, event_type: str,
                  payload: Dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT INTO events(run_id, agent, event_type, payload_json) VALUES (?, ?, ?, ?)",
            (run_id, agent, event_type, json.dumps(payload, ensure_ascii=False)),
        )
        self.conn.commit()

    def export_trace(self, run_id: int) -> Dict[str, Any]:
        run = self.conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        tasks = [dict(r) for r in self.get_tasks(run_id)]
        sources = [dict(r) for r in self.conn.execute(
            "SELECT * FROM sources WHERE run_id=? ORDER BY id", (run_id,)
        )]
        claims = [dict(r) for r in self.conn.execute(
            "SELECT * FROM claims WHERE run_id=? ORDER BY id", (run_id,)
        )]
        verdicts = [dict(r) for r in self.conn.execute(
            """SELECT v.* FROM verdicts v JOIN claims c ON c.id=v.claim_id
               WHERE c.run_id=? ORDER BY v.id""", (run_id,)
        )]
        feedback = [dict(r) for r in self.conn.execute(
            "SELECT * FROM feedback WHERE run_id=? ORDER BY id", (run_id,)
        )]
        messages = [dict(r) for r in self.conn.execute(
            "SELECT * FROM messages WHERE run_id=? ORDER BY id", (run_id,)
        )]
        events = [dict(r) for r in self.conn.execute(
            "SELECT * FROM events WHERE run_id=? ORDER BY id", (run_id,)
        )]
        return {
            "run": dict(run) if run else None,
            "tasks": tasks,
            "sources": sources,
            "claims": claims,
            "verdicts": verdicts,
            "feedback": feedback,
            "messages": messages,
            "events": events,
        }
