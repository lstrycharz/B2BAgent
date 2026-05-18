"""Tests for src/config.py — competitor configuration data structures."""

from src.config import DEFAULT_COMPETITORS, Competitor, Source


def test_source_holds_kind_and_url():
    source = Source(kind="pricing", url="https://linear.app/pricing")
    assert source.kind == "pricing"
    assert source.url == "https://linear.app/pricing"


def test_competitor_holds_name_and_sources():
    competitor = Competitor(
        name="Linear",
        sources=[Source(kind="pricing", url="https://linear.app/pricing")],
    )
    assert competitor.name == "Linear"
    assert len(competitor.sources) == 1
    assert competitor.sources[0].kind == "pricing"


def test_default_competitors_chunk1_only_includes_linear_pricing():
    """Chunk 1 scope: a single competitor with a single source. Other competitors
    are added in chunk 3, additional sources in chunk 4."""
    assert len(DEFAULT_COMPETITORS) == 1
    linear = DEFAULT_COMPETITORS[0]
    assert linear.name == "Linear"
    assert len(linear.sources) == 1
    assert linear.sources[0].kind == "pricing"
    assert linear.sources[0].url == "https://linear.app/pricing"
