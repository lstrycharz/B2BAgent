"""Email delivery via Resend.

Kept narrow: one class, one public method (`send`). Conversion of the digest
to HTML is intentionally NOT done here — chunk 5 sends markdown as plain text
since most modern clients render it readably. HTML rendering is a Stage 6
iteration if recipients complain about the formatting.
"""

import resend


class ResendSender:
    """Thin Resend client wrapper for sending digest emails.

    Resend exposes its API as module-level functions, so this class is mostly
    a config-holder + validator. The benefit is having a single seam to mock
    in tests and a single place to evolve email behavior (HTML rendering,
    retry policy, etc.) without ripple changes to callers.
    """

    def __init__(self, api_key: str, from_address: str) -> None:
        self._from_address = from_address
        # The Resend SDK reads the key from a module global, not per-call.
        resend.api_key = api_key

    def send(self, to: str, subject: str, body_text: str) -> str:
        """Send a plain-text email. Returns the Resend message ID.

        Raises RuntimeError if the Resend response is missing an id (e.g.,
        rate-limit or auth error response). We do NOT want to silently
        report 'sent' for an email that never went out.
        """
        params: resend.Emails.SendParams = {
            "from": self._from_address,
            "to": [to],
            "subject": subject,
            "text": body_text,
        }
        response = resend.Emails.send(params)
        message_id = response.get("id") if isinstance(response, dict) else None
        if not message_id:
            raise RuntimeError(f"Resend returned no message id: {response!r}")
        return message_id
