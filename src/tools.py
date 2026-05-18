"""HTTP fetching and HTML cleaning with security guards.

Security model (per ~/.claude/rules/security.md):
- Explicit timeout on every request
- Response size capped via streaming (not download-then-truncate)
- Manual redirect handling so each hop is re-validated against the host allowlist
- Caller provides the allowlist, so this module has no implicit trust assumptions
"""

import httpx
from bs4 import BeautifulSoup

_REQUEST_TIMEOUT_SECONDS = 15.0
_MAX_BYTES_PER_FETCH = 5 * 1024 * 1024  # 5 MB
_MAX_REDIRECTS = 3
_USER_AGENT = "Mozilla/5.0 (compatible; B2BAgent/0.1; +contact@example.com)"


def fetch_with_guards(url: str, allowed_hosts: set[str] | frozenset[str]) -> str:
    """Fetch a URL safely. Raises ValueError if host (or any redirect target)
    is not in `allowed_hosts`.

    Returns the response body as a UTF-8 string (errors replaced).
    """
    if httpx.URL(url).host not in allowed_hosts:
        raise ValueError(f"Host {httpx.URL(url).host!r} not in allowlist")

    with httpx.Client(
        timeout=_REQUEST_TIMEOUT_SECONDS,
        follow_redirects=False,
        headers={"User-Agent": _USER_AGENT},
    ) as http:
        current_url = url
        for _ in range(_MAX_REDIRECTS + 1):
            with http.stream("GET", current_url) as response:
                if response.status_code in (301, 302, 307, 308):
                    raw_location = response.headers.get("location", "")
                    if not raw_location:
                        raise RuntimeError(f"Redirect with no location header at {current_url}")
                    # Relative Location headers must resolve against the current URL.
                    next_url = str(httpx.URL(current_url).join(raw_location))
                    next_host = httpx.URL(next_url).host
                    if next_host and next_host not in allowed_hosts:
                        raise ValueError(f"Redirect target host {next_host!r} not in allowlist")
                    current_url = next_url
                    continue

                response.raise_for_status()
                chunks: list[bytes] = []
                received = 0
                for chunk in response.iter_bytes(chunk_size=65536):
                    chunks.append(chunk)
                    received += len(chunk)
                    if received >= _MAX_BYTES_PER_FETCH:
                        break
                return b"".join(chunks).decode("utf-8", errors="replace")
        raise RuntimeError(f"Too many redirects starting from {url}")


def html_to_text(html: str) -> str:
    """Strip HTML to readable text. Drops scripts, styles, and noise tags."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "link", "meta"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    lines = [ln for ln in (line.strip() for line in text.splitlines()) if ln]
    return "\n".join(lines)
