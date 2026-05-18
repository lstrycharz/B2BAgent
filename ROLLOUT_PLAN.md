# Stage 4: Phased Rollout Plan

## Context

The agent is built and runs successfully in production (GitHub Actions cron, daily 09:00 UTC). Before letting it run **autonomously**, we put it through 4 gated phases. Each phase has explicit go/no-go criteria — none of "it feels ready, let's ship." The phases trade the cost of waiting for the value of catching real-world failure modes (a competitor changes their HTML structure, the LLM produces a fabricated signal, the cron times out) that no amount of pre-production testing would catch.

This is the lifecycle muscle most engineers skip. The whole point of building the agent in 6 small chunks was to *earn the right* to go through this phase carefully, not bypass it.

**Evidence directory:** [`rollout/`](rollout/) — one subdirectory per phase, populated with copies of digests, the human review notes, and the graduation decision.

---

## Phase 1 — Shadow

**Duration:** 3–4 days minimum (target start: 2026-05-18 → graduate no earlier than 2026-05-21).

**Behavior:** Agent runs daily as scheduled. The email digest is delivered to `DIGEST_RECIPIENT_EMAIL` (you) only. **You do not forward it to anyone else.** You read every digest and annotate each signal as `✓` (would-forward), `✗` (noise), or `?` (needs more context).

**Why this phase exists:** to catch hallucinations, broken fetches, and noise-heavy output *before* anyone outside you sees the digest. Worst-case failure here is your 10 minutes of reading time.

**Daily ritual (≤ 10 min):**
1. Open the digest email.
2. For each signal, decide ✓ / ✗ / ?. Note the reason if not obvious.
3. Verify the verbatim quote exists in the source URL (spot-check 1 per digest — Cmd-F the quote in the source page).
4. Append the day's annotations to a new file under [`rollout/phase1_shadow/`](rollout/phase1_shadow/) using the [template](rollout/phase1_shadow/_template.md).

**Go / no-go criteria** (all must hold over the last 3 days before graduating):
- [ ] **Relevance ≥ 80%:** at minimum 4 of every 5 signals marked ✓ across the rolling 3-day window.
- [ ] **Real catch:** the agent surfaced at least 1 competitive move you could independently verify (cross-reference against TechCrunch, the competitor's Twitter, or a news search).
- [ ] **Zero hallucinations:** all spot-checked verbatim quotes are present in the source URLs verbatim. If any quote turns out to be paraphrased or fabricated → **stop. Tighten the prompt. Re-shadow.**
- [ ] **Run reliability:** 3 consecutive successful workflow runs, no fetch errors that lost an entire competitor, no cost-cap aborts.

**No-go action:** stay in Shadow. Identify the highest-impact failure (noise rate, prompt phrasing, fetch reliability) and address it before extending the phase.

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
