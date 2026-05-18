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


def test_default_competitors_includes_all_five_project_management_tools():
    """Chunk 3 scope: 5 competitors in the project-management category. The
    5 picks match the Stage 1 selection: Linear, Asana, Notion, Monday, ClickUp."""
    names = [c.name for c in DEFAULT_COMPETITORS]
    assert names == ["Linear", "Asana", "Notion", "Monday", "ClickUp"]


def test_every_competitor_has_a_pricing_source():
    for c in DEFAULT_COMPETITORS:
        kinds = [s.kind for s in c.sources]
        assert "pricing" in kinds, f"{c.name} must include a pricing source"


def test_chunk4_every_competitor_has_at_least_two_sources():
    """Chunk 4 scope: each competitor gets a pricing source plus one
    second source (changelog/blog/releases — whichever surfaces the most
    product-launch signal)."""
    for c in DEFAULT_COMPETITORS:
        assert len(c.sources) >= 2, f"{c.name} should have >= 2 sources in chunk 4"
