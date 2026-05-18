"""Pipeline stages: fetch competitor data → extract signals → render digest.

Each stage is a pure-ish function with clear inputs and outputs. The Anthropic
client is injected (not constructed here) so tests can pass a fake.
"""

from typing import Any

from pydantic import BaseModel, Field

from src.config import Competitor
from src.tools import fetch_with_guards, html_to_text

# --- Schemas ------------------------------------------------------------------


class Signal(BaseModel):
    """One competitive signal. The verbatim_quote field is the anti-hallucination guard."""

    signal_type: str = Field(
        description="One of: product_launch, pricing_change, hiring, positioning, content"
    )
    headline: str = Field(description="One-sentence summary, email-subject-line shaped")
    detail: str = Field(description="2-3 sentence explanation of what was observed and why it matters")
    verbatim_quote: str = Field(description="Direct quote from the source proving the signal is real")
    source_url: str = Field(description="URL where the signal was observed")
    significance: int = Field(ge=1, le=5, description="1=trivia, 3=worth knowing, 5=strategic")


class IntelligenceReport(BaseModel):
    competitor: str
    signals: list[Signal]
    null_finding: str | None = Field(
        default=None,
        description="If no signals worth surfacing, explain why",
    )


# --- Prompt -------------------------------------------------------------------

SYSTEM_PROMPT = """You are a senior B2B SaaS competitive intelligence analyst. You are reviewing fetched public data about a competitor to produce a daily intelligence digest for a marketing team.

Your job is to surface signals that would make a CMO say "I didn't know that, and it changes how I'm thinking." Skip generic observations.

Rules you must follow:
1. Every signal must be backed by a verbatim quote from the source data. If you cannot quote it, do not report it.
2. Significance ratings: 1 = trivia (skip unless slow week), 3 = worth knowing (informs positioning), 5 = strategic (changes battle cards, sales scripts, or roadmap discussions).
3. Prefer 0-3 high-signal items over 10 generic ones. Use `null_finding` if there is genuinely nothing of strategic interest.
4. Signal types: product_launch (new feature shipped), pricing_change (plan/price modified), hiring (key role posted that signals strategy), positioning (new messaging/category claim), content (notable new thought-leadership piece).
5. Be specific. "Linear added a new feature" is useless. "Linear shipped Cycles 2.0 with auto-rollover; targets engineering managers; quote: ..." is useful.

Submit your report via the submit_intelligence_report tool."""

_MAX_CHARS_PER_SOURCE = 30_000  # ~7.5k tokens per source

_EXTRACT_TOOL = {
    "name": "submit_intelligence_report",
    "description": "Submit the competitive intelligence report after analyzing the fetched data.",
    "input_schema": IntelligenceReport.model_json_schema(),
}


# --- Stages -------------------------------------------------------------------


def fetch_competitor(
    competitor: Competitor,
    allowed_hosts: frozenset[str] | set[str],
) -> list[dict[str, Any]]:
    """Fetch every source for a competitor. Returns one dict per source with the
    cleaned text and metadata. Sources that fail to fetch are skipped with a noted error."""
    results: list[dict[str, Any]] = []
    for source in competitor.sources:
        raw = fetch_with_guards(source.url, allowed_hosts)
        text = html_to_text(raw)
        results.append(
            {
                "kind": source.kind,
                "url": source.url,
                "text": text,
            }
        )
    return results


def extract_signals(
    client: Any,  # duck-typed: anything with .messages.create(...)
    competitor_name: str,
    sources: list[dict[str, Any]],
    model_id: str,
) -> tuple[IntelligenceReport, dict[str, int]]:
    """Send fetched source data to Claude and parse the structured response.

    Returns the validated report plus a usage dict (input_tokens, output_tokens).
    """
    source_blocks: list[str] = []
    for s in sources:
        text = s["text"]
        truncated = text[:_MAX_CHARS_PER_SOURCE]
        truncation_note = " [TRUNCATED]" if len(text) > _MAX_CHARS_PER_SOURCE else ""
        source_blocks.append(
            f"=== Source: {s['kind']} ===\n"
            f"URL: {s['url']}{truncation_note}\n\n"
            f"{truncated}"
        )

    user_message = (
        f"Competitor: {competitor_name}\n"
        f"Number of sources: {len(sources)}\n\n"
        + "\n\n".join(source_blocks)
    )

    response = client.messages.create(
        model=model_id,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[_EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "submit_intelligence_report"},
        messages=[{"role": "user", "content": user_message}],
    )

    tool_use = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_use is None:
        raise RuntimeError(f"Anthropic response had no tool_use block: {response.content!r}")

    report = IntelligenceReport.model_validate(tool_use.input)
    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    return report, usage


def render_digest(reports: dict[str, IntelligenceReport]) -> str:
    """Render a markdown digest across one or more competitor reports."""
    lines: list[str] = ["# Competitive Intelligence Digest", ""]
    for competitor, report in reports.items():
        lines.extend([f"## {competitor}", ""])
        if not report.signals:
            null_finding = report.null_finding or "(no reason provided)"
            lines.extend([f"*No signals worth surfacing.* {null_finding}", ""])
            continue
        ranked = sorted(report.signals, key=lambda s: -s.significance)
        for s in ranked:
            lines.extend(
                [
                    f"### [{s.significance}/5 — {s.signal_type}] {s.headline}",
                    "",
                    s.detail,
                    "",
                    f"> {s.verbatim_quote}",
                    "",
                    f"Source: {s.source_url}",
                    "",
                ]
            )
    return "\n".join(lines)
