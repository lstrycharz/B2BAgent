"""Agent orchestrator: runs the full pipeline across all configured competitors."""

from dataclasses import dataclass
from typing import Any

from src.config import Competitor
from src.stages import (
    IntelligenceReport,
    extract_signals,
    fetch_competitor,
    render_digest,
)


@dataclass
class RunResult:
    """Output of a single agent run — the digest plus accounting info."""

    digest: str
    reports: dict[str, IntelligenceReport]
    total_input_tokens: int
    total_output_tokens: int


def run_once(
    client: Any,
    competitors: list[Competitor],
    model_id: str,
) -> RunResult:
    """Run the pipeline once across all competitors. Returns a RunResult with
    the rendered digest and token accounting. No deduplication yet (chunk 2)."""
    allowed_hosts = frozenset(_host_of(source.url) for c in competitors for source in c.sources)

    reports: dict[str, IntelligenceReport] = {}
    total_in = 0
    total_out = 0

    for competitor in competitors:
        sources = fetch_competitor(competitor, allowed_hosts=allowed_hosts)
        report, usage = extract_signals(
            client=client,
            competitor_name=competitor.name,
            sources=sources,
            model_id=model_id,
        )
        reports[competitor.name] = report
        total_in += usage["input_tokens"]
        total_out += usage["output_tokens"]

    return RunResult(
        digest=render_digest(reports),
        reports=reports,
        total_input_tokens=total_in,
        total_output_tokens=total_out,
    )


def _host_of(url: str) -> str:
    import httpx

    return httpx.URL(url).host
