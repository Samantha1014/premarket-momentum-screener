from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from src.utils import safe_get_json


CATALYST_KEYWORDS: dict[int, tuple[str, ...]] = {
    5: (
        "fda approval",
        "approved by the fda",
        "major contract",
        "definitive merger",
        "acquisition agreement",
        "to be acquired",
        "buyout",
    ),
    4: (
        "earnings beat",
        "beats estimates",
        "raises guidance",
        "guidance raise",
        "strategic investment",
        "named partnership",
    ),
    3: (
        "strategic partnership",
        "named customer",
        "product launch",
        "commercial launch",
        "supply agreement",
    ),
    2: (
        "patent",
        "memorandum of understanding",
        "mou",
        "pilot project",
        "proof of concept",
    ),
    1: (
        "artificial intelligence",
        " ai ",
        "crypto",
        "blockchain",
        "green energy",
        "clean energy",
        "nvidia",
    ),
}

OFFERING_KEYWORDS = ("offering", "registered direct", "atm program", "warrant")
REVERSE_SPLIT_KEYWORDS = ("reverse stock split", "reverse split")
INSIDER_SELLING_KEYWORDS = ("insider selling", "form 4", "sold shares")


def score_catalyst(headline: str | None, summary: str | None = None) -> int:
    text = f" {headline or ''} {summary or ''} ".lower()
    for score in sorted(CATALYST_KEYWORDS.keys(), reverse=True):
        if any(keyword in text for keyword in CATALYST_KEYWORDS[score]):
            return score
    return 0


def detect_news_risks(headline: str | None, summary: str | None = None) -> list[str]:
    text = f" {headline or ''} {summary or ''} ".lower()
    risks: list[str] = []
    if any(keyword in text for keyword in OFFERING_KEYWORDS):
        risks.append("recent offering")
    if any(keyword in text for keyword in REVERSE_SPLIT_KEYWORDS):
        risks.append("reverse split")
    if any(keyword in text for keyword in INSIDER_SELLING_KEYWORDS):
        risks.append("insider selling")
    return risks


def fetch_latest_company_news(
    ticker: str,
    finnhub_api_key: str | None,
) -> dict[str, Any] | None:
    if not finnhub_api_key:
        return None

    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=2)
    payload = safe_get_json(
        "https://finnhub.io/api/v1/company-news",
        params={
            "symbol": ticker,
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
            "token": finnhub_api_key,
        },
    )
    if not isinstance(payload, list):
        return None

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_items = []
    for item in payload:
        published_at = datetime.fromtimestamp(item.get("datetime", 0), tz=timezone.utc)
        if published_at >= cutoff:
            recent_items.append({**item, "published_at": published_at.isoformat()})

    if not recent_items:
        return None

    latest = sorted(recent_items, key=lambda item: item.get("datetime", 0), reverse=True)[0]
    return {
        "headline": latest.get("headline"),
        "summary": latest.get("summary"),
        "url": latest.get("url"),
        "published_at": latest.get("published_at"),
    }
