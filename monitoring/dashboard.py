"""Streamlit monitoring dashboard for the competitive intelligence agent.

Run with:  streamlit run monitoring/dashboard.py

This module is intentionally thin — all computation lives in monitoring/metrics.py
and src/state.py (both unit-tested). The dashboard only reads the database and
renders; it never writes.
"""

import sys
from pathlib import Path

# `streamlit run monitoring/dashboard.py` puts monitoring/ on sys.path but NOT
# the repo root, so `monitoring.*` and `src.*` imports would fail. Add the repo
# root before those imports. (pytest handles this via pyproject's pythonpath;
# Streamlit doesn't read that config.)
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from monitoring.metrics import summarize_runs  # noqa: E402
from src.state import RunLog  # noqa: E402

DB_PATH = REPO_ROOT / "data" / "state.db"


def _load_runs(limit: int = 60):
    if not DB_PATH.exists():
        return []
    log = RunLog(str(DB_PATH))
    try:
        return log.recent(limit=limit)
    finally:
        log.close()


def main() -> None:
    st.set_page_config(page_title="Competitive Intel — Monitoring", page_icon="📡")
    st.title("📡 Competitive Intelligence — Monitoring")

    runs = _load_runs()

    if not runs:
        st.warning(
            f"No run data found at `{DB_PATH}`. "
            "Run the agent at least once (`python -m src.main`) to populate it."
        )
        return

    summary = summarize_runs(runs)

    # --- Topline health metrics ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total runs", summary.total_runs)
    col2.metric("Success rate", f"{summary.success_rate * 100:.0f}%")
    col3.metric("Avg cost / run", f"${summary.avg_cost_usd:.3f}")
    col4.metric("Signals (all runs)", summary.total_signals)

    latest = runs[0]
    status_icon = {"success": "🟢", "partial": "🟡", "error": "🔴"}.get(latest.status, "⚪")
    st.caption(
        f"Latest run: {status_icon} {latest.status} — {latest.started_at} — "
        f"{latest.total_signals} signals — ${latest.cost_usd:.4f}"
    )
    if latest.status == "error" and latest.error:
        st.error(f"Most recent run failed: {latest.error}")

    # --- Recent runs table ---
    st.subheader("Recent runs")
    df = pd.DataFrame(
        {
            "started_at": [r.started_at for r in runs],
            "status": [r.status for r in runs],
            "competitors": [r.competitors_processed for r in runs],
            "signals": [r.total_signals for r in runs],
            "cost_usd": [round(r.cost_usd, 4) for r in runs],
            "aborted": [r.aborted_competitors or "—" for r in runs],
            "error": [r.error or "" for r in runs],
        }
    )
    st.dataframe(df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
