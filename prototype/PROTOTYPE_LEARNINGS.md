# Stage 2: Prototype Learnings

## Context

The Stage 2 goal was to answer one question: *Can Claude actually produce useful, non-generic competitive intelligence from real public data on a single competitor?* This doc captures the design decisions made while building [`notebook.ipynb`](notebook.ipynb), the open questions that only running the notebook can answer, and the explicit list of things that **must change before Stage 3 production**.

> ⚠️ **Status:** This doc is split into two sections. Section A (Design Decisions) was completed when the notebook was built. Section B (Open Questions) requires you to actually run the notebook with a real `ANTHROPIC_API_KEY` and judge the output. Run the notebook, fill in Section B, then move to Stage 3.

---

## Section A — Design Decisions Made During Prototyping

### A1. Model choice: Sonnet 4.6 for prototype, A/B test in production

Initial plan called for Opus 4.7 throughout. Changed to **Sonnet 4.6 for the prototype** because:

- We're iterating prompts, not testing model ceiling. Opus on every iteration is wasteful.
- Sonnet 4.6 is ~5× cheaper. ~$0.05 vs ~$0.25 per run during prompt tuning saves real money over 20+ iterations.
- If Sonnet 4.6 produces forward-to-CMO quality, **production should use Sonnet 4.6**, not Opus. Per agent-design rule: "per-stage model routing is correctness, not cost — sometimes the weaker/faster model is the right one."

**Production decision deferred to Stage 3:** A/B 5 sample runs Sonnet 4.6 vs Opus 4.7 on the same competitor data, blind-rate the outputs, pick the cheaper model unless Opus is meaningfully better.

### A2. Strict output contract via tool use, not "respond in JSON"

The notebook uses `tool_choice={'type': 'tool', 'name': 'submit_intelligence_report'}` to force structured output that matches a Pydantic schema. We avoid the "please respond in JSON" pattern because:

- The Anthropic SDK's tool-use path gives us validated structured output without regex parsing.
- Malformed output raises a Pydantic `ValidationError` loudly instead of producing a string that silently breaks downstream code.
- Matches the agent-design rule: *"strict output contracts (Pydantic / Zod / equivalent). Malformed output fails loudly and immediately."*

### A3. Every signal requires a verbatim quote — anti-hallucination guard

The `Signal` schema requires `verbatim_quote` as a non-optional field. The system prompt says: *"If you cannot quote it, do not report it."* This is the primary defense against the failure mode I'm most worried about: **the agent fabricating "competitor X launched Y" with no basis in the fetched data**.

The Stage 4 Shadow phase will manually spot-check whether quotes actually appear in source URLs. If quotes turn out to be paraphrases or hallucinations, the prompt needs to be tightened further (e.g., require character offsets within the source text).

### A4. Constrained signal types — no `"other"` escape hatch

Five buckets only: `product_launch`, `pricing_change`, `hiring`, `positioning`, `content`. No "other" option. This is deliberate — forcing the model to commit to a category rather than dump miscellany into a catch-all bucket improves downstream filtering and per-type prompt tuning.

If a category turns out to be missing (e.g., `acquisition` becomes important), add it explicitly. Don't relax the constraint.

### A5. Significance rating 1–5 with rubric, plus `null_finding` field

Two anti-noise mechanisms:

1. **Rated rubric in system prompt:** 1 = trivia, 3 = worth knowing, 5 = strategic. The rendered report sorts by significance, so a 5 dominates a 2.
2. **`null_finding` field:** The model can return `signals=[]` if there's genuinely nothing strategic. This permits an honest "quiet week" rather than forcing fabricated signals.

If the prototype produces a lot of 3-5 signals on a competitor that's actually been quiet, the model is overrating — tighten the rubric or use a stricter prompt.

### A6. Two narrow sources per competitor (pricing + changelog/blog)

Production plan calls for 5 sources per competitor (pricing, blog, careers, RSS, GitHub). Prototype intentionally narrows to two:

- **Pricing page** — catches the highest-stakes signal type (pricing changes).
- **Changelog (Linear) / blog RSS (Asana)** — catches product launches and content shifts.

