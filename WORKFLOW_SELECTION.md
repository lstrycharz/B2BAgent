# Stage 1: Workflow Selection

## Context

Before writing any agent code, we need to make an **explicit, scored decision** about which B2B SaaS workflow to automate. This document is the PM artifact: it forces us to compare alternatives on the dimensions that actually matter, justify the choice, and acknowledge what we're giving up.

Most agent projects skip this step and lose months building the wrong thing. We do it first, in 3 hours, so the next 60 hours of build time are pointed at the right target.

**Decision:** Build the **Competitive Intelligence** agent.

---

## The 5 Candidates

| # | Workflow | One-line description |
|---|----------|----------------------|
| 1 | **Competitive Intelligence** | Monitor 5-10 competitors daily for product launches, pricing changes, content, hiring, positioning shifts |
| 2 | **Sales Win/Loss Analysis** | Aggregate CRM deal data to extract structured win/loss reasons and competitor involvement |
| 3 | **Product Feedback Aggregation** | Pull from support tickets, NPS surveys, app reviews; surface trending themes weekly |
| 4 | **Market Trend Monitoring** | Track industry news, regulations, emerging categories adjacent to our space |
| 5 | **Customer Health Scoring** | Combine usage, support, and engagement signals to identify churn-risk accounts |

---

## Evaluation Dimensions

| Dimension | What we're measuring | Why it matters |
|-----------|---------------------|----------------|
| **Volume** | Number of data points the agent must process per run | Drives cost and risk of token blowup |
| **Cost** | Estimated $/week (API + infra) at production scale | Determines economic viability |
| **Decision Complexity** | How much real reasoning the agent must do vs. summarization | LLMs are great at some judgments and bad at others |
| **Reversibility** | What's the blast radius of a wrong output? | High reversibility = safe to test; low = pair-mode only |
| **Measurability** | Can we tell if the agent is working without weeks of waiting? | Required for the iteration loop to function |
| **Strategic Leverage** | If it works, how much business value is unlocked? | Some problems are worth solving even when hard |

Scoring is 1–5 (1 = weak, 5 = strong). Higher is better for *all* dimensions (e.g. Volume 5 = manageable volume; Cost 5 = cheap; Reversibility 5 = safe to fail; Decision Complexity 5 = in LLM sweet spot).

---

## Scoring Matrix

| Workflow | Volume | Cost | Decision Complexity | Reversibility | Measurability | Strategic Leverage | **Total (/30)** |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **1. Competitive Intelligence** | 4 | 5 | 4 | 5 | 4 | 4 | **26** |
| 2. Sales Win/Loss Analysis | 4 | 5 | 2 | 3 | 2 | 4 | 20 |
| 3. Product Feedback Aggregation | 2 | 3 | 3 | 4 | 3 | 4 | 19 |
| 4. Market Trend Monitoring | 1 | 2 | 2 | 5 | 2 | 3 | 15 |
| 5. Customer Health Scoring | 2 | 3 | 2 | 2 | 4 | 5 | 18 |

---

## Per-Workflow Rationale

### 1. Competitive Intelligence — winner (26/30)

- **Volume (4):** 5 competitors × ~5 sources each (pricing page, blog, careers, RSS, GitHub) = 25 fetches per daily run. Bounded and predictable.
- **Cost (5):** Estimated ~$1–2 per run × 7 = under $15/week at the planned model mix (Opus for extraction, Haiku for summarization). Easily affordable.
- **Decision Complexity (4):** The hard work is *novelty detection* (is this signal new vs. already-known?) and *significance ranking* (does this matter?). Both are well-suited to LLMs when paired with state (SQLite of seen signals).
- **Reversibility (5):** A bad digest wastes 10 minutes of a marketer's morning. Nothing breaks. No customer-facing impact. Easiest possible setting to iterate in.
- **Measurability (4):** Tractable metrics — signals per week, % relevance (human audit), team actions taken, lead time vs. public announcement.
- **Strategic Leverage (4):** Cited problem: 20h/week of a junior marketer. Even at 50% time recovery, that's ~10h/week × $40/hr = ~$20k/year per company. Multiplied across customers, real value.

### 2. Sales Win/Loss Analysis (20/30)

- **Decision Complexity (2) is the killer.** Sales rep notes are sparse, biased ("lost on price" when really lost on product), and multi-causal. Extracting *real* reasons requires customer interviews — exactly the work the agent can't do.
- Reversibility (3) suffers because wrong conclusions feed product strategy, which is expensive to reverse months later.
- Measurability (2) is worst-in-class: the only way to verify the agent is right is to interview lost customers, which defeats the automation.
- Strong on Cost (5) and Strategic Leverage (4), but the underlying data is too noisy to trust.

### 3. Product Feedback Aggregation (19/30)

