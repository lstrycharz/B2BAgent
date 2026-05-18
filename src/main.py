"""CLI entry point for the competitive intelligence agent.

Usage: python -m src.main

Loads ANTHROPIC_API_KEY from .env, runs the full pipeline across all configured
competitors, prints the digest, and prints a cost summary.
"""

import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from src.agent import run_once
from src.config import DEFAULT_COMPETITORS, usage_to_cost_usd
from src.mailer import ResendSender
from src.state import SignalStore

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
    store = SignalStore(str(DEFAULT_DB_PATH))

    try:
        client = Anthropic(api_key=api_key)
        result = run_once(
            client=client,
            competitors=DEFAULT_COMPETITORS,
            model_id=DEFAULT_MODEL_ID,
            store=store,
        )
    finally:
        store.close()

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

    _maybe_send_digest(result.digest, total_new_signals=sum(len(r.signals) for r in result.reports.values()))
    return 0


def _maybe_send_digest(digest: str, total_new_signals: int) -> None:
    """Send the digest via Resend if RESEND_API_KEY and DIGEST_RECIPIENT_EMAIL
    are both set. Silently skipped otherwise so local-only runs work without
    email config."""
    resend_key = os.environ.get("RESEND_API_KEY")
    recipient = os.environ.get("DIGEST_RECIPIENT_EMAIL")
    if not resend_key or not recipient:
        print("(email skipped: RESEND_API_KEY or DIGEST_RECIPIENT_EMAIL not set)")
        return

    from_address = os.environ.get("DIGEST_FROM_EMAIL", DEFAULT_FROM_EMAIL)
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
