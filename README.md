# Premarket Momentum Screener

A Python Streamlit app for ranking US stocks that may have strong intraday momentum before the market opens.

The MVP combines quote data, premarket activity, catalyst scoring, risk flags, and a simple trading-plan view. It is designed to keep running even when API keys are missing or paid real-time endpoints are unavailable by using sample fallback data.

## Features

- Top-ranked premarket momentum candidates
- Filters for gap percentage, premarket volume, price range, and market cap
- Catalyst score from recent headlines
- Risk flags for no news, offerings, reverse splits, insider selling, low liquidity, and wide spreads
- Momentum score out of 100:
  - Gap percentage: 15
  - Premarket volume: 20
  - Relative volume: 15
  - Catalyst quality: 20
  - Low float / squeeze potential: 15
  - Technical setup: 15
- Suggested trading plan:
  - Premarket high
  - Premarket low
  - VWAP
  - Opening range breakout level placeholder
  - Invalidation level
- Watchlist logging to `data/watchlist_log.csv`

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create your environment file:

```powershell
Copy-Item .env.example .env
```

Add keys to `.env`:

```text
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
FINNHUB_API_KEY=your_finnhub_key
```

Run the app:

```powershell
streamlit run app.py
```

## Data Notes

Alpaca and Finnhub are wired defensively, but real-time premarket data and complete market mover feeds often require paid data access. The code includes TODO comments where production-grade provider implementations should replace fallback behavior.

`yfinance` is included only as an optional dependency for future fallback historical data. It is not used for real-time premarket data in this MVP.

## Disclaimer

This project is for research and education. It is not financial advice. Premarket trading can be illiquid and volatile; validate all data against your broker or real-time market data provider before trading.
