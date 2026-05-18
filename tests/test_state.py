"""Tests for src/state.py — SQLite-backed deduplication of seen signals."""

import pytest

from src.stages import Signal
from src.state import SignalStore, signal_hash


def _signal(headline: str, quote: str = "Quote", sig_type: str = "product_launch") -> Signal:
    return Signal(
        signal_type=sig_type,
        headline=headline,
        detail="-",
        verbatim_quote=quote,
        source_url="https://example.com",
        significance=3,
    )


# --- signal_hash --------------------------------------------------------------

def test_signal_hash_is_stable_for_same_inputs():
    s = _signal("Linear ships X")
    assert signal_hash(s, "Linear") == signal_hash(s, "Linear")


def test_signal_hash_differs_when_headline_differs():
    a = _signal("Linear ships X")
    b = _signal("Linear ships Y")
    assert signal_hash(a, "Linear") != signal_hash(b, "Linear")


def test_signal_hash_differs_when_competitor_differs():
    """Two competitors with literally identical signal text are still distinct
    intel — don't let one mask the other."""
    s = _signal("Acquired by Big Co")
    assert signal_hash(s, "Linear") != signal_hash(s, "Asana")


def test_signal_hash_ignores_quote_variation():
    """Even at temperature=0, Claude picks slightly different quote spans from
    the same source across runs. Hashing the quote defeats dedup entirely.
    Trade-off: two genuinely-different signals with the same headline will
    collide — acceptable for marketing-digest scope where the headline IS the
    unit of intel."""
    a = _signal("Linear ships X", quote="First quote chosen by the model.")
    b = _signal("Linear ships X", quote="Different quote chosen by the model.")
    assert signal_hash(a, "Linear") == signal_hash(b, "Linear")


def test_signal_hash_normalizes_whitespace_and_case():
    """Real-world: Claude may produce 'Linear ships X' one run and 'Linear Ships X'
    the next. Treat these as the same intel."""
    a = _signal("Linear ships X")
    b = _signal("  LINEAR SHIPS X  ")
    assert signal_hash(a, "Linear") == signal_hash(b, "Linear")


# --- SignalStore --------------------------------------------------------------

@pytest.fixture
def store() -> SignalStore:
    return SignalStore(":memory:")


def test_is_new_returns_true_for_unseen_signal(store: SignalStore):
    assert store.is_new(_signal("New thing"), competitor="Linear") is True


def test_is_new_returns_false_after_mark_seen(store: SignalStore):
    s = _signal("Linear ships X")
    store.mark_seen(s, competitor="Linear")
    assert store.is_new(s, competitor="Linear") is False


def test_mark_seen_is_idempotent(store: SignalStore):
    """Marking the same signal twice must not raise (e.g., if a run is retried)."""
    s = _signal("Linear ships X")
    store.mark_seen(s, competitor="Linear")
    store.mark_seen(s, competitor="Linear")  # must not raise
    assert store.is_new(s, competitor="Linear") is False


def test_same_signal_text_different_competitor_is_still_new(store: SignalStore):
    s = _signal("Acquired by Big Co")
    store.mark_seen(s, competitor="Linear")
    assert store.is_new(s, competitor="Asana") is True


def test_store_persists_across_reopen(tmp_path):
    """Real-world: each daily run reopens the database file. State must survive."""
    db_path = str(tmp_path / "state.db")
    s = _signal("Linear ships X")

    store_a = SignalStore(db_path)
    store_a.mark_seen(s, competitor="Linear")
    store_a.close()

    store_b = SignalStore(db_path)
    assert store_b.is_new(s, competitor="Linear") is False
    store_b.close()
