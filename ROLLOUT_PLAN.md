# Stage 4: Phased Rollout Plan

## Context

The agent is built and runs successfully in production (GitHub Actions cron, daily 09:00 UTC). Before letting it run **autonomously**, we put it through 4 gated phases. Each phase has explicit go/no-go criteria — none of "it feels ready, let's ship." The phases trade the cost of waiting for the value of catching real-world failure modes (a competitor changes their HTML structure, the LLM produces a fabricated signal, the cron times out) that no amount of pre-production testing would catch.

This is the lifecycle muscle most engineers skip. The whole point of building the agent in 6 small chunks was to *earn the right* to go through this phase carefully, not bypass it.

**Evidence directory:** [`rollout/`](rollout/) — one subdirectory per phase, populated with copies of digests, the human review notes, and the graduation decision.

---

## Phase 1 — Shadow (lean, solo-project version)

**Duration:** 3 days (target start: 2026-05-18 → graduate no earlier than 2026-05-21).

**Why "lean":** The original Phase 1 protocol (per-signal grading × 21 signals × 3 days) was scaled for a team where shipping a bad digest embarrasses you in front of a stakeholder. For a solo learning project where you're the only recipient, that risk doesn't exist yet. Right-sizing the discipline to the actual blast radius is itself the PM lesson — see [ITERATIONS.md](ITERATIONS.md) Iteration #1 for the explicit decision.

**Behavior:** Agent runs daily as scheduled. You read the digest casually (workflow log or email if working). No per-signal grading. **You do not forward the digest to anyone.**

**Daily ritual (≤ 2 min):** open the digest. Skim. Notice anything obviously wrong. Move on.

**End-of-day-3 consolidated review (≤ 10 min, one pass over all 3 digests together):**

Fill in [`rollout/phase1_shadow/_review.md`](rollout/phase1_shadow/_review.md) — three questions:

1. **Relevance gut-check:** of all the signals across 3 digests, roughly what fraction felt useful? ("most", "about half", "less than half")
2. **Hallucination check:** pick **one** signal from any of the 3 digests. Open its source URL. Search for the verbatim quote. Was it actually there?
3. **Systematic patterns:** anything that systematically annoyed you (repeated near-duplicates, off-target rankings, missing intel about a known competitor move)? These become Stage 6 iteration candidates.

**Go / no-go criteria:**
- [ ] **Relevance feels ≥ 70%** ("most" of the signals were useful).
- [ ] **Hallucination check passes** — the spot-checked quote is verbatim in the source.
- [ ] **Run reliability** — 3 consecutive successful workflow runs (check via `gh run list --limit 5`).

**No-go action:** if relevance is low or you found a hallucination, log the specific failure mode in [ITERATIONS.md](ITERATIONS.md) as a real iteration item, address it (tighten the prompt, fix the failing source, etc.), then re-shadow for 2 more days.

---

## Phase 2 — Suggested

**Duration:** 3–4 days minimum.

**Behavior:** Agent sends digests to you + 1 simulated stakeholder (use a second email address you control, or share the GitHub Actions workflow log link with a colleague). Subject prefixed `[SUGGESTED — review before sharing]`. You and the stakeholder review and decide what they would forward.

**Go / no-go criteria:**
- [ ] Stakeholder finds **≥ 1 insight they did not already know** across the phase (logged with a brief "I would have used this for X" note).
- [ ] **No critical errors:** no fabricated competitor moves, no signals that misattribute one competitor's move to another.
- [ ] Review time **≤ 15 min per digest** (anything slower means the digest is not yet useful as-shipped — needs better signal density or clearer formatting).

**No-go action:** refine the prompt (more aggressive significance rubric, stricter quoting), gather written feedback from the stakeholder, stay in Phase 2.

---

## Phase 3 — Approved

**Duration:** 3–4 days minimum.

**Behavior:** Digest goes directly to the broader marketing distribution (no `[SUGGESTED]` prefix). The recipients can read and act on it as authoritative.

**Go / no-go criteria:**
- [ ] **Team acts on ≥ 1 signal** (e.g., update to a competitive positioning doc, mention in a sales call, change to a battle card). Log the action.
- [ ] **No false alarms:** no signal that misled the team into preparing for a non-event.
- [ ] **Digest clarity:** team does not need to fact-check details from the digest itself before acting.

**No-go action:** roll back to Phase 2 (Suggested) until digest quality is consistent enough that recipients trust it without verification.

---

## Phase 4 — Autonomous

**Duration:** ongoing (no graduation; this is the steady state).

**Behavior:** No human review gate between agent and recipients. Stage 5 monitoring dashboard + alerts catch regressions.

**Continuous success criteria (checked weekly via the monitoring dashboard):**
- [ ] **ROI check:** the 20h/week of manual competitive monitoring is meaningfully reduced (per the team's own report).
- [ ] **No critical errors detected** in the last 7 digests.
- [ ] **≥ 2 strategic signals per week** that inform decisions.
- [ ] **Cost stable:** alert fires if any single run exceeds $3 for 3 consecutive days.

**Demotion trigger:** if monitoring shows quality dropping or recipients stop reading, roll back to Phase 3 and investigate.

---

## Phase Evidence Index

| Phase | Started | Graduated | Evidence |
|---|---|---|---|
| 1 Shadow | 2026-05-18 | _pending_ | [rollout/phase1_shadow/](rollout/phase1_shadow/) |
| 2 Suggested | _pending_ | _pending_ | [rollout/phase2_suggested/](rollout/phase2_suggested/) |
| 3 Approved | _pending_ | _pending_ | [rollout/phase3_approved/](rollout/phase3_approved/) |
| 4 Autonomous | _pending_ | — | [rollout/phase4_autonomous/](rollout/phase4_autonomous/) |
