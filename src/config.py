from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
WATCHLIST_LOG = DATA_DIR / "watchlist_log.csv"


@dataclass(frozen=True)
class Settings:
    alpaca_api_key: str | None
    alpaca_secret_key: str | None
    finnhub_api_key: str | None

    @property
    def has_alpaca(self) -> bool:
        return bool(self.alpaca_api_key and self.alpaca_secret_key)

    @property
    def has_finnhub(self) -> bool:
        return bool(self.finnhub_api_key)


def load_settings() -> Settings:
    load_dotenv(ROOT_DIR / ".env")
    return Settings(
        alpaca_api_key=os.getenv("ALPACA_API_KEY") or None,
        alpaca_secret_key=os.getenv("ALPACA_SECRET_KEY") or None,
        finnhub_api_key=os.getenv("FINNHUB_API_KEY") or None,
    )
