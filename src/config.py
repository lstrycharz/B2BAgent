"""Static configuration for the competitive intelligence agent.

Chunk 3 scope: 5 project-management competitors selected in WORKFLOW_SELECTION.md,
each with a pricing-page source. Additional sources per competitor are added in
chunk 4.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    """One thing-to-monitor for a competitor (a page, a feed, etc.)."""

    kind: str
    url: str


@dataclass(frozen=True)
class Competitor:
    """A competitor and the sources we monitor for it."""

    name: str
    sources: list[Source]


DEFAULT_COMPETITORS: list[Competitor] = [
    Competitor(
        name="Linear",
        sources=[
            Source(kind="pricing", url="https://linear.app/pricing"),
            Source(kind="changelog", url="https://linear.app/changelog"),
        ],
    ),
    Competitor(
        name="Asana",
        sources=[
            Source(kind="pricing", url="https://asana.com/pricing"),
            Source(kind="blog_rss", url="https://blog.asana.com/feed/"),
        ],
    ),
    Competitor(
        name="Notion",
        sources=[
            Source(kind="pricing", url="https://www.notion.com/pricing"),
            Source(kind="releases", url="https://www.notion.com/releases"),
        ],
    ),
    Competitor(
        name="Monday",
        sources=[
            Source(kind="pricing", url="https://monday.com/pricing"),
            Source(kind="blog", url="https://monday.com/blog/"),
        ],
    ),
    Competitor(
        name="ClickUp",
        sources=[
            Source(kind="pricing", url="https://clickup.com/pricing"),
            Source(kind="blog", url="https://clickup.com/blog"),
        ],
    ),
]

# Safety net so a misconfig or runaway model output can't blow the budget.
# Sonnet 4.6 pricing as of 2026-05: $3 / MTok in, $15 / MTok out.
DEFAULT_COST_CAP_USD = 5.0
INPUT_PRICE_PER_MTOK_USD = 3.0
OUTPUT_PRICE_PER_MTOK_USD = 15.0


def usage_to_cost_usd(input_tokens: int, output_tokens: int) -> float:
    """Convert a usage dict to an estimated cost in USD."""
    return (
        input_tokens / 1_000_000 * INPUT_PRICE_PER_MTOK_USD
        + output_tokens / 1_000_000 * OUTPUT_PRICE_PER_MTOK_USD
    )
