"""SQLite-backed persistence for the agent.

Two concerns, two classes, one file (the database wrapper is one deep module):
- SignalStore — seen-signal deduplication across runs.
- RunLog — per-run metadata (status, cost, tokens) for the monitoring dashboard.

Callers never touch SQL.
"""

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

from src.stages import Signal

_SCHEMA = """
CREATE TABLE IF NOT EXISTS seen_signals (
    hash TEXT PRIMARY KEY,
    competitor TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    headline TEXT NOT NULL,
    first_seen_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_seen_competitor ON seen_signals(competitor);
"""


def signal_hash(signal: Signal, competitor: str) -> str:
    """Stable dedup key. Hash material is competitor + signal_type + normalized
    headline only — the verbatim_quote is excluded because the model picks
    slightly different quote spans across runs even at temperature=0, which
    would defeat the dedup. Trade-off: two genuinely-different signals that
    happen to share a headline will collide; acceptable for digest scope.

    Worth revisiting in Stage 6 (semantic similarity via embeddings) if
    real-world false-collision rate proves too high.
    """
    normalized_headline = " ".join(signal.headline.split()).casefold()
    material = f"{competitor}|{signal.signal_type}|{normalized_headline}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class SignalStore:
    """Append-only store of signals we have already surfaced. Reopening the same
    file resumes previous state; using ':memory:' gives a clean store per test."""

    def __init__(self, db_path: str) -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def is_new(self, signal: Signal, competitor: str) -> bool:
        cursor = self._conn.execute(
            "SELECT 1 FROM seen_signals WHERE hash = ?",
            (signal_hash(signal, competitor),),
        )
        return cursor.fetchone() is None

    def mark_seen(self, signal: Signal, competitor: str) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO seen_signals "
            "(hash, competitor, signal_type, headline, first_seen_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                signal_hash(signal, competitor),
                competitor,
                signal.signal_type,
                signal.headline,
                datetime.now(UTC).isoformat(),
            ),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


# --- Run logging --------------------------------------------------------------

_RUNS_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    status TEXT NOT NULL,
    competitors_processed INTEGER NOT NULL,
    total_signals INTEGER NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_usd REAL NOT NULL,
    aborted_competitors TEXT NOT NULL,
    error TEXT
);
CREATE INDEX IF NOT EXISTS idx_runs_started_at ON runs(started_at);
"""


@dataclass
class RunRecord:
    """One agent run's metadata. status is 'success', 'partial' (cost cap hit
    or some competitors failed), or 'error' (run did not complete)."""

    run_id: str
    started_at: str  # ISO 8601
    status: str
    competitors_processed: int
    total_signals: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    aborted_competitors: str  # comma-joined, "" if none
    error: str | None = None


class RunLog:
    """Append-only log of agent runs. The monitoring dashboard reads from here.

    Shares the same SQLite file as SignalStore but owns a separate table — both
    classes call CREATE TABLE IF NOT EXISTS, so either can be constructed first.
    """

    def __init__(self, db_path: str) -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.executescript(_RUNS_SCHEMA)
        self._conn.commit()

    def record(self, run: RunRecord) -> None:
        """Insert a run. Idempotent on run_id (a retried step won't duplicate)."""
        self._conn.execute(
            "INSERT OR REPLACE INTO runs "
            "(run_id, started_at, status, competitors_processed, total_signals, "
            "input_tokens, output_tokens, cost_usd, aborted_competitors, error) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                run.run_id,
                run.started_at,
                run.status,
                run.competitors_processed,
                run.total_signals,
                run.input_tokens,
                run.output_tokens,
                run.cost_usd,
                run.aborted_competitors,
                run.error,
            ),
        )
        self._conn.commit()

    def recent(self, limit: int = 30) -> list[RunRecord]:
        """Return the most recent runs, newest first."""
        rows = self._conn.execute(
            "SELECT run_id, started_at, status, competitors_processed, total_signals, "
            "input_tokens, output_tokens, cost_usd, aborted_competitors, error "
            "FROM runs ORDER BY started_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            RunRecord(
                run_id=r[0],
                started_at=r[1],
                status=r[2],
                competitors_processed=r[3],
                total_signals=r[4],
                input_tokens=r[5],
                output_tokens=r[6],
                cost_usd=r[7],
                aborted_competitors=r[8],
                error=r[9],
            )
            for r in rows
        ]

    def close(self) -> None:
        self._conn.close()
