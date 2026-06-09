from __future__ import annotations

from typing import Any

import pandas as pd

from src.config import Settings
from src.data_sources.alpaca import enrich_with_alpaca
from src.data_sources.finnhub import enrich_with_finnhub, fetch_us_movers
from src.data_sources.mock import load_sample_movers


MERGE_FILL_COLUMNS = [
    "company_name",
    "latest_price",
    "previous_close",
    "premarket_volume",
    "relative_volume",
    "market_cap",
    "float_shares",
    "headline",
    "summary",
    "url",
    "published_at",
    "premarket_high",
    "premarket_low",
    "vwap",
    "bid",
    "ask",
]


def _merge_with_samples(frame: pd.DataFrame) -> pd.DataFrame:
    samples = load_sample_movers()
    if frame.empty:
        return samples.assign(data_source="sample")

    merged = frame.merge(samples, on="ticker", how="outer", suffixes=("", "_sample"))
    for column in MERGE_FILL_COLUMNS:
        sample_column = f"{column}_sample"
        if column not in merged:
            merged[column] = None
        if sample_column in merged:
            merged[column] = merged[column].combine_first(merged[sample_column])
    keep = ["ticker", *MERGE_FILL_COLUMNS]
    return merged[keep].assign(data_source="api+sample_fallback")


def load_market_candidates(settings: Settings, max_live_candidates: int = 12) -> pd.DataFrame:
    movers = fetch_us_movers(settings.finnhub_api_key)
    if not movers.empty:
        movers = movers.head(max_live_candidates)

    enriched_rows: list[dict[str, Any]] = []
    for row in movers.to_dict("records"):
        with_finnhub = enrich_with_finnhub(row, settings.finnhub_api_key)
        with_alpaca = enrich_with_alpaca(
            with_finnhub,
            settings.alpaca_api_key,
            settings.alpaca_secret_key,
        )
        enriched_rows.append(with_alpaca)

    live_frame = pd.DataFrame(enriched_rows)
    return _merge_with_samples(live_frame)