- **Strong second choice.** Reversibility (4), Strategic Leverage (4), and reasonable Decision Complexity (3).
- Volume (2) is the main weakness — mid-size SaaS can produce thousands of support tickets and reviews per week. Token economics get ugly fast.
- Cost (3) reflects the volume issue — would likely need a two-tier system (cheap classifier + expensive LLM only on interesting tickets).
- Measurability (3) is tricky: easy to count themes surfaced, hard to know if the *right* themes surfaced (selection bias toward loud complaints).
- **Future candidate** once we have lifecycle muscle. Worth revisiting in 6 months.

### 4. Market Trend Monitoring (15/30)

- **Risk: becomes a generic news aggregator.** The internet has infinite trends; the agent's value is in saying "no" to most of them. That's a really hard prompt to get right.
- Volume (1) and Cost (2) are weak — filtering a firehose is expensive.
- Measurability (2) is the worst: "did we identify the right trend?" only knowable 6+ months out.
- Skip.

### 5. Customer Health Scoring (18/30)

- **Highest Strategic Leverage (5)** — churn is revenue.
- But **Reversibility (2) is dangerous.** False positives waste CS time chasing healthy accounts; false negatives produce surprise churn.
- **Decision Complexity (2):** Churn prediction is statistically multi-causal. Traditional ML (logistic regression, XGBoost on usage features) historically beats LLMs here. Using an LLM is the wrong tool.
- Measurability (4) is actually good (compare predictions to actual churn).
- Right problem, wrong tool. Skip for an LLM-agent project.

---

## Why Competitive Intelligence Wins (One-Paragraph Summary)

Competitive Intelligence wins because it sits in the sweet spot for an LLM agent: **bounded volume** (25 fetches per run, not 25,000), **manageable cost** (<$15/week), **high reversibility** (worst case is a wasted 10 minutes), and **strong measurability** (signals/week, relevance audit, team actions). Its decision complexity is novelty detection + significance ranking — both tasks where LLMs paired with persistent state genuinely excel. The strategic value (~20h/week saved per marketing team) is real but not load-bearing on the decision; if it were the only thing going for it, this wouldn't be the right pick. What makes it the right pick is the **combination of high reversibility and high measurability** — we can ship it, see if it works, and iterate, which is exactly the lifecycle muscle this project exists to build.

---

## Assumptions

1. We have access to 5 real B2B SaaS competitors with public-facing data (pricing pages, blogs, careers, RSS) — **confirmed** for Linear, Asana, Notion, Monday, ClickUp.
2. A weekly email digest is the right output format (vs. real-time alerts, vs. Slack updates, vs. dashboard).
3. The Anthropic API will remain available and pricing stable enough to run within budget.
4. Competitor websites will continue to expose useful data via standard HTTP fetching (no aggressive bot blocking that would force a paid scraping service).
5. A "team" exists or can be simulated who will receive the digest and provide feedback during Stage 4 rollout — for this project, that's primarily the builder, with simulated stakeholder reviews.

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|:----------:|:------:|------------|
| Competitor websites change structure or block scraping | Medium | Medium | Use stable sources (pricing pages, RSS); graceful degradation per source; log fetch failures distinctly from analysis failures |
| Signal extraction hallucinates "launches" that didn't happen | Medium | High | Require source URL + verbatim quote for every signal claim; Stage 4 Shadow phase catches before it ships; Opus-tier model only for extraction |
| Cost creeps as competitors add more pages or as we add more competitors | Low | Medium | Hard per-run cap in `src/config.py` (default $5); alert if >$3 for 3 consecutive runs; pre-flight token estimate before each LLM call |
| Deduplication fails and signals repeat week-over-week | Medium | Low | SQLite seen-signals table keyed on (competitor, signal_hash); explicit dedup test in CI |
| Digest becomes noise; team stops reading | Medium | High | Phase 1 (Shadow) requires 80% relevance before promoting; quality audit form in monitoring dashboard; iteration loop in Stage 6 tunes prompts based on real audit data |
| Bot detection / rate limiting on heavy fetches | Medium | Medium | Respectful rate limits (1 req/sec per host); rotate user agents only if needed; cache responses for at least 4 hours |

---

## What This Means for Stage 2

The prototype must answer **one question**: *Can Claude actually produce useful, non-generic competitive intelligence from real public data on a single competitor?*

If the prototype produces output that reads like a Wikipedia summary, the entire premise fails and we need to revisit (different prompt strategy? different data sources? wrong workflow?). If it produces something a marketer would forward to their CMO, we proceed to production.

Specifically, Stage 2 will:
- Pick 1–2 competitors from the chosen 5 (Linear and Asana are good first picks — distinct positioning, lots of public data)
- Fetch real pages today
- Extract signals with Claude
- Judge the output honestly: would I actually read this? Would I forward it?

---

## Definition of Done — Stage 1

- [x] Scoring table filled for all 5 workflows across all 6 dimensions
- [x] Explicit justification for Competitive Intelligence as winner
- [x] Acknowledged why runners-up matter (not strawmanned — Feedback Aggregation is explicitly flagged as a future candidate)
- [x] At least 2 risks listed with mitigation ideas (6 listed)
- [x] Can defend the decision in a 5-min conversation
