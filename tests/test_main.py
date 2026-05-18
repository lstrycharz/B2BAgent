"""Tests for src/main.py — specifically the env-var handling that bit us in CI."""

from unittest.mock import MagicMock, patch

from src import main


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
