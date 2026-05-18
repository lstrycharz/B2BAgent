"""SQLite-backed persistence of seen signals for week-over-week deduplication.

The store is intentionally deep: callers see two methods (`is_new`, `mark_seen`)
and never touch SQL. The hash function is exposed so callers can use it for
their own purposes (e.g., logging which key collided).
"""

import hashlib
import sqlite3
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
