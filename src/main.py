"""CLI entry point for the competitive intelligence agent.

Usage: python -m src.main

Loads ANTHROPIC_API_KEY from .env, runs the full pipeline across all configured
competitors, prints the digest, and prints a cost summary.
"""

import os
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from src.agent import run_once
from src.config import DEFAULT_COMPETITORS, usage_to_cost_usd
from src.state import SignalStore

DEFAULT_MODEL_ID = "claude-sonnet-4-6"

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
    return 0


if __name__ == "__main__":
    sys.exit(main())
