# PROGRESS — Cross-Session Handoff

Last updated: 2026-05-18 end-of-day.

## Completed

### Stages 1–3 — Identify, Prototype, Build (all Done)
- **Stage 1** [WORKFLOW_SELECTION.md](../WORKFLOW_SELECTION.md): scored 5 candidate workflows × 6 dimensions, picked Competitive Intelligence (26/30).
- **Stage 2** [prototype/](../prototype/): Jupyter notebook proves Claude produces useful intel on Linear + Asana. Forward-to-CMO bar passed, $0.086/run. Decision log signed off.
- **Stage 3** [src/](../src/) + [tests/](../tests/): full production agent in 6 chunks (vertical slice → SQLite dedup → 5 competitors → multi-source + cost cap → Resend email → GitHub Actions cron). **42 tests passing.** $0.22/run.

### Stage 4 — Phased Rollout (in progress, lean version)
- Phase 1 Shadow Day 1 ✅ — workflow ran successfully end-to-end in production (run [26064257711](https://github.com/lstrycharz/B2BAgent/actions/runs/26064257711)). Digest delivered to Gmail.
- Days 2 (2026-05-19) and 3 (2026-05-20) require ~2 min/day of skimming the digest. End-of-day-3 consolidated review in [rollout/phase1_shadow/_review.md](../rollout/phase1_shadow/_review.md).

### Stage 6 — Iterations (1 of 3+ logged)
- Iteration #1 ✅ — Lightened Phase 1 protocol for solo-project scale ([ITERATIONS.md](../ITERATIONS.md)).
- Iteration #2 queued — semantic dedup via Wayback-Machine snapshot test ([KNOWN_LIMITATIONS.md L-1](../KNOWN_LIMITATIONS.md)).

### Production milestones
- Repo created: https://github.com/lstrycharz/B2BAgent
- LICENSE (MIT) added, README updated for public visibility.
- 3 GitHub Actions secrets configured: ANTHROPIC_API_KEY, RESEND_API_KEY, DIGEST_RECIPIENT_EMAIL.
- Daily cron live at 09:00 UTC, auto-commits `data/state.db` back to repo for dedup persistence.
- Email delivery confirmed working (regression test for empty-env-var bug in `tests/test_main.py`).

## In Progress

- **Stage 4 Phase 1 Shadow** — passively running. Each morning's digest lands in Gmail; user does ~2 min skim. Consolidated review at end of day 3 (2026-05-20 evening) decides whether to graduate to Phase 2.

## Blocked / Pending User Action

- **Make repo public** — user has the command but hasn't run it yet:
  ```bash
  gh repo edit lstrycharz/B2BAgent --visibility public --accept-visibility-change-consequences
  ```
  Not urgent — Phase 1 work continues either way.

## Stage 5 — Monitoring (code Done)

- `monitoring/metrics.py` — pure `summarize_runs()` (total/success-rate/cost/signals).
- `monitoring/dashboard.py` — Streamlit app: topline metrics, cost-per-run + signals-per-run line charts, signals-per-competitor bar chart, recent-runs table. Verified via screenshot.
- `monitoring/alerts.py` — two health checks (no-signals-in-48h, cost-spike-3-consecutive) + Slack sender. Wired into the workflow as a 'Run health alerts' step.
- `src/state.py` gained `RunLog`/`RunRecord` (runs table) and `SignalStore.counts_by_competitor()`.
- `src/main.py` records every run (success/partial/error) to the RunLog.
- Run the dashboard: `streamlit run monitoring/dashboard.py`.
- Remaining DoD items are time-based (2 weeks of baseline data accumulates as the cron runs) + a user task (manually audit 5 digests).

## Next Up (priority order)

1. **Phase 1 Day 2/3 skims** (user, ~2 min each) — then end-of-day-3 consolidated review in `rollout/phase1_shadow/_review.md`
2. **Graduate decision: Phase 2 or stay in Phase 1** (after review)
3. **Stage 6 Iteration #2: semantic dedup** (after Phase 1 closes; uses Wayback Machine snapshots as test data)
4. **Optional housekeeping:** bump `actions/checkout`/`actions/setup-python` to silence Node 20 deprecation warning

## Known Issues / Limitations

- **L-1: paraphrased dedup misses** ([KNOWN_LIMITATIONS.md](../KNOWN_LIMITATIONS.md)) — hash-based dedup catches exact-headline repeats but not semantic equivalents. ~5% caught on back-to-back runs. Queued as Stage 6 Iteration #2.
- **Node 20 deprecation warning** in workflow — non-blocking until June 2026. Bump `actions/checkout` and `actions/setup-python` versions later.

## Session Resume Checklist

When resuming:
1. Read this file
2. `git log --oneline -10`
3. `.venv/bin/pytest` — confirm 67 still passing
4. Check latest workflow run: `gh run list --limit 3 --workflow=competitive_intel.yml`
5. If today is 2026-05-21 or later: open `rollout/phase1_shadow/_review.md` and decide Phase 2 graduation
6. Otherwise: wait for user input
