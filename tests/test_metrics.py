"""Tests for monitoring/metrics.py — pure-function metric computations.

These are the testable core of the dashboard; the Streamlit layer just renders
whatever these return."""

import pytest

from monitoring.metrics import summarize_runs
from src.state import RunRecord


def _run(run_id: str, status: str, cost: float, signals: int = 5) -> RunRecord:
    return RunRecord(
        run_id=run_id,
        started_at="2026-05-18T09:00:00+00:00",
        status=status,
        competitors_processed=5,
        total_signals=signals,
        input_tokens=45000,
        output_tokens=5800,
        cost_usd=cost,
        aborted_competitors="",
        error=None,
    )


def test_summarize_empty_runs_returns_zeros_without_dividing_by_zero():
    s = summarize_runs([])
    assert s.total_runs == 0
    assert s.success_rate == 0.0
    assert s.total_cost_usd == 0.0
    assert s.avg_cost_usd == 0.0


def test_summarize_counts_total_runs():
    runs = [_run("a", "success", 0.20), _run("b", "success", 0.22)]
    assert summarize_runs(runs).total_runs == 2


def test_success_rate_treats_partial_as_success():
    """A cost-capped 'partial' run still produced a usable digest — it counts
    as a healthy run for the success-rate metric. Only 'error' is a failure."""
    runs = [
        _run("a", "success", 0.20),
        _run("b", "partial", 0.21),
        _run("c", "error", 0.0),
        _run("d", "success", 0.22),
    ]
    # 3 of 4 healthy (success + partial)
    assert summarize_runs(runs).success_rate == pytest.approx(0.75)


def test_total_and_average_cost():
    runs = [_run("a", "success", 0.20), _run("b", "success", 0.30)]
    s = summarize_runs(runs)
    assert s.total_cost_usd == pytest.approx(0.50)
    assert s.avg_cost_usd == pytest.approx(0.25)


def test_total_signals_summed():
    runs = [_run("a", "success", 0.2, signals=10), _run("b", "success", 0.2, signals=7)]
    assert summarize_runs(runs).total_signals == 17
