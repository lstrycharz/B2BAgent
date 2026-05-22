"""Tests for src/state.py RunLog — per-run metadata for the monitoring dashboard."""

import pytest

from src.state import RunLog, RunRecord


def _record(run_id: str, started_at: str, status: str = "success", signals: int = 5) -> RunRecord:
    return RunRecord(
        run_id=run_id,
        started_at=started_at,
        status=status,
        competitors_processed=5,
        total_signals=signals,
        input_tokens=45000,
        output_tokens=5800,
        cost_usd=0.222,
        aborted_competitors="",
        error=None,
    )


@pytest.fixture
def log() -> RunLog:
    return RunLog(":memory:")


def test_record_then_recent_returns_the_run(log: RunLog):
    log.record(_record("r1", "2026-05-18T09:00:00+00:00"))
    runs = log.recent()
    assert len(runs) == 1
    assert runs[0].run_id == "r1"
    assert runs[0].total_signals == 5
    assert runs[0].cost_usd == pytest.approx(0.222)


def test_recent_returns_newest_first(log: RunLog):
    log.record(_record("old", "2026-05-16T09:00:00+00:00"))
    log.record(_record("mid", "2026-05-17T09:00:00+00:00"))
    log.record(_record("new", "2026-05-18T09:00:00+00:00"))
    runs = log.recent()
    assert [r.run_id for r in runs] == ["new", "mid", "old"]


def test_recent_respects_limit(log: RunLog):
    for i in range(10):
        log.record(_record(f"r{i}", f"2026-05-{10 + i:02d}T09:00:00+00:00"))
    assert len(log.recent(limit=3)) == 3


def test_error_run_round_trips_with_message(log: RunLog):
    rec = _record("err1", "2026-05-18T09:00:00+00:00", status="error")
    rec.error = "httpx.ConnectTimeout on monday.com"
    log.record(rec)
    fetched = log.recent()[0]
    assert fetched.status == "error"
    assert fetched.error == "httpx.ConnectTimeout on monday.com"


def test_record_is_idempotent_on_run_id(log: RunLog):
    """Re-recording the same run_id (e.g., a retried workflow step) must not
    create a duplicate row."""
    log.record(_record("r1", "2026-05-18T09:00:00+00:00"))
    log.record(_record("r1", "2026-05-18T09:00:00+00:00"))
    assert len(log.recent()) == 1


def test_runlog_persists_across_reopen(tmp_path):
    db_path = str(tmp_path / "state.db")
    log_a = RunLog(db_path)
    log_a.record(_record("r1", "2026-05-18T09:00:00+00:00"))
    log_a.close()

    log_b = RunLog(db_path)
    assert log_b.recent()[0].run_id == "r1"
    log_b.close()


def test_runlog_and_signalstore_coexist_in_same_db(tmp_path):
    """RunLog and SignalStore both wrap the same SQLite file — creating one
    must not break the other's schema."""
    from src.stages import Signal
    from src.state import SignalStore

    db_path = str(tmp_path / "state.db")
    store = SignalStore(db_path)
    log = RunLog(db_path)

    log.record(_record("r1", "2026-05-18T09:00:00+00:00"))
    sig = Signal(
        signal_type="product_launch",
        headline="X shipped Y",
        detail="-",
        verbatim_quote="-",
        source_url="https://x.com",
        significance=4,
    )
    store.mark_seen(sig, competitor="Linear")

    assert log.recent()[0].run_id == "r1"
    assert store.is_new(sig, competitor="Linear") is False
    store.close()
    log.close()
