# Project Instructions

<!-- ⚠️  THIS FILE IS AUTO-POPULATED after the first planning session.
     When you run plan mode for the first time, Claude will fill in
     Tech Stack, Commands, Project Structure, and Rules based on the plan.
     Review and adjust as needed. -->

## Session Start

**Fresh project (no PROGRESS.md):**
Run the full test suite to orient yourself on project scope and current state. Do not proceed if tests are failing unless the task is specifically to fix them.

**Resuming work (PROGRESS.md exists):**
1. Read `.claude/PROGRESS.md` for handoff context
2. Run `git log --oneline -10` to see recent commits
3. Run the full test suite — confirm current state is green
4. Read `tasks/todo.md` and `tasks/lessons.md` if they exist
5. Pick the highest-priority incomplete item from PROGRESS.md
6. Begin work — do not re-implement anything marked as Completed

## Project Summary

**B2B SaaS Competitive Intelligence Agent** — Monitors 5 project management tools (Linear, Asana, Notion, Monday, ClickUp) daily for competitive signals (product launches, pricing changes, content, hiring, positioning). Sends weekly email digests with high-signal events.

This is a **full lifecycle PM + engineer learning project** — the 6-stage discipline (Identify → Prototype → Production → Phased Rollout → Monitoring → Iteration) is the deliverable, equal to the agent itself.

Stage doc trail (built in order):
1. `WORKFLOW_SELECTION.md` — Stage 1 ROI evaluation of 5 candidate workflows
2. `prototype/` + `PROTOTYPE_LEARNINGS.md` — Stage 2 proof of concept
3. `src/` + `tests/` — Stage 3 production agent
4. `ROLLOUT_PLAN.md` + `rollout/` — Stage 4 phased rollout evidence
5. `monitoring/` — Stage 5 dashboard + alerts
6. `ITERATIONS.md` — Stage 6 post-launch iteration log

Plan file: `/Users/lukaszstrycharz/.claude/plans/i-want-to-work-unified-lecun.md`

## Tech Stack

- **Language:** Python 3.11+
- **LLM:** Anthropic SDK with Claude Opus 4.7 (signal extraction), Claude Haiku 4.5 (cheaper summarization where reasoning is light)
- **State:** SQLite (competitor data, seen signals, run logs)
- **HTTP fetching:** httpx (async, with timeout + SSRF guards per security rules)
- **Email:** Resend SDK for digests
- **Scheduling:** GitHub Actions (cron: daily 09:00 UTC)
- **Monitoring:** Streamlit dashboard, Slack webhooks for alerts
- **Testing:** pytest, pytest-asyncio, cassette replay for API determinism
- **Linting:** ruff (format + lint)

## Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Tests
pytest                          # full suite
pytest tests/test_stages.py -v  # single file

# Lint / format
ruff check .
ruff format .

# Run agent locally (one shot)
python -m src.main

# Run dashboard
streamlit run monitoring/dashboard.py
```

## Project Structure

```
.
├── WORKFLOW_SELECTION.md       # Stage 1 deliverable
├── prototype/                  # Stage 2 deliverable
│   ├── notebook.ipynb
│   └── PROTOTYPE_LEARNINGS.md
├── src/                        # Stage 3 agent code
│   ├── agent.py                # Orchestrator
│   ├── stages.py               # fetch → extract → dedupe → digest
│   ├── state.py                # SQLite wrapper
│   ├── tools.py                # web_fetch w/ SSRF + timeout guards
│   ├── config.py               # Competitor URLs, cost caps
│   └── main.py                 # GitHub Actions entry point
├── tests/                      # pytest (TDD red-green-refactor)
├── .github/workflows/
│   └── competitive_intel.yml   # Daily cron
├── rollout/                    # Stage 4 evidence (per-phase outputs)
├── monitoring/                 # Stage 5 dashboard + alerts
│   ├── dashboard.py
│   └── alerts.py
├── ROLLOUT_PLAN.md             # Stage 4 deliverable
├── ITERATIONS.md               # Stage 6 deliverable
└── requirements.txt
```

## Rules (project-specific)

- **Stage gates are real** — don't start Stage N+1 until Stage N's Definition of Done is met. The point of this project is the discipline.
- **Real competitors only** — use actual public URLs (pricing pages, blogs). Do not mock or fabricate competitor data for prototype or production.
- **Cost cap enforced in code** — every run records its API spend; agent halts if a single run projects to exceed $5 USD.
- **All competitor URLs are config, not hardcoded in stages** — keep `src/config.py` as the single source of truth for what's monitored.
- **Cassette replay for tests** — API calls in tests use recorded fixtures (no live Anthropic calls in CI). Live calls only when explicitly recording.

## Definition of Done
- Tests written before implementation (red/green/refactor cycle)
- Types pass
- Tests pass
- No new linting errors
- DB migrations generated if models changed
- No `TODO` or `FIXME` left without a linked issue
- Works locally end-to-end before pushing

## Common Gotchas
<!-- Add project-specific landmines here as you discover them -->

## Core Principles
- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs.
- **Own Your Mistakes**: When wrong, say so, fix it, add a lesson. No excuses.
- **Context Is King**: Read existing code before writing new code. Match patterns already in the repo.
