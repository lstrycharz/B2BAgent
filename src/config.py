"""Static configuration for the competitive intelligence agent.

Chunk 1 scope: a single competitor (Linear) with a single source (pricing page).
Additional competitors and sources are added in later chunks per the Stage 3 plan.
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
]
