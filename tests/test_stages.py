"""Tests for src/stages.py — fetch, extract, render stages."""

from unittest.mock import MagicMock

import httpx
import respx

from src.config import Competitor, Source
from src.stages import (
    IntelligenceReport,
    Signal,
    extract_signals,
    fetch_competitor,
    render_digest,
)


# --- Schema tests --------------------------------------------------------------

def test_signal_requires_verbatim_quote():
    """Anti-hallucination guard: every signal must include a quote from the source."""
    s = Signal(
        signal_type="product_launch",
        headline="X shipped Y",
        detail="Why it matters.",
        verbatim_quote="We are excited to announce Y.",
        source_url="https://example.com/page",
        significance=4,
    )
    assert s.verbatim_quote == "We are excited to announce Y."


def test_intelligence_report_allows_zero_signals_with_null_finding():
    """A quiet week is valid — the model can report no signals if it justifies why."""
    r = IntelligenceReport(competitor="Linear", signals=[], null_finding="Quiet week.")
    assert r.signals == []
    assert r.null_finding == "Quiet week."


# --- fetch_competitor ---------------------------------------------------------

@respx.mock
def test_fetch_competitor_returns_one_entry_per_source():
    respx.get("https://linear.app/pricing").mock(
        return_value=httpx.Response(200, text="<html><body><h1>Pricing</h1></body></html>")
    )
    competitor = Competitor(
        name="Linear",
        sources=[Source(kind="pricing", url="https://linear.app/pricing")],
    )
    results = fetch_competitor(competitor, allowed_hosts=frozenset({"linear.app"}))
    assert len(results) == 1
    assert results[0]["kind"] == "pricing"
    assert results[0]["url"] == "https://linear.app/pricing"
    assert "Pricing" in results[0]["text"]


# --- extract_signals ----------------------------------------------------------

def _fake_anthropic_response(tool_input: dict, input_tokens: int = 100, output_tokens: int = 50):
    """Build a MagicMock that mimics the shape of an Anthropic messages.create response."""
    tool_use = MagicMock()
    tool_use.type = "tool_use"
    tool_use.input = tool_input
    response = MagicMock()
    response.content = [tool_use]
    response.usage.input_tokens = input_tokens
    response.usage.output_tokens = output_tokens
    return response


def test_extract_signals_returns_parsed_report_and_usage():
    fake_tool_input = {
        "competitor": "Linear",
        "signals": [
            {
                "signal_type": "product_launch",
                "headline": "Linear ships Cycles 2.0",
                "detail": "Auto-rollover for engineering managers.",
                "verbatim_quote": "Introducing Cycles 2.0 with auto-rollover.",
                "source_url": "https://linear.app/changelog",
                "significance": 5,
            }
        ],
        "null_finding": None,
    }
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_anthropic_response(
        fake_tool_input, input_tokens=8000, output_tokens=400
    )

    sources = [{"kind": "pricing", "url": "https://linear.app/pricing", "text": "Linear pricing $10/user"}]
    report, usage = extract_signals(
        client=fake_client,
        competitor_name="Linear",
        sources=sources,
        model_id="claude-sonnet-4-6",
    )

    assert report.competitor == "Linear"
    assert len(report.signals) == 1
    assert report.signals[0].headline == "Linear ships Cycles 2.0"
    assert usage == {"input_tokens": 8000, "output_tokens": 400}


def test_extract_signals_uses_temperature_zero_for_determinism():
    """Without this, the same competitor data produces differently-phrased
    signals on each run, defeating the dedup hash."""
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_anthropic_response(
        {"competitor": "Linear", "signals": [], "null_finding": "Quiet."}
    )
    extract_signals(
        client=fake_client,
        competitor_name="Linear",
        sources=[{"kind": "pricing", "url": "x", "text": "y"}],
        model_id="claude-sonnet-4-6",
    )
    assert fake_client.messages.create.call_args.kwargs["temperature"] == 0


def test_extract_signals_sends_competitor_and_sources_in_user_message():
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_anthropic_response(
        {"competitor": "Linear", "signals": [], "null_finding": "Quiet."}
    )
    sources = [{"kind": "pricing", "url": "https://linear.app/pricing", "text": "page text here"}]
    extract_signals(
        client=fake_client,
        competitor_name="Linear",
        sources=sources,
        model_id="claude-sonnet-4-6",
    )
    call_kwargs = fake_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-sonnet-4-6"
    user_message = call_kwargs["messages"][0]["content"]
    assert "Linear" in user_message
    assert "page text here" in user_message
    # Strict output contract: tool_choice forces structured output
    assert call_kwargs["tool_choice"]["type"] == "tool"


# --- render_digest ------------------------------------------------------------

def test_render_digest_orders_signals_by_significance_descending():
    report = IntelligenceReport(
        competitor="Linear",
        signals=[
            Signal(
                signal_type="content",
                headline="LOW item",
                detail="-",
                verbatim_quote="-",
                source_url="https://linear.app/x",
                significance=2,
            ),
            Signal(
                signal_type="product_launch",
                headline="HIGH item",
                detail="-",
                verbatim_quote="-",
                source_url="https://linear.app/y",
                significance=5,
            ),
        ],
    )
    digest = render_digest({"Linear": report})
    assert digest.index("HIGH item") < digest.index("LOW item")


def test_render_digest_shows_null_finding_when_no_signals():
    report = IntelligenceReport(competitor="Linear", signals=[], null_finding="Quiet week.")
    digest = render_digest({"Linear": report})
    assert "Quiet week." in digest
