# Phase 1 Shadow — Consolidated Review

Fill in after 3 consecutive successful daily runs (~10 minutes one-time).

---

**Review date:** YYYY-MM-DD
**Phase 1 start date:** 2026-05-18
**Workflow runs reviewed:**
- Day 1 (2026-05-18): https://github.com/lstrycharz/B2BAgent/actions/runs/26063199541
- Day 2 (2026-05-19): _link to run_
- Day 3 (2026-05-20): _link to run_

## 1. Relevance gut-check

Looking at all the signals across the 3 digests together, how did they feel?

- [ ] **Most were useful** (≥ ~70% felt forward-worthy) → ✅ passes
- [ ] **About half** → mixed; consider one prompt iteration before promoting
- [ ] **Less than half** → ❌ fails; investigate and re-shadow

**Notes:**

_e.g., "5/5 product launches were almost always real and specific. 3/5 positioning signals were often abstract — would tighten the prompt to require a quoted, named claim for positioning signals."_

## 2. Hallucination check (1 signal, any of the 3 digests)

- **Picked signal:** (competitor, headline)
- **Source URL:**
- **Verbatim quote claimed in the digest:**
- **Was the quote actually in the source?** ✅ yes / ❌ no
- **If no, what does the source actually say?**

> A "no" here is a **stop-and-fix** event. Hallucinated quotes were the highest-risk failure mode flagged in the prototype design (PROTOTYPE_LEARNINGS.md A3). One verified case → tighten the prompt, log as an iteration, re-shadow.

## 3. Systematic patterns

Anything that systematically annoyed you across the 3 days? Log here; these become Stage 6 iteration candidates.

- _"Several Monday signals were near-duplicates of each other — semantic dedup is needed (already tracked as L-1 / Iteration #2)"_
- _e.g., "Significance ratings clustered too high — 14 of 21 signals were 4-5/5. Need more variance."_
- _e.g., "Notion's 'Plan Mode' signal didn't appear in Day 2 even though it's still on their site — fetch likely had stale cache"_

## 4. Run reliability

```bash
gh run list --limit 5 --workflow=competitive_intel.yml
```

- [ ] All 3 daily runs completed successfully
- [ ] No fetch errors that dropped an entire competitor
- [ ] No cost-cap aborts

## Decision

- [ ] **Graduate to Phase 2** (all 3 criteria pass — relevance ≥ 70%, no hallucination, all runs clean)
- [ ] **Stay in Phase 1** (fix specific failure first, log in ITERATIONS.md, re-shadow 2 more days)

**Decision rationale (1-2 sentences):**

_e.g., "Graduating. Quality felt high, hallucination check passed, no run errors. Two follow-on iteration items logged: semantic dedup (L-1) and Monday near-duplicates."_
