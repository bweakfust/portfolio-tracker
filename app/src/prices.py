"""
Price fetching layer with local parquet cache.
All prices are returned in EUR.
"""

from __future__ import annotations

import re
import yfinance as yf
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date, timedelta

CACHE_DIR = Path("cache")

# Currencies quoted in sub-units (pence, etc.) → divide by 100
_PENCE_CURRENCIES = {"GBp", "GBX", "ZAc"}


def _cache_path(ticker: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_\-]", "_", ticker)  # noqa: W605
    return CACHE_DIR / f"px_{safe}.parquet"


def _is_stale(path: Path) -> bool:
    """Older than 1 trading day (roughly) → refetch."""
    if not path.exists():
        return True
    age_hours = (pd.Timestamp.now() - pd.Timestamp(path.stat().st_mtime, unit="s")).total_seconds() / 3600
    # Refresh after market close (~20h since last update is fine)
    return age_hours > 20


def _fetch_raw(ticker: str, start: str) -> pd.Series:
    """Download closing prices from yfinance, return Series with tz-naive DatetimeIndex."""
    try:
        df = yf.download(
            [ticker],
            start=start,
            end=(date.today() + timedelta(days=2)).isoformat(),
            auto_adjust=True,
            progress=False,
            actions=False,
        )
        if df.empty:
            return pd.Series(dtype=float, name=ticker)

        # Flatten MultiIndex (yfinance ≥0.2.x always returns MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        close = df["Close"].copy()
        close.index = pd.to_datetime(close.index).tz_localize(None)
        close.name = ticker
        return close
    except Exception:
        return pd.Series(dtype=float, name=ticker)


def get_prices(ticker: str, start: str = "2010-01-01") -> pd.Series:
    """Raw prices in native currency, cached locally."""
    import re  # local import to avoid circular at module level
    path = _cache_path(ticker)

    if not _is_stale(path):
        try:
            df = pd.read_parquet(path)
            return df["Close"]
        except Exception:
            pass

    series = _fetch_raw(ticker, start)

    if not series.empty:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        series.rename("Close").to_frame().to_parquet(path)

    return series


def get_ticker_currency(ticker: str) -> str:
    """Return the native currency code for a ticker."""
    try:
        info = yf.Ticker(ticker).fast_info
        return getattr(info, "currency", "USD") or "USD"
    except Exception:
        return "USD"


def get_fx_series(from_currency: str, start: str = "2010-01-01") -> pd.Series:
    """Return daily from_currency→EUR exchange rate series."""
    if from_currency.upper() == "EUR":
        return pd.Series(dtype=float)  # caller should handle: multiply by 1.0
    fx_ticker = f"{from_currency.upper()}EUR=X"
    return get_prices(fx_ticker, start)


def prices_in_eur(ticker: str, start: str = "2010-01-01") -> pd.Series:
    """Return daily closing prices converted to EUR."""
    raw = get_prices(ticker, start)
    if raw.empty:
        return raw

    currency = get_ticker_currency(ticker)

    # Handle pence-quoted stocks (e.g. London-listed equities in GBp)
    if currency in _PENCE_CURRENCIES:
        raw = raw / 100
        currency = "GBP"

    if currency.upper() == "EUR":
        return raw

    fx = get_fx_series(currency, start)
    if fx.empty:
        # Fallback: no FX conversion, return raw (will be off but better than nothing)
        return raw

    # Align on trading dates
    fx_aligned = fx.reindex(raw.index).ffill().bfill()
    return raw * fx_aligned


def get_sp500(start: str = "2010-01-01") -> pd.Series:
    """S&P 500 index in USD (for benchmark, normalized so currency doesn't matter)."""
    return get_prices("^GSPC", start)


def batch_prices_eur(tickers: list[str], start: str) -> dict[str, pd.Series]:
    """Fetch EUR prices for multiple tickers. Returns {ticker: Series}."""
    result = {}
    for ticker in tickers:
        result[ticker] = prices_in_eur(ticker, start)
    return result
