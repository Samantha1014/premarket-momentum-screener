from __future__ import annotations

from typing import Any

import pandas as pd

from src.data_sources.news import fetch_latest_company_news
from src.utils import safe_get_json


def fetch_us_movers(api_key: str | None) -> pd.DataFrame:
    if not api_key:
        return pd.DataFrame()

    # TODO: Finnhub's free tier does not provide a complete real-time premarket
    # movers endpoint. Replace this with a paid market movers/gainers endpoint
    # when available for production use.
    payload = safe_get_json(
        "https://finnhub.io/api/v1/stock/symbol",
        params={"exchange": "US", "token": api_key},
    )
    if not isinstance(payload, list):
        return pd.DataFrame()

    candidates = [
        row.get("symbol")
        for row in payload
        if row.get("type") == "Common Stock" and row.get("symbol") and "." not in row.get("symbol", "")
    ]
    return pd.DataFrame({"ticker": candidates[:25]})


def fetch_quote(ticker: str, api_key: str | None) -> dict[str, Any] | None:
    if not api_key:
        return None

    payload = safe_get_json(
        "https://finnhub.io/api/v1/quote",
        params={"symbol": ticker, "token": api_key},
    )
    if not isinstance(payload, dict) or not payload.get("c"):
        return None
    return {
        "latest_price": payload.get("c"),
        "previous_close": payload.get("pc"),
        "day_high": payload.get("h"),
        "day_low": payload.get("l"),
    }


def fetch_company_profile(ticker: str, api_key: str | None) -> dict[str, Any] | None:
    if not api_key:
        return None

    payload = safe_get_json(
        "https://finnhub.io/api/v1/stock/profile2",
        params={"symbol": ticker, "token": api_key},
    )
    if not isinstance(payload, dict) or not payload:
        return None
    market_cap_millions = payload.get("marketCapitalization")
    return {
        "company_name": payload.get("name"),
        "market_cap": market_cap_millions * 1_000_000 if market_cap_millions else None,
        "exchange": payload.get("exchange"),
        "industry": payload.get("finnhubIndustry"),
    }


def enrich_with_finnhub(row: dict[str, Any], api_key: str | None) -> dict[str, Any]:
    ticker = row["ticker"]
    quote = fetch_quote(ticker, api_key) or {}
    profile = fetch_company_profile(ticker, api_key) or {}
    news = fetch_latest_company_news(ticker, api_key) or {}
    return {**row, **quote, **profile, **news}
