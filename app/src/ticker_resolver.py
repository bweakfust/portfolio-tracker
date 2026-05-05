"""
ISIN + DEGIRO Beurs → yfinance ticker resolution.
Uses OpenFIGI API (free, no key required) with exchange hint for accuracy.
Results cached locally; manual overrides always win.
"""

from __future__ import annotations

import json
import time
import requests
import yfinance as yf
from pathlib import Path
from typing import Optional

CACHE_DIR = Path("cache")
AUTO_CACHE = CACHE_DIR / "ticker_map_auto.json"
OVERRIDE_CACHE = CACHE_DIR / "ticker_map_override.json"

# DEGIRO Beurs code → OpenFIGI exchCode
_DEGIRO_TO_FIGI: dict[str, str] = {
    "NDQ": "UW",   # NASDAQ
    "NSY": "UN",   # NYSE
    "EAM": "NA",   # Euronext Amsterdam
    "AEX": "NA",   # Euronext Amsterdam (alt)
    "XET": "GR",   # Xetra / Frankfurt
    "EPA": "PA",   # Euronext Paris
    "LSE": "LN",   # London Stock Exchange
    "SWX": "SW",   # SIX Swiss Exchange
    "MIL": "BI",   # Borsa Italiana
    "OSL": "NO",   # Oslo Bors
    "STO": "SE",   # Nasdaq Stockholm
    "CPH": "DC",   # Nasdaq Copenhagen
    "HEL": "HE",   # Nasdaq Helsinki
    "BRU": "BB",   # Euronext Brussels
    "VIE": "VX",   # Vienna
}

# OpenFIGI exchCode → yfinance ticker suffix
_FIGI_TO_SUFFIX: dict[str, str] = {
    "UW": "",    # NASDAQ
    "UN": "",    # NYSE
    "US": "",    # US generic
    "UA": "",    # NYSE American
    "NA": ".AS",
    "GR": ".DE",
    "PA": ".PA",
    "LN": ".L",
    "SW": ".SW",
    "BI": ".MI",
    "NO": ".OL",
    "SE": ".ST",
    "DC": ".CO",
    "HE": ".HE",
    "BB": ".BR",
    "VX": ".VX",
}


def _load(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def clear_failed(max_age_days: int = 1):
    """Remove None entries older than max_age_days so they get retried."""
    auto = _load(AUTO_CACHE)
    cleaned = {k: v for k, v in auto.items() if v}
    if len(cleaned) < len(auto):
        _save(AUTO_CACHE, cleaned)


def _save(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _probe(ticker: str) -> bool:
    """Return True if yfinance can fetch recent data for this ticker."""
    try:
        hist = yf.Ticker(ticker).history(period="5d")
        return not hist.empty
    except Exception:
        return False


def _openfigi(isin: str, exch_code: Optional[str] = None) -> Optional[str]:
    """
    Query OpenFIGI to map ISIN → yfinance ticker.
    exch_code is an OpenFIGI exchCode (e.g. 'UW', 'NA') to narrow the search.
    """
    payload: dict = {"idType": "ID_ISIN", "idValue": isin}
    if exch_code:
        payload["exchCode"] = exch_code

    try:
        resp = requests.post(
            "https://api.openfigi.com/v3/mapping",
            json=[payload],
            headers={"Content-Type": "application/json"},
            timeout=6,
        )
        if resp.status_code != 200:
            return None
        body = resp.json()
        if not body or "data" not in body[0]:
            return None
        data = body[0]["data"]
        if not data:
            return None

        # Sort: prefer entries with a known suffix mapping
        def rank(item: dict) -> int:
            ec = item.get("exchCode", "")
            if ec == exch_code:
                return 0
            if ec in _FIGI_TO_SUFFIX:
                return 1
            return 2

        for item in sorted(data, key=rank):
            base = item.get("ticker", "")
            ec = item.get("exchCode", "")
            if not base:
                continue
            suffix = _FIGI_TO_SUFFIX.get(ec, "")
            for candidate in ([base + suffix] if suffix else [base, base]):
                if _probe(candidate):
                    return candidate

        return None

    except Exception:
        return None


def _resolve_one(isin: str, product: str, beurs: str) -> Optional[str]:
    """Try to resolve a single ISIN to a yfinance ticker."""
    figi_exch = _DEGIRO_TO_FIGI.get(beurs.upper())

    # 1. OpenFIGI with exchange hint (most accurate)
    if figi_exch:
        ticker = _openfigi(isin, figi_exch)
        if ticker:
            return ticker

    # 2. OpenFIGI without exchange hint (broader search)
    ticker = _openfigi(isin)
    if ticker:
        return ticker

    return None


def resolve_tickers(
    isin_info_map: dict,   # {isin: {"product": str, "beurs": str}}
    progress_callback=None,
) -> dict:
    """
    Resolve ISINs to yfinance tickers using ISIN + Beurs exchange code.

    Returns {isin: ticker_or_None}
    """
    auto = _load(AUTO_CACHE)
    overrides = _load(OVERRIDE_CACHE)

    result = {}
    pending = []

    for isin, info in isin_info_map.items():
        if isin in overrides:
            result[isin] = overrides[isin] or None
        elif isin in auto:
            result[isin] = auto[isin] or None
        else:
            pending.append((isin, info))

    for i, (isin, info) in enumerate(pending):
        if progress_callback:
            progress_callback(i + 1, len(pending), info.get("product", isin))

        ticker = _resolve_one(isin, info.get("product", ""), info.get("beurs", ""))
        auto[isin] = ticker
        result[isin] = ticker
        time.sleep(0.35)  # respect OpenFIGI free-tier rate limit

    if pending:
        _save(AUTO_CACHE, auto)

    return result


def save_override(isin: str, ticker: Optional[str]):
    overrides = _load(OVERRIDE_CACHE)
    overrides[isin] = ticker.strip().upper() if ticker and ticker.strip() else None
    _save(OVERRIDE_CACHE, overrides)


def get_overrides() -> dict:
    return _load(OVERRIDE_CACHE)
