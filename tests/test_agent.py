"""Tests for src/agent.py — orchestrates fetch → extract → render across competitors."""

from unittest.mock import MagicMock, patch

from src.agent import run_once
from src.config import Competitor, Source
from src.stages import IntelligenceReport, Signal


def _stub_report(name: str) -> IntelligenceReport:
    return IntelligenceReport(
        competitor=name,
        signals=[
            Signal(
                signal_type="product_launch",
                headline=f"{name} shipped Y",
                detail="-",
                verbatim_quote="-",
                source_url=f"https://{name.lower()}.app/x",
                significance=4,
            )
        ],
    )


@patch("src.agent.extract_signals")
@patch("src.agent.fetch_competitor")
def test_run_once_fetches_and_extracts_per_competitor(mock_fetch, mock_extract):
    mock_fetch.return_value = [{"kind": "pricing", "url": "https://linear.app/pricing", "text": "..."}]
    mock_extract.return_value = (_stub_report("Linear"), {"input_tokens": 100, "output_tokens": 50})

    competitors = [
        Competitor(name="Linear", sources=[Source(kind="pricing", url="https://linear.app/pricing")])
    ]
    result = run_once(client=MagicMock(), competitors=competitors, model_id="claude-sonnet-4-6")

    assert mock_fetch.call_count == 1
    assert mock_extract.call_count == 1
    assert "Linear" in result.digest
    assert "shipped Y" in result.digest
    assert result.total_input_tokens == 100
    assert result.total_output_tokens == 50
    assert result.reports["Linear"].signals[0].headline == "Linear shipped Y"


@patch("src.agent.extract_signals")
@patch("src.agent.fetch_competitor")
def test_run_once_accumulates_tokens_across_competitors(mock_fetch, mock_extract):
    mock_fetch.return_value = [{"kind": "pricing", "url": "x", "text": "y"}]
    mock_extract.side_effect = [
        (_stub_report("Linear"), {"input_tokens": 100, "output_tokens": 50}),
        (_stub_report("Asana"), {"input_tokens": 200, "output_tokens": 80}),
    ]
    competitors = [
        Competitor(name="Linear", sources=[Source(kind="pricing", url="https://linear.app/pricing")]),
        Competitor(name="Asana", sources=[Source(kind="pricing", url="https://asana.com/pricing")]),
    ]
    result = run_once(client=MagicMock(), competitors=competitors, model_id="claude-sonnet-4-6")
    assert result.total_input_tokens == 300
    assert result.total_output_tokens == 130
