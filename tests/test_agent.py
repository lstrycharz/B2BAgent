"""Tests for src/agent.py — orchestrates fetch → extract → dedup → render."""

from unittest.mock import MagicMock, patch

import pytest

from src.agent import run_once
from src.config import Competitor, Source
from src.stages import IntelligenceReport, Signal
from src.state import SignalStore


def _stub_report(name: str) -> IntelligenceReport:
    return IntelligenceReport(
        competitor=name,
        signals=[
            Signal(
                signal_type="product_launch",
                headline=f"{name} shipped Y",
                detail="-",
                verbatim_quote=f"{name}-quote-text",
                source_url=f"https://{name.lower()}.app/x",
                significance=4,
            )
        ],
    )


@pytest.fixture
def store() -> SignalStore:
    return SignalStore(":memory:")


@patch("src.agent.extract_signals")
@patch("src.agent.fetch_competitor")
def test_run_once_fetches_and_extracts_per_competitor(mock_fetch, mock_extract, store):
    mock_fetch.return_value = [{"kind": "pricing", "url": "https://linear.app/pricing", "text": "..."}]
    mock_extract.return_value = (_stub_report("Linear"), {"input_tokens": 100, "output_tokens": 50})

    competitors = [
        Competitor(name="Linear", sources=[Source(kind="pricing", url="https://linear.app/pricing")])
    ]
    result = run_once(
        client=MagicMock(), competitors=competitors, model_id="claude-sonnet-4-6", store=store
    )

    assert mock_fetch.call_count == 1
    assert mock_extract.call_count == 1
    assert "Linear" in result.digest
    assert "shipped Y" in result.digest
    assert result.total_input_tokens == 100
    assert result.total_output_tokens == 50
    assert result.reports["Linear"].signals[0].headline == "Linear shipped Y"


@patch("src.agent.extract_signals")
@patch("src.agent.fetch_competitor")
def test_run_once_accumulates_tokens_across_competitors(mock_fetch, mock_extract, store):
    mock_fetch.return_value = [{"kind": "pricing", "url": "x", "text": "y"}]
    mock_extract.side_effect = [
        (_stub_report("Linear"), {"input_tokens": 100, "output_tokens": 50}),
        (_stub_report("Asana"), {"input_tokens": 200, "output_tokens": 80}),
    ]
    competitors = [
        Competitor(name="Linear", sources=[Source(kind="pricing", url="https://linear.app/pricing")]),
        Competitor(name="Asana", sources=[Source(kind="pricing", url="https://asana.com/pricing")]),
    ]
    result = run_once(
        client=MagicMock(), competitors=competitors, model_id="claude-sonnet-4-6", store=store
    )
    assert result.total_input_tokens == 300
    assert result.total_output_tokens == 130


@patch("src.agent.extract_signals")
@patch("src.agent.fetch_competitor")
def test_run_once_filters_out_signals_already_in_store(mock_fetch, mock_extract, store):
    """Second consecutive run with identical signals should report zero new ones."""
    mock_fetch.return_value = [{"kind": "pricing", "url": "x", "text": "y"}]
    mock_extract.return_value = (_stub_report("Linear"), {"input_tokens": 100, "output_tokens": 50})

    competitors = [
        Competitor(name="Linear", sources=[Source(kind="pricing", url="https://linear.app/pricing")])
    ]
    first = run_once(
        client=MagicMock(), competitors=competitors, model_id="claude-sonnet-4-6", store=store
    )
    assert len(first.reports["Linear"].signals) == 1  # 1 new signal

    # Same stub, same store — should be deduplicated
    second = run_once(
        client=MagicMock(), competitors=competitors, model_id="claude-sonnet-4-6", store=store
    )
    assert len(second.reports["Linear"].signals) == 0
    # null_finding should explain why the report is empty
    assert second.reports["Linear"].null_finding is not None
    assert "already" in second.reports["Linear"].null_finding.lower()


@patch("src.agent.extract_signals")
@patch("src.agent.fetch_competitor")
def test_run_once_preserves_original_null_finding_when_extraction_returned_zero(
    mock_fetch, mock_extract, store
):
    """If Claude itself returned zero signals (genuine quiet week), do NOT
    overwrite its null_finding with the dedup message."""
    mock_fetch.return_value = [{"kind": "pricing", "url": "x", "text": "y"}]
    empty_report = IntelligenceReport(
        competitor="Linear", signals=[], null_finding="Genuinely quiet week."
    )
    mock_extract.return_value = (empty_report, {"input_tokens": 100, "output_tokens": 50})

    competitors = [
        Competitor(name="Linear", sources=[Source(kind="pricing", url="https://linear.app/pricing")])
    ]
    result = run_once(
        client=MagicMock(), competitors=competitors, model_id="claude-sonnet-4-6", store=store
    )
    assert result.reports["Linear"].null_finding == "Genuinely quiet week."
