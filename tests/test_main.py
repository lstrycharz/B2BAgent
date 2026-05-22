"""Tests for src/main.py — env-var handling + run-record construction."""

from unittest.mock import MagicMock, patch

from src import main
from src.agent import RunResult
from src.stages import IntelligenceReport, Signal


def _report(name: str, n_signals: int) -> IntelligenceReport:
    return IntelligenceReport(
        competitor=name,
        signals=[
            Signal(
                signal_type="product_launch",
                headline=f"{name} #{i}",
                detail="-",
                verbatim_quote="-",
                source_url="https://x.com",
                significance=3,
            )
            for i in range(n_signals)
        ],
    )


# --- run-record construction --------------------------------------------------

def test_run_record_marks_success_when_nothing_aborted():
    result = RunResult(
        digest="...",
        reports={"Linear": _report("Linear", 3), "Asana": _report("Asana", 2)},
        total_input_tokens=45000,
        total_output_tokens=5800,
        aborted_competitors=[],
    )
    rec = main._run_record("run-1", "2026-05-18T09:00:00+00:00", result)
    assert rec.status == "success"
    assert rec.competitors_processed == 2
    assert rec.total_signals == 5
    assert rec.cost_usd > 0
    assert rec.aborted_competitors == ""
    assert rec.error is None


def test_run_record_marks_partial_when_competitors_aborted():
    result = RunResult(
        digest="...",
        reports={"Linear": _report("Linear", 3)},
        total_input_tokens=10000,
        total_output_tokens=1000,
        aborted_competitors=["Monday", "ClickUp"],
    )
    rec = main._run_record("run-2", "2026-05-18T09:00:00+00:00", result)
    assert rec.status == "partial"
    assert rec.aborted_competitors == "Monday,ClickUp"


def test_error_record_captures_exception_type_and_message():
    rec = main._error_record(
        "run-3", "2026-05-18T09:00:00+00:00", RuntimeError("fetch blew up")
    )
    assert rec.status == "error"
    assert rec.error == "RuntimeError: fetch blew up"
    assert rec.total_signals == 0
    assert rec.cost_usd == 0.0


@patch("src.main.ResendSender")
def test_empty_digest_from_email_falls_back_to_default(mock_sender_cls, monkeypatch):
    """Regression: GitHub Actions injects unset secrets as empty strings, not
    None. `os.environ.get(KEY, DEFAULT)` returns '' verbatim in that case,
    which caused Resend to reject sends with 'The domain is invalid'.
    The fix is `os.environ.get(KEY) or DEFAULT`."""
    monkeypatch.setenv("RESEND_API_KEY", "re_fake")
    monkeypatch.setenv("DIGEST_RECIPIENT_EMAIL", "test@example.com")
    monkeypatch.setenv("DIGEST_FROM_EMAIL", "")  # simulate the GitHub Actions case

    mock_sender = MagicMock()
    mock_sender.send.return_value = "msg-id"
    mock_sender_cls.return_value = mock_sender

    main._maybe_send_digest(digest="...", total_new_signals=3)

    # The ResendSender must be constructed with the DEFAULT, not the empty string
    mock_sender_cls.assert_called_once()
    construct_kwargs = mock_sender_cls.call_args.kwargs
    assert construct_kwargs["from_address"] == main.DEFAULT_FROM_EMAIL
    assert construct_kwargs["from_address"] != ""


@patch("src.main.ResendSender")
def test_unset_digest_from_email_uses_default(mock_sender_cls, monkeypatch):
    """Companion check: unset env var also yields the default."""
    monkeypatch.setenv("RESEND_API_KEY", "re_fake")
    monkeypatch.setenv("DIGEST_RECIPIENT_EMAIL", "test@example.com")
    monkeypatch.delenv("DIGEST_FROM_EMAIL", raising=False)

    mock_sender = MagicMock()
    mock_sender.send.return_value = "msg-id"
    mock_sender_cls.return_value = mock_sender

    main._maybe_send_digest(digest="...", total_new_signals=3)

    assert mock_sender_cls.call_args.kwargs["from_address"] == main.DEFAULT_FROM_EMAIL


@patch("src.main.ResendSender")
def test_explicit_digest_from_email_overrides_default(mock_sender_cls, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_fake")
    monkeypatch.setenv("DIGEST_RECIPIENT_EMAIL", "test@example.com")
    monkeypatch.setenv("DIGEST_FROM_EMAIL", "intel@mydomain.com")

    mock_sender = MagicMock()
    mock_sender.send.return_value = "msg-id"
    mock_sender_cls.return_value = mock_sender

    main._maybe_send_digest(digest="...", total_new_signals=3)

    assert mock_sender_cls.call_args.kwargs["from_address"] == "intel@mydomain.com"


def test_skips_send_when_resend_api_key_missing(monkeypatch, capsys):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.setenv("DIGEST_RECIPIENT_EMAIL", "test@example.com")

    main._maybe_send_digest(digest="...", total_new_signals=3)

    out = capsys.readouterr().out
    assert "email skipped" in out
