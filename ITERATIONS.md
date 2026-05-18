# Iterations Log

Every meaningful change made to the agent (or its surrounding process) **after** Stage 3 launched. Each entry follows the same structure: hypothesis → change → measured effect → decision. The discipline is to never rely on "it feels better"; if a change can't be measured, name what you couldn't measure and flag it as such.

Process iterations and agent-behavior iterations are both logged here. They're equally valid PM/engineering learning.

---

## Iteration #1 — Lighten Phase 1 Shadow protocol for solo-project scale (process)

- **Date:** 2026-05-18
- **Trigger:** First attempt to follow the original Phase 1 protocol (per-signal grading of 21 signals + daily file commits) felt tedious within the first attempt. That tediousness is data: real friction means the protocol is wrong for the context.
- **Hypothesis:** The original Phase 1 protocol was implicitly scaled for a team context where shipping a bad digest embarrasses you in front of a stakeholder. For a solo learning project where you are the only recipient, that risk doesn't exist yet — making the daily ceremony pure cost with no benefit. A lean version (skim daily, one consolidated review at end of day 3) preserves the core protections (hallucination check, relevance feel, run reliability) at ~10% of the time cost.
- **Change:**
  - `ROLLOUT_PLAN.md` Phase 1 section rewritten: drop per-signal grading, replace with end-of-day-3 consolidated review.
  - Deleted `rollout/phase1_shadow/_template.md` (daily) and the pre-filled `2026-05-18.md` annotation file.
  - Added `rollout/phase1_shadow/_review.md` (one-time consolidated review).
- **Measured effect:**
  - Time-on-protocol: 10 min × 3 days = 30 min (old) → 2 min × 3 days + 10 min review = 16 min (new). ~50% reduction.
  - Hallucination check: preserved (1 spot-check at end of phase vs. 3 spot-checks during phase).
  - Per-signal relevance data: lost (was: 21 × 3 = 63 graded signals; now: gut-feel summary). Trade-off accepted.
- **Decision:** Adopt the lean version. The protocol exists to manage risk; with no team and no stakeholders, the risk surface is small enough to justify the lighter touch.
- **Lesson worth keeping:** *Match protocol weight to actual blast radius.* The reason most engineers skip lifecycle ceremony isn't laziness — it's that the textbook version is sized for contexts they're not in. Right-sizing is the actual PM skill, not following the recipe.

---

<!-- Future iterations queued (from KNOWN_LIMITATIONS.md and Phase 1 review):

## Iteration #2 — Semantic dedup (agent behavior)
- Hypothesis: hash-based dedup misses paraphrased signals (~95% miss rate in back-to-back tests, per L-1)
- Test data: Wayback Machine snapshots of competitor pricing pages at 3 historical points
- Proposed change: embeddings + cosine similarity threshold, OR Claude-as-judge
- See KNOWN_LIMITATIONS.md L-1 for full plan.

(more queued as we hit them) -->
