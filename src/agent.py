"""Agent orchestrator: runs the full pipeline across all configured competitors.

Pipeline: fetch → extract → dedup (via SignalStore) → render. A per-run cost
cap aborts remaining competitors if the budget is exhausted mid-run; the
partial digest still renders so the marketer gets something useful.
"""

from dataclasses import dataclass, field
from typing import Any

import httpx

from src.config import DEFAULT_COST_CAP_USD, Competitor, usage_to_cost_usd
from src.stages import (
    IntelligenceReport,
    extract_signals,
    fetch_competitor,
    render_digest,
)
from src.state import SignalStore


@dataclass
class RunResult:
    """Output of a single agent run — the digest plus accounting info."""

    digest: str
    reports: dict[str, IntelligenceReport]
    total_input_tokens: int
    total_output_tokens: int
    aborted_competitors: list[str] = field(default_factory=list)


def run_once(
    client: Any,
    competitors: list[Competitor],
    model_id: str,
    store: SignalStore,
    cost_cap_usd: float = DEFAULT_COST_CAP_USD,
) -> RunResult:
    """Run the pipeline once across all competitors. Filters out signals
    already in `store`, marks new signals as seen, and returns the digest.

    If accumulated cost exceeds `cost_cap_usd` after any competitor, remaining
    competitors are aborted (their names are returned in `aborted_competitors`)
    and the partial digest still renders.
    """
    allowed_hosts = frozenset(httpx.URL(s.url).host for c in competitors for s in c.sources)

    reports: dict[str, IntelligenceReport] = {}
    aborted: list[str] = []
    total_in = 0
    total_out = 0
    accumulated_cost = 0.0

    for i, competitor in enumerate(competitors):
        if accumulated_cost >= cost_cap_usd:
            aborted.extend(c.name for c in competitors[i:])
            break

        sources = fetch_competitor(competitor, allowed_hosts=allowed_hosts)
        report, usage = extract_signals(
            client=client,
            competitor_name=competitor.name,
            sources=sources,
            model_id=model_id,
        )
        total_in += usage["input_tokens"]
        total_out += usage["output_tokens"]
        accumulated_cost += usage_to_cost_usd(usage["input_tokens"], usage["output_tokens"])
        reports[competitor.name] = _dedup_report(report, competitor.name, store)

    return RunResult(
        digest=render_digest(reports),
        reports=reports,
        total_input_tokens=total_in,
        total_output_tokens=total_out,
        aborted_competitors=aborted,
    )


def _dedup_report(
    report: IntelligenceReport,
    competitor_name: str,
    store: SignalStore,
) -> IntelligenceReport:
    """Filter signals to only those unseen, mark survivors as seen.

    If the model already returned zero signals (genuine quiet week), preserve
    its null_finding. If dedup itself emptied the list, explain that distinctly
    so the marketer doesn't think the competitor was quiet when really we just
    saw repeats.
    """
    if not report.signals:
        return report  # nothing to filter; preserve model's null_finding

    new_signals = [s for s in report.signals if store.is_new(s, competitor_name)]
    for s in new_signals:
        store.mark_seen(s, competitor_name)

    if not new_signals:
        return report.model_copy(
            update={
                "signals": [],
                "null_finding": (
                    f"All {len(report.signals)} signal(s) this run were already "
                    "surfaced previously."
                ),
            }
        )
    return report.model_copy(update={"signals": new_signals})
