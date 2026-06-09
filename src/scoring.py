from __future__ import annotations

import pandas as pd

from src.data_sources.news import score_catalyst
from src.risk_flags import build_risk_flags, flags_to_text
from src.technicals import calculate_trade_plan, technical_setup_score
from src.utils import clamp, coerce_float


def _gap_points(gap_pct: float) -> float:
    return clamp((gap_pct / 25.0) * 15.0, 0.0, 15.0)


def _premarket_volume_points(volume: float) -> float:
    return clamp((volume / 5_000_000.0) * 20.0, 0.0, 20.0)


def _relative_volume_points(relative_volume: float) -> float:
    return clamp((relative_volume / 10.0) * 15.0, 0.0, 15.0)


def _float_points(float_shares: float | None, market_cap: float | None) -> float:
    if float_shares and float_shares > 0:
        if float_shares <= 10_000_000:
            return 15.0
        if float_shares <= 30_000_000:
            return 11.0
        if float_shares <= 75_000_000:
            return 7.0
        return 2.0

    if market_cap and market_cap > 0:
        if market_cap <= 300_000_000:
            return 12.0
        if market_cap <= 1_000_000_000:
            return 8.0
        if market_cap <= 5_000_000_000:
            return 4.0
    return 0.0


def score_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame

    scored = frame.copy()
    scored["latest_price"] = scored["latest_price"].apply(coerce_float)
    scored["previous_close"] = scored["previous_close"].apply(coerce_float)
    scored["gap_pct"] = scored.apply(
        lambda row: ((row["latest_price"] - row["previous_close"]) / row["previous_close"] * 100)
        if row["previous_close"]
        else coerce_float(row.get("gap_pct")),
        axis=1,
    )
    scored["catalyst_score"] = scored.apply(
        lambda row: score_catalyst(row.get("headline"), row.get("summary")),
        axis=1,
    )
    scored["gap_points"] = scored["gap_pct"].apply(_gap_points)
    scored["premarket_volume_points"] = scored["premarket_volume"].apply(lambda value: _premarket_volume_points(coerce_float(value)))
    scored["relative_volume_points"] = scored["relative_volume"].apply(lambda value: _relative_volume_points(coerce_float(value)))
    scored["catalyst_points"] = scored["catalyst_score"].apply(lambda value: coerce_float(value) / 5.0 * 20.0)
    scored["float_points"] = scored.apply(
        lambda row: _float_points(row.get("float_shares"), row.get("market_cap")),
        axis=1,
    )
    scored["technical_points"] = scored.apply(technical_setup_score, axis=1)
    scored["total_score"] = scored[
        [
            "gap_points",
            "premarket_volume_points",
            "relative_volume_points",
            "catalyst_points",
            "float_points",
            "technical_points",
        ]
    ].sum(axis=1)

    plan_rows = scored.apply(calculate_trade_plan, axis=1, result_type="expand")
    for column in plan_rows.columns:
        scored[column] = plan_rows[column]
    scored["risk_flags_list"] = scored.apply(build_risk_flags, axis=1)
    scored["risk_flags"] = scored["risk_flags_list"].apply(flags_to_text)
    scored["total_score"] = scored["total_score"].round(1)
    scored["gap_pct"] = scored["gap_pct"].round(2)
    return scored.sort_values("total_score", ascending=False).reset_index(drop=True)
