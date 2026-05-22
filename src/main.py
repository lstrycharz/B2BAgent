"""CLI entry point for the competitive intelligence agent.

Usage: python -m src.main

Loads ANTHROPIC_API_KEY from .env, runs the full pipeline across all configured
competitors, records the run in the RunLog, prints the digest, and emails it.
"""

import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from anthropic import Anthropic
from dotenv import load_dotenv

from src.agent import RunResult, run_once
from src.config import DEFAULT_COMPETITORS, usage_to_cost_usd
from src.mailer import ResendSender
from src.state import RunLog, RunRecord, SignalStore

DEFAULT_MODEL_ID = "claude-sonnet-4-6"
DEFAULT_FROM_EMAIL = "onboarding@resend.dev"

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "data" / "state.db"


def main() -> int:
    # override=True so a stale empty env var doesn't block the real value
    load_dotenv(REPO_ROOT / ".env", override=True)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("error: ANTHROPIC_API_KEY is not set (see .env.example)", file=sys.stderr)
        return 2

    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    run_id = uuid4().hex
    started_at = datetime.now(UTC).isoformat()
    store = SignalStore(str(DEFAULT_DB_PATH))
    run_log = RunLog(str(DEFAULT_DB_PATH))

    try:
        try:
            client = Anthropic(api_key=api_key)
            result = run_once(
                client=client,
                competitors=DEFAULT_COMPETITORS,
                model_id=DEFAULT_MODEL_ID,
                store=store,
            )
        except Exception as e:
            run_log.record(_error_record(run_id, started_at, e))
            print(f"error: agent run failed and was logged: {e}", file=sys.stderr)
            return 1

        run_log.record(_run_record(run_id, started_at, result))
        _print_summary(result)
        _maybe_send_digest(
            result.digest,
            total_new_signals=sum(len(r.signals) for r in result.reports.values()),
        )
        return 0
    finally:
        store.close()
        run_log.close()


def _run_record(run_id: str, started_at: str, result: RunResult) -> RunRecord:
    """Build a RunRecord from a successful (or cost-capped) run."""
    total_signals = sum(len(r.signals) for r in result.reports.values())
    return RunRecord(
        run_id=run_id,
        started_at=started_at,
        status="partial" if result.aborted_competitors else "success",
        competitors_processed=len(result.reports),
        total_signals=total_signals,
        input_tokens=result.total_input_tokens,
        output_tokens=result.total_output_tokens,
        cost_usd=usage_to_cost_usd(result.total_input_tokens, result.total_output_tokens),
        aborted_competitors=",".join(result.aborted_competitors),
        error=None,
    )


def _error_record(run_id: str, started_at: str, exc: Exception) -> RunRecord:
    """Build a RunRecord for a run that crashed before completing."""
    return RunRecord(
        run_id=run_id,
        started_at=started_at,
        status="error",
        competitors_processed=0,
        total_signals=0,
        input_tokens=0,
        output_tokens=0,
        cost_usd=0.0,
        aborted_competitors="",
        error=f"{type(exc).__name__}: {exc}",
    )


def _print_summary(result: RunResult) -> None:
    print(result.digest)
    print()
    print("---")
    cost = usage_to_cost_usd(result.total_input_tokens, result.total_output_tokens)
    print(
        f"Tokens: {result.total_input_tokens} in / {result.total_output_tokens} out  "
        f"≈ ${cost:.4f} USD  |  state: {DEFAULT_DB_PATH}"
    )
    if result.aborted_competitors:
        print(
            f"⚠️  Cost cap reached; aborted: {', '.join(result.aborted_competitors)}",
            file=sys.stderr,
        )


def _maybe_send_digest(digest: str, total_new_signals: int) -> None:
    """Send the digest via Resend if RESEND_API_KEY and DIGEST_RECIPIENT_EMAIL
    are both set. Silently skipped otherwise so local-only runs work without
    email config."""
    resend_key = os.environ.get("RESEND_API_KEY")
    recipient = os.environ.get("DIGEST_RECIPIENT_EMAIL")
    if not resend_key or not recipient:
        print("(email skipped: RESEND_API_KEY or DIGEST_RECIPIENT_EMAIL not set)")
        return

    # `or` covers both unset *and* set-to-empty-string (which is what GitHub
    # Actions injects when the secret isn't configured — bug found 2026-05-18).
    from_address = os.environ.get("DIGEST_FROM_EMAIL") or DEFAULT_FROM_EMAIL
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    subject = f"[Competitive Intel] {today} — {total_new_signals} new signal(s)"

    try:
        sender = ResendSender(api_key=resend_key, from_address=from_address)
        msg_id = sender.send(to=recipient, subject=subject, body_text=digest)
        print(f"📨 Sent digest to {recipient} (resend id: {msg_id})")
    except Exception as e:
        # Don't fail the run because email failed — the digest is already printed
        # and signals are already in the SQLite store.
        # Log enough context to diagnose without exposing the API key.
        recipient_user, _, recipient_domain = recipient.partition("@")
        print(
            f"⚠️  Email send failed: type={type(e).__name__} msg={e!r}",
            file=sys.stderr,
        )
        print(
            f"   diagnostic: from={from_address!r}  recipient_user_len={len(recipient_user)}  "
            f"recipient_domain={recipient_domain!r}  key_len={len(resend_key)}",
            file=sys.stderr,
        )
        # Try to pull additional fields off the exception (some SDKs attach
        # .message, .code, .status_code, .body)
        for attr in ("message", "code", "status_code", "body", "errors"):
            value = getattr(e, attr, None)
            if value is not None:
                print(f"   exception.{attr} = {value!r}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
