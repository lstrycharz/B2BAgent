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
    """Chunk 3 scope: 5 competitors in the project-management category, each
    with one pricing-page source. Additional sources per competitor are added
    in chunk 4. The 5 picks match the Stage 1 selection: Linear, Asana,
    Notion, Monday, ClickUp."""
    names = [c.name for c in DEFAULT_COMPETITORS]
    assert names == ["Linear", "Asana", "Notion", "Monday", "ClickUp"]

    for competitor in DEFAULT_COMPETITORS:
        assert len(competitor.sources) == 1, f"{competitor.name} should have 1 source in chunk 3"
        assert competitor.sources[0].kind == "pricing"
        assert competitor.sources[0].url.startswith("https://")


def test_default_competitor_urls_are_the_expected_pricing_pages():
    urls = {c.name: c.sources[0].url for c in DEFAULT_COMPETITORS}
    assert urls == {
        "Linear": "https://linear.app/pricing",
        "Asana": "https://asana.com/pricing",
        "Notion": "https://www.notion.com/pricing",
        "Monday": "https://monday.com/pricing",
        "ClickUp": "https://clickup.com/pricing",
    }
