from __future__ import annotations

import pandas as pd

from src.data_sources.news import detect_news_risks
from src.utils import coerce_float


def build_risk_flags(row: pd.Series) -> list[str]:
    flags = detect_news_risks(row.get("headline"), row.get("summary"))

    if coerce_float(row.get("catalyst_score")) == 0:
        flags.append("no clear news")

    premarket_volume = coerce_float(row.get("premarket_volume"))
    if premarket_volume and premarket_volume < 100_000:
        flags.append("low liquidity")

    bid = coerce_float(row.get("bid"))
    ask = coerce_float(row.get("ask"))
    latest = coerce_float(row.get("latest_price"))
    if bid > 0 and ask > bid and latest > 0:
        spread_pct = (ask - bid) / latest * 100
        if spread_pct > 1.0:
            flags.append("wide spread")

    return sorted(set(flags))


def flags_to_text(flags: list[str]) -> str:
    return ", ".join(flags) if flags else "none"
