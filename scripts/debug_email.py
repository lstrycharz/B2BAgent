"""Diagnose Resend email failures in isolation.

Run with: python scripts/debug_email.py

Tests two send variations and prints the exact Resend response (or exception)
for each, so we can see what's actually being rejected.
"""

import os
import sys
import traceback
from pathlib import Path

import resend
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

api_key = os.environ.get("RESEND_API_KEY")
# Recipient: prefer CLI arg, fall back to .env
recipient = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DIGEST_RECIPIENT_EMAIL")

if not api_key:
    print("RESEND_API_KEY not in .env — abort")
    sys.exit(1)
if not recipient:
    print("Recipient not given. Pass as arg: python scripts/debug_email.py you@gmail.com")
    print("(or add DIGEST_RECIPIENT_EMAIL to .env)")
    sys.exit(1)

resend.api_key = api_key
print(f"Recipient: {recipient}")
print(f"API key starts with: {api_key[:10]}...  (length {len(api_key)})")
print()


def try_send(label: str, params: dict) -> None:
    print(f"=== {label} ===")
    print(f"  from:    {params['from']!r}")
    print(f"  to:      {params['to']!r}")
    print(f"  subject: {params['subject']!r}")
    try:
        response = resend.Emails.send(params)
        print(f"  response: {response!r}")
    except Exception as e:
        print(f"  EXCEPTION type:    {type(e).__name__}")
        print(f"  EXCEPTION message: {e}")
        print(f"  --- traceback ---")
        traceback.print_exc()
    print()


# Variation 1: bare email as sender
try_send(
    "V1 — bare 'onboarding@resend.dev'",
    {
        "from": "onboarding@resend.dev",
        "to": [recipient],
        "subject": "B2BAgent debug — V1",
        "text": "test",
    },
)

# Variation 2: display-name format
try_send(
    "V2 — 'Acme <onboarding@resend.dev>' display-name form",
    {
        "from": "Acme <onboarding@resend.dev>",
        "to": [recipient],
        "subject": "B2BAgent debug — V2",
        "text": "test",
    },
)
