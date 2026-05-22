"""Pure-function metric computations for the monitoring dashboard.

No Streamlit, no I/O — just data in, summary out. This is the testable core;
dashboard.py renders whatever these return.
"""

from dataclasses import dataclass

from src.state import RunRecord

# A 'partial' run hit the cost cap but still produced a usable digest, so it
# counts as healthy. Only 'error' (run did not complete) is a failure.
_HEALTHY_STATUSES = {"success", "partial"}


@dataclass
class RunSummary:
    total_runs: int
    success_rate: float  # fraction of runs that were healthy (0.0–1.0)
    total_cost_usd: float
    avg_cost_usd: float
    total_signals: int


def summarize_runs(runs: list[RunRecord]) -> RunSummary:
    """Aggregate a list of runs into headline dashboard metrics."""
    if not runs:
        return RunSummary(
            total_runs=0,
            success_rate=0.0,
            total_cost_usd=0.0,
            avg_cost_usd=0.0,
            total_signals=0,
        )

    total = len(runs)
    healthy = sum(1 for r in runs if r.status in _HEALTHY_STATUSES)
    total_cost = sum(r.cost_usd for r in runs)
    return RunSummary(
        total_runs=total,
        success_rate=healthy / total,
        total_cost_usd=total_cost,
        avg_cost_usd=total_cost / total,
        total_signals=sum(r.total_signals for r in runs),
    )
