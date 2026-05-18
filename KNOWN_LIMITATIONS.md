# Known Limitations

Tracked failure modes the agent ships *with*, on purpose. Each one is a Stage 6 iteration candidate — we measure the real-world impact first, then decide whether the fix is worth its complexity cost.

The discipline: **add only after a failure** (never preemptive). Each entry must trace to a specific test, run, or observation.

---

## L-1 — Hash-based dedup misses paraphrased signals

**Discovered:** Stage 3 chunk 2 (2026-05-18), back-to-back local runs.

**Behavior:** `signal_hash` keys on `competitor + signal_type + normalized headline`. The verbatim_quote is intentionally excluded because Claude picks slightly different quote spans across runs even at `temperature=0`. This means:

- ✅ **Caught:** Two runs that produce literally the same headline → dedup works.
- ❌ **Missed:** Two runs that produce the same *intel* with different headlines. Observed concretely on back-to-back Linear runs: Run 1 said *"Linear ships 'Code Intelligence' and 'Triage Intelligence' as Business-tier differentiators"*; Run 2 said *"Linear's 'Code Intelligence' and 'Triage Intelligence' are gating AI-powered dev workflows behind the $16 Business tier"* — same intel, both treated as new.

**Why we ship anyway:**

1. The most-spammy failure case (literally identical strings appearing across weeks) IS caught.
2. Production runs are **weekly** (not back-to-back), so real signal-novelty rate is much higher than the contrived test suggests.
3. We can't measure the real failure rate without production data — building a fix now would be solving an unmeasured problem.

**Iteration plan (Stage 6 Iteration #1):**

- **Test data:** Wayback Machine snapshots of the 5 competitor pricing pages at 3 different historical points (e.g., 2026-01-15, 2026-03-01, 2026-05-01). Run the agent on each as if they were consecutive "weeks." Measure: % of signals in snapshot N that are semantic duplicates of signals in snapshot N-1. That's the baseline.
- **Hypothesis:** Adding semantic dedup (embeddings + cosine similarity threshold, or Claude-as-judge) reduces the baseline duplicate rate from X% to <5%.
- **Proposed change:** Either (a) compute embeddings for each signal, compare to last 90 days of stored signals, dedup if cosine similarity > 0.85; or (b) Claude-as-judge — for each candidate signal, pass last 30 stored headlines and ask "is this a duplicate?".
- **Measurement after fix:** Same Wayback test. Plus track ongoing weekly digest "felt-duplicate-rate" via the monitoring dashboard's quality audit form.
- **Trade-off being measured:** dedup quality gain vs. ~2× LLM cost (option b) or extra embedding-API cost (option a).

**Code pointer:** [src/state.py:signal_hash](src/state.py)
