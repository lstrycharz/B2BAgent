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
        sources=[Source(kind="pricing", url="https://linear.app/pricing")],
    ),
    Competitor(
        name="Asana",
        sources=[Source(kind="pricing", url="https://asana.com/pricing")],
    ),
    Competitor(
        name="Notion",
        sources=[Source(kind="pricing", url="https://www.notion.com/pricing")],
    ),
    Competitor(
        name="Monday",
        sources=[Source(kind="pricing", url="https://monday.com/pricing")],
    ),
    Competitor(
        name="ClickUp",
        sources=[Source(kind="pricing", url="https://clickup.com/pricing")],
    ),
]
