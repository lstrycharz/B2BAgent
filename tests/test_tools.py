"""Tests for src/tools.py — HTTP fetching with security guards + HTML stripping."""

import httpx
import pytest
import respx

from src.tools import fetch_with_guards, html_to_text

ALLOWED = {"linear.app"}


def test_fetch_rejects_host_not_in_allowlist():
    with pytest.raises(ValueError, match="not in allowlist"):
        fetch_with_guards("https://evil.example.com/page", allowed_hosts=ALLOWED)


@respx.mock
def test_fetch_returns_body_for_allowlisted_host():
    respx.get("https://linear.app/pricing").mock(
        return_value=httpx.Response(200, text="<html>Linear pricing</html>")
    )
    body = fetch_with_guards("https://linear.app/pricing", allowed_hosts=ALLOWED)
    assert "Linear pricing" in body


@respx.mock
def test_fetch_resolves_relative_redirect_urls():
    """A relative Location header (e.g. '/new-path') must resolve against the
    original URL, not be treated as an absolute URL. Without this, Asana's edge
    redirect to '/blog-edge-redirect/feed/' fails with 'unknown url type'."""
    respx.get("https://linear.app/pricing").mock(
        return_value=httpx.Response(302, headers={"location": "/pricing-v2"})
    )
    respx.get("https://linear.app/pricing-v2").mock(
        return_value=httpx.Response(200, text="<html>new pricing</html>")
    )
    body = fetch_with_guards("https://linear.app/pricing", allowed_hosts=ALLOWED)
    assert "new pricing" in body


@respx.mock
def test_fetch_rejects_redirect_to_non_allowlisted_host():
    respx.get("https://linear.app/pricing").mock(
        return_value=httpx.Response(302, headers={"location": "https://evil.example.com/x"})
    )
    with pytest.raises(ValueError, match="not in allowlist"):
        fetch_with_guards("https://linear.app/pricing", allowed_hosts=ALLOWED)


def test_html_to_text_strips_scripts_and_styles():
    html = """
    <html>
      <head><style>body{color:red}</style></head>
      <body>
        <script>alert('xss')</script>
        <h1>Pricing</h1>
        <p>$10/user</p>
      </body>
    </html>
    """
    text = html_to_text(html)
    assert "Pricing" in text
    assert "$10/user" in text
    assert "alert" not in text
    assert "color:red" not in text


def test_html_to_text_collapses_blank_lines():
    html = "<p>Line one</p>\n\n\n<p>Line two</p>"
    text = html_to_text(html)
    # No more than a single newline between content lines
    assert "\n\n" not in text
