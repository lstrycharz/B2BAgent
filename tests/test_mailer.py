"""Tests for src/mailer.py — Resend-backed email delivery for digests."""

from unittest.mock import patch

from src.mailer import ResendSender


def test_resend_sender_sends_with_correct_params():
    with patch("resend.Emails.send") as mock_send:
        mock_send.return_value = {"id": "msg-abc123"}
        sender = ResendSender(api_key="re_test", from_address="agent@example.com")
        msg_id = sender.send(
            to="cmo@example.com",
            subject="Weekly intel digest",
            body_text="# Linear\n\n- thing happened",
        )
        assert msg_id == "msg-abc123"
        params = mock_send.call_args[0][0]
        assert params["from"] == "agent@example.com"
        assert params["to"] == ["cmo@example.com"]
        assert params["subject"] == "Weekly intel digest"
        assert params["text"] == "# Linear\n\n- thing happened"


def test_resend_sender_sets_api_key_on_module():
    """Resend SDK reads the key from the module global, not per-call."""
    import resend

    with patch("resend.Emails.send") as mock_send:
        mock_send.return_value = {"id": "x"}
        ResendSender(api_key="re_uniquekey_for_test", from_address="x@example.com").send(
            to="y@example.com", subject="s", body_text="t"
        )
        assert resend.api_key == "re_uniquekey_for_test"


def test_resend_sender_raises_on_missing_id_in_response():
    """If Resend returns a malformed response (no id), fail loudly — never
    silently report 'sent' for an email that wasn't."""
    with patch("resend.Emails.send") as mock_send:
        mock_send.return_value = {"error": "rate limited"}
        sender = ResendSender(api_key="re_test", from_address="x@example.com")
        try:
            sender.send(to="y@example.com", subject="s", body_text="t")
        except RuntimeError as e:
            assert "rate limited" in str(e) or "no id" in str(e).lower()
        else:
            raise AssertionError("expected RuntimeError on malformed Resend response")
