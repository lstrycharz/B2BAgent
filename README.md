# B2B Agent

*A small robot that watches your competitors so you don't have to.*

---

## What is this?

Imagine you work at a software company. To stay ahead, someone on your team has to spend hours every week checking what 5 competing companies are doing — did they launch a new feature? Change their prices? Start hiring in a new country? It's tedious work, and it's easy to miss things.

**This project automates that work.** Every morning at 9 AM, an automatic program:

1. Visits the websites of five well-known competitors (Linear, Asana, Notion, Monday, and ClickUp — they all sell software to help teams organize their work)
2. Reads their pricing pages, product update logs, and blogs
3. Uses **Claude** (an AI made by Anthropic, similar to ChatGPT) to pick out what's actually new and interesting
4. Emails you a short summary with the highlights, ranked by how important each one is

It costs about **25 cents per day** to run.

---

## What does the email look like?

The subject line says something like:

> **[Competitive Intel] 2026-05-18 — 19 new signal(s)**

Inside, each "signal" looks like this:

> ### Linear (importance: 5 out of 5)
>
> **Linear shipped a new AI feature called Code Intelligence — it lets people who aren't engineers ask questions about how the company's software works.**
>
> This is significant because it expands Linear from being a tool just for developers into something marketing, sales, and support teams can use too. They're giving it away during the testing period, which is a deliberate strategy to get more people inside companies trying it.
>
> *Direct quote from Linear's website:*
> > "PMs can write sharper specs, Support and Sales can answer technical questions with more confidence..."
>
> *Link to source:* https://linear.app/changelog

About 4–6 of these per company, sorted with the most important first.

The **direct quote** is important: it means the AI can't just make something up — it has to point to the exact words on the source page where it found the news. You can always click through and verify.

---

## Why does this exist?

Two reasons:

**1. It saves real time.** A junior employee doing this kind of competitive watching manually spends roughly 20 hours a week on it. This program does it in a few minutes a day and finds things people would miss because they get bored after the third page.

**2. It's a learning project.** The person who built this (👋 hi) wanted practice doing the full job of designing, building, deploying, and improving an AI system — not just writing the code part. Most software projects skip the "think carefully and roll out cautiously" parts. This one walks through every step with written documentation.

The six stages, in plain English:

1. **Identify** — pick which task to automate (and write down *why* you picked it)
2. **Prototype** — prove the idea works on a small scale before building the real thing
3. **Build** — write the production version, with tests for everything
4. **Roll out carefully** — let it run, watch closely, expand only after it proves itself *(← currently here)*
5. **Monitor** — set up dashboards so you notice when things start going wrong
6. **Improve** — measure what's not great, change it, measure again

Each stage has its own document in this repository explaining what was done and why.

---

## Current status

The agent is **running daily** in **Shadow mode**. That means the email only goes to the developer for now — not to anyone else — so any mistakes the AI makes can be caught quietly. After several days of consistent good-quality emails (≥80% of signals are useful, no fabricated facts, no crashes), it graduates to a wider audience.

Each phase is gated by explicit "go / no-go" criteria. The decision to expand isn't "it feels ready" — it's a checklist that has to pass.

---

## How does it know what's important?

The AI follows a few strict rules:

- **Every signal must include a direct quote.** No quote → it doesn't make it into the email. This is the main defense against the AI making things up.
- **Rank everything 1 to 5.** Trivia gets a 1. Real strategic news gets a 5. The email sorts them so you read the most important stuff first.
- **Prefer 3 great signals over 10 generic ones.** The AI is told it's better to send a short, useful email than a long, padded one.

The AI does occasionally repeat itself across weeks (it might phrase the same news two slightly different ways and not realize it's the same news). There's a known fix for this planned in a future update.

---

## What does it cost?

| Cost | Amount |
|---|---|
| Per daily run | ~$0.22 |
| Per month | ~$7 |
| Setup | Free (uses free tiers of GitHub and Resend) |

For comparison, a part-time analyst doing the same work would cost a few thousand dollars a month — though, to be fair, the analyst would also catch things this program can't, like rumors in industry forums and conversations on LinkedIn. This program handles only what's published on competitors' own websites.

---

## What's in this repository?

For anyone who wants to look around:

- **[WORKFLOW_SELECTION.md](WORKFLOW_SELECTION.md)** — The "why we built this and not something else" document
- **[prototype/](prototype/)** — The little experiment that proved the idea worked before we built the real thing
- **[src/](src/)** — The actual program (Python code)
- **[tests/](tests/)** — 38 automated checks that make sure the program does what it's supposed to do
- **[ROLLOUT_PLAN.md](ROLLOUT_PLAN.md)** — The 4-phase plan for going from "tested" to "fully trusted"
- **[rollout/](rollout/)** — Real evidence collected during each rollout phase (what the AI produced, what was good, what was bad)
- **[KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md)** — An honest list of what doesn't work great yet and what we plan to do about it
- **[.github/workflows/competitive_intel.yml](.github/workflows/competitive_intel.yml)** — The schedule that makes it run every day automatically

---

## Scope and responsible use

This agent fetches only **publicly published content** from competitor websites (pricing pages, public changelogs, public blogs). It does not log in, does not bypass any access control, and respects standard `robots.txt` conventions implicitly by only requesting documented public URLs.

If you fork this and point it at different sites, you are responsible for:
- Respecting those sites' Terms of Service
- Not exceeding reasonable request rates
- Using the output internally rather than republishing it

The five competitors monitored by default (Linear, Asana, Notion, Monday, ClickUp) were chosen precisely because all five publish pricing, product updates, and blog content openly for marketing reasons — they want this content read.

## License

[MIT](LICENSE). Use it, fork it, modify it, ship it — credit appreciated, not required.

## Status disclaimer

This is a **learning project**, not a commercial product. It works (42 tests passing, running daily in production), but it ships with known limitations (see [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md)) and is intentionally simple in places where a production-grade tool would invest more. If you want competitive intelligence as a paid service, several established companies do this — this repo is for people who want to *learn how to build* one.

## For developers

If you're technical and want to run this yourself, see **[.claude/CLAUDE.md](.claude/CLAUDE.md)** for the setup commands, tech stack, and project structure. Quick version:

```bash
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # then fill in ANTHROPIC_API_KEY
python -m src.main         # one-shot run; prints the digest
pytest                     # 38 tests, runs in <1 second
```

To deploy: fork the repo, set the GitHub Actions secrets (`ANTHROPIC_API_KEY` required; `RESEND_API_KEY` + `DIGEST_RECIPIENT_EMAIL` optional for email), and the daily cron takes over.
