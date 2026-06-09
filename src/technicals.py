from __future__ import annotations

from typing import Any

import pandas as pd

from src.utils import coerce_float


def calculate_trade_plan(row: pd.Series) -> dict[str, float | None]:
    latest = coerce_float(row.get("latest_price"))
    premarket_high = row.get("premarket_high")
    premarket_low = row.get("premarket_low")
    vwap = row.get("vwap")

    if pd.isna(premarket_high) or not premarket_high:
        premarket_high = latest * 1.04 if latest else None
    if pd.isna(premarket_low) or not premarket_low:
        premarket_low = latest * 0.96 if latest else None
    if pd.isna(vwap) or not vwap:
        vwap = latest

    breakout = premarket_high
    invalidation = min(vwap, premarket_low) if vwap and premarket_low else premarket_low
    return {
        "premarket_high": premarket_high,
        "premarket_low": premarket_low,
        "vwap": vwap,
        "orb_level": breakout,
        "invalidation_level": invalidation,
    }


def technical_setup_score(row: pd.Series | dict[str, Any]) -> float:
    latest = coerce_float(row.get("latest_price"))
    vwap = coerce_float(row.get("vwap"), latest)
    premarket_high = coerce_float(row.get("premarket_high"), latest)
    premarket_low = coerce_float(row.get("premarket_low"), latest)

    if latest <= 0:
        return 0.0

    score = 0.0
    if latest >= vwap:
        score += 5.0
    if premarket_high and latest >= premarket_high * 0.97:
        score += 5.0
    if premarket_low and premarket_high and premarket_high > premarket_low:
        range_pct = (premarket_high - premarket_low) / latest * 100
        if 2 <= range_pct <= 18:
            score += 3.0
        elif range_pct > 18:
            score += 1.0
    gap_pct = coerce_float(row.get("gap_pct"))
    if 5 <= gap_pct <= 80:
        score += 2.0
    return min(score, 15.0)
