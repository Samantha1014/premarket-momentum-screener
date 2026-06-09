from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

from src.utils import safe_get_json


ALPACA_DATA_BASE_URL = "https://data.alpaca.markets/v2"


def _headers(api_key: str, secret_key: str) -> dict[str, str]:
    return {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key,
    }


def fetch_latest_trade(
    ticker: str,
    api_key: str | None,
    secret_key: str | None,
) -> dict[str, Any] | None:
    if not api_key or not secret_key:
        return None

    payload = safe_get_json(
        f"{ALPACA_DATA_BASE_URL}/stocks/{ticker}/trades/latest",
        headers=_headers(api_key, secret_key),
    )
    trade = payload.get("trade") if isinstance(payload, dict) else None
    if not trade:
        return None
    return {
        "latest_price": trade.get("p"),
        "latest_trade_size": trade.get("s"),
        "latest_trade_timestamp": trade.get("t"),
    }


def fetch_premarket_bars(
    ticker: str,
    api_key: str | None,
    secret_key: str | None,
) -> dict[str, Any] | None:
    if not api_key or not secret_key:
        return None

    today = datetime.now(timezone.utc).date().isoformat()
    # TODO: Accurate premarket coverage requires a paid real-time data plan.
    # This endpoint is wired defensively and will silently fall back when access
    # is denied or delayed data is insufficient.
    payload = safe_get_json(
        f"{ALPACA_DATA_BASE_URL}/stocks/{ticker}/bars",
        headers=_headers(api_key, secret_key),
        params={
            "timeframe": "1Min",
            "start": f"{today}T08:00:00Z",
            "end": f"{today}T13:30:00Z",
            "adjustment": "raw",
            "feed": "iex",
            "limit": 500,
        },
    )
    bars = payload.get("bars") if isinstance(payload, dict) else None
    if not bars:
        return None

    frame = pd.DataFrame(bars)
    if frame.empty:
        return None

    volume = float(frame["v"].sum())
    high = float(frame["h"].max())
    low = float(frame["l"].min())
    vwap = float((frame["vw"] * frame["v"]).sum() / frame["v"].sum()) if frame["v"].sum() else None
    return {
        "premarket_volume": volume,
        "premarket_high": high,
        "premarket_low": low,
        "vwap": vwap,
    }


def enrich_with_alpaca(
    row: dict[str, Any],
    api_key: str | None,
    secret_key: str | None,
) -> dict[str, Any]:
    ticker = row["ticker"]
    trade = fetch_latest_trade(ticker, api_key, secret_key) or {}
    bars = fetch_premarket_bars(ticker, api_key, secret_key) or {}
    return {**row, **trade, **bars}