If the prototype can't extract good signals from two clean sources, adding three more won't help — it just adds noise. **Only widen the source list in Stage 3 after the prompt produces good output on the narrow set.**

### A7. HTML stripping with BeautifulSoup + script/style removal

The fetched pages are 350KB–2MB of Next.js-rendered HTML. After running `html_to_text()`, expect 5K–30K characters of usable text. Then truncated to 30K chars per source before sending to Claude (~7.5K tokens per source max).

Trade-off accepted: aggressive stripping might lose context (e.g., hidden price tiers in modals). If we miss real signals because of this, the production version may need a more careful per-site parser (a "Linear pricing parser" that knows the page structure). For prototype, generic stripping is enough.

### A8. Cost recording and persistence

Every notebook run writes a timestamped JSON to `prototype/runs/` capturing model, tokens, estimated cost, and the structured reports. This lets us:

- Compare runs as we iterate the prompt (did relevance go up or down?).
- Spot-check what production cost will look like.
- Have real artifacts to paste into this doc as evidence.

The `runs/` directory is gitignored except for the most recent representative run (which we'll commit as an artifact).

### A9. Security guards baked in from prototype, not retrofitted

`fetch_with_guards()` already enforces:
- Explicit 15s timeout per request
- 5MB response size cap (streaming, not download-then-truncate)
- Manual redirect handling with per-hop host allowlist re-check
- Host allowlist (only the 5 competitor domains permitted)

These are required for production per `~/.claude/rules/security.md`. Building them in now means the production agent reuses this shape, rather than us "remembering to add them later."

---

## Section B — Open Questions Answered by Running the Notebook

> Fill these in after running `prototype/notebook.ipynb` end-to-end with a real `ANTHROPIC_API_KEY`. Each question has a guidance hint to keep your judgment honest.

### B1. Would you forward the rendered digest to a CMO?

`[ ] yes  [ ] yes-with-edits  [ ] no`

**Linear:** _your answer_
**Asana:** _your answer_

*Guidance:* If you'd add even one sentence of context before forwarding ("by the way, ignore signal #3, it's nothing"), the answer is "yes-with-edits" — log what you'd add or strip.

### B2. Are the verbatim quotes actually verbatim?

Spot-check 3 quotes against the source URLs. Open the URL, Cmd-F the quote, confirm match.

`[ ] 3/3 verbatim  [ ] 2/3 verbatim  [ ] <2/3 verbatim`

If <3/3: the prompt needs to be tighter. Consider adding "use Ctrl-F searchable phrases — do not paraphrase, do not summarize."

### B3. Are significance ratings calibrated?

For each signal rated 4 or 5, ask: *would a busy CMO actually care?* For each signal rated 1 or 2, ask: *should this even be in the digest?*

Misratings observed: _list any specific ones, e.g._ "Linear hiring a Senior Brand Designer scored 4/5 but is closer to 2/5"

### B4. What's the worst signal in the digest?

The lowest-quality item tells you what to fix first. Identify it and why.

_your answer_

### B5. What's missing that you expected to see?

If you know Linear or Asana made a recent move that the agent didn't catch, log it here. This becomes a regression test in Stage 3.

_your answer_

### B6. Actual cost per competitor

Recorded automatically in `runs/*.json`. Fill in:

| Competitor | Input tokens | Output tokens | Cost (USD) |
|---|:-:|:-:|:-:|
| Linear | _ | _ | _ |
| Asana | _ | _ | _ |
| **Total** | _ | _ | _ |

Production target: ≤ $2 per run across 5 competitors. If prototype-with-2-competitors is already > $0.80, the math won't work for 5 competitors with 5 sources each → must add per-competitor pre-flight token budget.

### B7. Did the prompt produce any blatant hallucinations?

`[ ] no hallucinations observed  [ ] minor (paraphrase passed as quote)  [ ] major (fact fabricated)`

If major: do not proceed to Stage 3 until the prompt is fixed and re-validated.

---

## Section C — Production Design Changes Already Identified

These are changes that **must** make it into Stage 3 even before running the prototype, based on what was learned while building it:

1. **SQLite seen-signals table.** The prototype has no memory — every run re-reports the same signals. Production needs `(competitor, signal_hash)` deduplication keyed on a stable hash of `signal_type + headline + verbatim_quote[:200]`.

2. **Per-run cost cap with circuit breaker.** Prototype tracks cost after the fact. Production must estimate tokens before each call and abort the run if the projected total would exceed the configured cap (default $5).

3. **Source-specific parsers as opt-in upgrade.** Generic `html_to_text` will miss structured data (pricing tiers in interactive components, changelog item dates). Production should have a `parsers/` module where competitor+source pairs can register custom extractors when generic stripping proves lossy.

4. **Async fetching with concurrency cap.** Prototype fetches sequentially with `time.sleep(1.0)` between calls. Production runs across 5 competitors × 5 sources = 25 fetches — should use `httpx.AsyncClient` with a concurrency semaphore (e.g., 3 concurrent, 1s min spacing per host).

5. **Truncation strategy is naive.** Prototype truncates to 30K chars per source. For long blog feeds we may lose the most recent posts (they could be at the end). Production should either (a) parse the RSS XML to grab N most recent items, or (b) truncate by tag boundary not character count.

6. **Cassette-replay tests.** Per agent-design rule, tests for Stage 3 should use recorded API responses, not live calls. `respx` is in `requirements.txt` already for this.

7. **Digest assembly is a separate stage.** Prototype renders per-competitor reports. The production weekly email needs to merge across all 5 competitors, sort by significance, and produce one cohesive digest. That's a separate LLM call (digest editor persona) — adds cost but improves readability.

8. **Source URL normalization.** If `linear.app/pricing` redirects to `linear.app/pricing/` after a site update, naive deduplication will treat them as different. Normalize URLs (lowercase, strip trailing slash, strip query params except known-meaningful ones) before storing.

9. **(Discovered in Stage 3 chunk 2, backfilled here)** **Hash-based dedup misses paraphrased signals even at `temperature=0`.** Originally we planned to include `verbatim_quote[:200]` in the dedup hash. Live testing showed Claude picks slightly different quote spans across runs, defeating the hash. Even after switching to headline-only hashing, Claude rephrases the *headline itself* across runs for the same underlying intel. The fix (semantic similarity dedup) is not free, and we can't measure whether it's needed until we have production data. Logged as `L-1` in [KNOWN_LIMITATIONS.md](../KNOWN_LIMITATIONS.md) and queued as Stage 6 Iteration #1.

---

## Section D — Definition of Done — Stage 2

- [x] Notebook structure built, JSON validates
- [x] Real competitor URLs confirmed reachable (200 OK on all 5 candidate sources during URL probe)
- [x] Security guards (timeout, size cap, allowlist, manual redirect handling) implemented in `fetch_with_guards()`
- [x] Strict Pydantic output contract + verbatim-quote requirement coded in prompt
- [x] PROTOTYPE_LEARNINGS.md sections A and C complete
- [ ] Notebook runs end-to-end against real Anthropic API (requires user with API key)
- [ ] Produces 2+ concrete signals per competitor that pass the "forward to CMO" bar
- [ ] PROTOTYPE_LEARNINGS.md Section B filled in with honest judgments
- [ ] Decision recorded below: proceed to Stage 3, or revise prompt/sources first

## Decision Log

| Date | Run | Decision | Notes |
|------|-----|----------|-------|
| 2026-05-18 | runs/20260518T192638Z.json | **Proceed to Stage 3** | First-shot run on Linear + Asana produced specific, well-quoted, strategically interesting signals (e.g., Linear Code Intelligence beta, Asana AI Studio bundled credits, Asana compliance add-ons gated even on Enterprise+). Forward-to-CMO bar passed. Cost $0.086 for 2 competitors / 3 sources. Quotes were verbatim on spot-check. Asana RSS source initially failed due to relative-URL redirect handling — fixed in cell `ab0ffc37`. |
