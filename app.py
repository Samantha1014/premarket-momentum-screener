from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import WATCHLIST_LOG, load_settings
from src.data_sources.market_data import load_market_candidates
from src.scoring import score_frame
from src.utils import fmt_large_number, utc_now_iso


st.set_page_config(
    page_title="Premarket Momentum Screener",
    layout="wide",
)


def get_scored_candidates() -> pd.DataFrame:
    settings = load_settings()
    candidates = load_market_candidates(settings)
    return score_frame(candidates)


def apply_filters(frame: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")
    min_gap = st.sidebar.slider("Minimum gap %", min_value=0.0, max_value=100.0, value=10.0, step=0.5)
    min_volume = st.sidebar.number_input("Minimum premarket volume", min_value=0, value=100_000, step=50_000)
    price_range = st.sidebar.slider("Price range", min_value=0.0, max_value=100.0, value=(0.5, 25.0), step=0.5)
    max_market_cap = st.sidebar.selectbox(
        "Market cap",
        options=[
            ("Any", None),
            ("Under $300M", 300_000_000),
            ("Under $1B", 1_000_000_000),
            ("Under $5B", 5_000_000_000),
        ],
        format_func=lambda item: item[0],
    )[1]
    hide_offerings = st.sidebar.checkbox("Hide recent offerings", value=False)
    hide_no_news = st.sidebar.checkbox("Hide no-clear-news names", value=False)

    filtered = frame[
        (frame["gap_pct"] >= min_gap)
        & (frame["premarket_volume"] >= min_volume)
        & (frame["latest_price"].between(price_range[0], price_range[1]))
    ].copy()
    if max_market_cap:
        filtered = filtered[filtered["market_cap"].fillna(float("inf")) <= max_market_cap]
    if hide_offerings:
        filtered = filtered[~filtered["risk_flags"].str.contains("recent offering", case=False, na=False)]
    if hide_no_news:
        filtered = filtered[~filtered["risk_flags"].str.contains("no clear news", case=False, na=False)]
    return filtered


def render_metric_strip(frame: pd.DataFrame) -> None:
    top = frame.iloc[0] if not frame.empty else None
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Candidates", f"{len(frame)}")
    col2.metric("Top ticker", top["ticker"] if top is not None else "N/A")
    col3.metric("Top score", f"{top['total_score']:.1f}" if top is not None else "N/A")
    col4.metric("Median gap", f"{frame['gap_pct'].median():.1f}%" if not frame.empty else "N/A")


def render_chart(frame: pd.DataFrame) -> None:
    if frame.empty:
        st.info("No candidates match the selected filters.")
        return
    chart = px.bar(
        frame.head(12),
        x="ticker",
        y="total_score",
        color="catalyst_score",
        hover_data=["gap_pct", "premarket_volume", "relative_volume", "risk_flags"],
        title="Top Momentum Scores",
        labels={"total_score": "Momentum score", "catalyst_score": "Catalyst"},
    )
    chart.update_layout(height=360, margin=dict(l=20, r=20, t=55, b=20))
    st.plotly_chart(chart, use_container_width=True)


def render_table(frame: pd.DataFrame) -> None:
    display = frame[
        [
            "ticker",
            "company_name",
            "total_score",
            "latest_price",
            "gap_pct",
            "premarket_volume",
            "relative_volume",
            "market_cap",
            "float_shares",
            "catalyst_score",
            "risk_flags",
            "headline",
        ]
    ].copy()
    display["market_cap"] = display["market_cap"].apply(fmt_large_number)
    display["float_shares"] = display["float_shares"].apply(fmt_large_number)
    st.dataframe(display, use_container_width=True, hide_index=True)


def render_trading_plan(frame: pd.DataFrame) -> None:
    if frame.empty:
        return
    selected = st.selectbox("Trading plan ticker", options=frame["ticker"].tolist())
    row = frame[frame["ticker"] == selected].iloc[0]

    st.subheader(f"{selected} Trading Plan")
    cols = st.columns(5)
    cols[0].metric("Premarket high", f"${row['premarket_high']:.2f}")
    cols[1].metric("Premarket low", f"${row['premarket_low']:.2f}")
    cols[2].metric("VWAP", f"${row['vwap']:.2f}")
    cols[3].metric("ORB level", f"${row['orb_level']:.2f}")
    cols[4].metric("Invalidation", f"${row['invalidation_level']:.2f}")

    st.write("Latest news:", row["headline"] or "No recent headline found.")
    if row.get("url"):
        st.link_button("Open news source", row["url"])
    st.warning(f"Risk flags: {row['risk_flags']}")


def append_watchlist(frame: pd.DataFrame) -> None:
    if frame.empty:
        return
    if st.button("Log visible watchlist"):
        WATCHLIST_LOG.parent.mkdir(parents=True, exist_ok=True)
        log = frame[["ticker", "total_score", "gap_pct", "premarket_volume", "catalyst_score", "risk_flags"]].copy()
        log.insert(0, "timestamp", utc_now_iso())
        header = not WATCHLIST_LOG.exists() or WATCHLIST_LOG.stat().st_size == 0
        log.to_csv(WATCHLIST_LOG, mode="a", index=False, header=header)
        st.success(f"Logged {len(log)} candidates to {WATCHLIST_LOG}")


def main() -> None:
    st.title("Premarket Momentum Screener")
    st.caption("Ranks US stocks by gap, premarket activity, catalyst quality, float profile, and technical setup.")

    scored = get_scored_candidates()
    settings = load_settings()
    if not (settings.has_alpaca and settings.has_finnhub):
        st.info("Missing one or more API keys. The app is running with sample fallback data where live fields are unavailable.")

    filtered = apply_filters(scored)
    render_metric_strip(filtered)
    render_chart(filtered)
    render_table(filtered)
    render_trading_plan(filtered)
    append_watchlist(filtered)


if __name__ == "__main__":
    main()
