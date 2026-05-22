"""Tests for monitoring/alerts.py — health checks + Slack delivery."""

from datetime import UTC, datetime
from unittest.mock import patch

import httpx
import respx

from monitoring.alerts import check_cost_spike, check_no_signals, send_slack
from src.state import RunRecord

NOW = datetime(2026, 5, 18, 9, 0, tzinfo=UTC)


def _run(hours_ago: float, signals: int, cost: float, status: str = "success") -> RunRecord:
    started = NOW.timestamp() - hours_ago * 3600
    return RunRecord(
        run_id=f"r-{hours_ago}",
        started_at=datetime.fromtimestamp(started, tz=UTC).isoformat(),
        status=status,
        competitors_processed=5,
        total_signals=signals,
        input_tokens=45000,
        output_tokens=5800,
        cost_usd=cost,
        aborted_competitors="",
        error=None,
    )


# --- check_no_signals ---------------------------------------------------------

def test_no_signals_alert_when_recent_runs_all_empty():
    runs = [_run(2, signals=0, cost=0.2), _run(26, signals=0, cost=0.2)]
    alert = check_no_signals(runs, now=NOW, window_hours=48)
    assert alert is not None
    assert "48" in alert


def test_no_signals_alert_when_no_runs_at_all_in_window():
    """Cron silently broke — no runs in 48h is itself an alert."""
    runs = [_run(100, signals=12, cost=0.2)]  # outside the 48h window
    alert = check_no_signals(runs, now=NOW, window_hours=48)
    assert alert is not None


def test_no_signals_quiet_when_window_has_signals():
    runs = [_run(2, signals=8, cost=0.2), _run(26, signals=0, cost=0.2)]
    assert check_no_signals(runs, now=NOW, window_hours=48) is None


# --- check_cost_spike ---------------------------------------------------------

def test_cost_spike_alert_when_last_3_runs_all_over_threshold():
    runs = [_run(2, 10, 3.5), _run(26, 10, 3.2), _run(50, 10, 3.8), _run(74, 10, 0.2)]
    alert = check_cost_spike(runs, threshold_usd=3.0, consecutive=3)
    assert alert is not None
    assert "3" in alert


def test_cost_spike_quiet_when_only_two_recent_runs_over():
    runs = [_run(2, 10, 3.5), _run(26, 10, 3.2), _run(50, 10, 0.2)]
    assert check_cost_spike(runs, threshold_usd=3.0, consecutive=3) is None


def test_cost_spike_quiet_under_normal_cost():
    runs = [_run(2, 10, 0.22), _run(26, 10, 0.21), _run(50, 10, 0.23)]
    assert check_cost_spike(runs, threshold_usd=3.0, consecutive=3) is None


# --- send_slack ---------------------------------------------------------------

@respx.mock
def test_send_slack_posts_text_payload():
    route = respx.post("https://hooks.slack.com/services/T/B/X").mock(
        return_value=httpx.Response(200, text="ok")
    )
    send_slack("https://hooks.slack.com/services/T/B/X", "agent is down")
    assert route.called
    sent = route.calls.last.request
    import json

    assert json.loads(sent.content)["text"] == "agent is down"


def test_send_slack_noop_when_webhook_url_empty():
    """No webhook configured → silently skip, don't crash."""
    with patch("httpx.post") as mock_post:
        send_slack("", "message")
        mock_post.assert_not_called()
