"""Health alerts for the competitive intelligence agent.

Run with:  python -m monitoring.alerts

Reads the RunLog, runs health checks, and posts any fired alerts to a Slack
incoming webhook (SLACK_WEBHOOK_URL). If no webhook is configured, checks still
run and print to stdout — so the alert logic is observable even before Slack
is wired up.

Check functions are pure (data in, alert-message-or-None out) so they're
unit-testable without a database or a webhook.
"""

import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

from src.state import RunLog, RunRecord

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "state.db"

_SLACK_TIMEOUT_SECONDS = 10.0


def check_no_signals(
    runs: list[RunRecord],
    now: datetime,
    window_hours: int = 48,
) -> str | None:
    """Alert if no signals surfaced within the last `window_hours`.

    Fires both when recent runs all returned 0 signals AND when there were no
    runs at all in the window (a silently-broken cron). Either way, a human
    should look.
    """
    cutoff = now.timestamp() - window_hours * 3600
    in_window = [
        r for r in runs if datetime.fromisoformat(r.started_at).timestamp() >= cutoff
    ]
    total_signals = sum(r.total_signals for r in in_window)
    if total_signals == 0:
        return (
            f":warning: No competitive signals surfaced in the last {window_hours}h "
            f"({len(in_window)} run(s) in window). The agent may be broken, or "
            f"competitors are unusually quiet — worth a look."
        )
    return None


def check_cost_spike(
    runs: list[RunRecord],
    threshold_usd: float = 3.0,
    consecutive: int = 3,
) -> str | None:
    """Alert if the most recent `consecutive` runs each exceeded `threshold_usd`.

    A single expensive run is noise; a sustained spike is a real signal that
    something (prompt size, competitor page bloat) changed."""
    if len(runs) < consecutive:
        return None
    recent = runs[:consecutive]  # runs are newest-first
    if all(r.cost_usd > threshold_usd for r in recent):
        costs = ", ".join(f"${r.cost_usd:.2f}" for r in recent)
        return (
            f":moneybag: Cost spike: the last {consecutive} runs each exceeded "
            f"${threshold_usd:.2f} ({costs}). Investigate before the budget cap trips."
        )
    return None


def send_slack(webhook_url: str, message: str) -> None:
    """Post a message to a Slack incoming webhook. No-op if webhook_url is empty."""
    if not webhook_url:
        return
    httpx.post(webhook_url, json={"text": message}, timeout=_SLACK_TIMEOUT_SECONDS)


def run_alert_checks(runs: list[RunRecord], now: datetime) -> list[str]:
    """Run every check, return the list of fired alert messages (may be empty)."""
    candidates = [
        check_no_signals(runs, now=now),
        check_cost_spike(runs),
    ]
    return [alert for alert in candidates if alert is not None]


def main() -> int:
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not DB_PATH.exists():
        print(f"No database at {DB_PATH}; nothing to check.")
        return 0

    log = RunLog(str(DB_PATH))
    try:
        runs = log.recent(limit=60)
    finally:
        log.close()

    alerts = run_alert_checks(runs, now=datetime.now(UTC))
    if not alerts:
        print("All health checks passed — no alerts.")
        return 0

    for alert in alerts:
        print(f"ALERT: {alert}")
        send_slack(webhook_url, alert)

    if not webhook_url:
        print("(SLACK_WEBHOOK_URL not set — alerts printed above but not delivered)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
