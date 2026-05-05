"""
DEGIRO transaction CSV parser.
Supports two export formats:
  - Nieuw (2024+): Datum,Tijd,Product,ISIN,Beurs,...,Aantal,Koers,[cur],Lokale waarde,[cur],Waarde EUR,...
  - Oud:          Datum,Tijd,Valutadatum,Product,ISIN,Omschrijving,FX,Mutatie,[amt],Saldo,...
"""

from __future__ import annotations

import re
import pandas as pd
import numpy as np
from io import StringIO


def _parse_number(val) -> float:
    """Parse European or US formatted number string to float."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return np.nan
    s = str(val).strip().replace(" ", "")
    s = re.sub(r"[€$£¥\"]", "", s).strip()
    if not s or s in ("-", "nan", "None"):
        return np.nan
    # European: 1.234,56 → strip dots, swap comma
    if re.search(r"\d\.\d{3}", s) or (re.search(r",\d+$", s) and "." not in s):
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return np.nan


def _decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, AttributeError):
            continue
    raise ValueError("Bestand kan niet worden gelezen.")


def _read_df(text: str) -> pd.DataFrame:
    for sep in (",", ";"):
        try:
            df = pd.read_csv(StringIO(text), sep=sep, header=0, dtype=str)
            if len(df.columns) >= 6:
                return df
        except Exception:
            continue
    raise ValueError("Kan CSV-formaat niet herkennen.")


# ── Format detection ──────────────────────────────────────────────────────────

def _is_new_format(cols: list[str]) -> bool:
    """New format has 'Aantal' and 'Koers' columns, no 'Omschrijving'."""
    names = [c.lower().strip() for c in cols]
    return "aantal" in names and "koers" in names


# ── New format parser (2024+ export) ─────────────────────────────────────────
# Columns: Datum(0), Tijd(1), Product(2), ISIN(3), Beurs(4), Uitvoeringsplaats(5),
#          Aantal(6), Koers(7), [currency](8), Lokale waarde(9), [currency](10),
#          Waarde EUR(11), Wisselkoers(12), AutoFX Kosten(13), Transactiekosten(14),
#          Totaal EUR(15), Order ID(16)

def _parse_new(df: pd.DataFrame) -> tuple[list[dict], list[str]]:
    cols = [c.lower().strip() for c in df.columns]

    def ci(name: str, fallback: int) -> int:
        for i, c in enumerate(cols):
            if name in c:
                return i
        return fallback

    idx_datum   = ci("datum", 0)
    idx_product = ci("product", 2)
    idx_isin    = ci("isin", 3)
    idx_aantal  = ci("aantal", 6)
    idx_koers   = ci("koers", 7)
    idx_cur     = idx_koers + 1          # unnamed currency column right after Koers
    idx_waarde  = ci("waarde eur", 11)
    idx_order   = ci("order", 16)

    rows, warnings = [], []

    for i, row in df.iterrows():
        aantal = _parse_number(row.iloc[idx_aantal])
        if np.isnan(aantal) or aantal == 0:
            continue

        action = "buy" if aantal > 0 else "sell"
        quantity = abs(aantal)
        price = _parse_number(row.iloc[idx_koers])
        currency = str(row.iloc[idx_cur]).strip().upper() if idx_cur < len(row) else "USD"
        amount_eur = abs(_parse_number(row.iloc[idx_waarde]))

        datum_raw = str(row.iloc[idx_datum]).strip()
        try:
            date = pd.to_datetime(datum_raw, format="%d-%m-%Y")
        except Exception:
            try:
                date = pd.to_datetime(datum_raw, dayfirst=True)
            except Exception:
                warnings.append(f"Rij {i}: kan datum niet lezen: '{datum_raw}'")
                continue

        if np.isnan(amount_eur) or amount_eur == 0:
            amount_eur = quantity * price
            warnings.append(f"Rij {i}: EUR-bedrag geschat voor '{row.iloc[idx_product]}'")

        idx_beurs = ci("beurs", 4)
        rows.append({
            "date":       date,
            "product":    str(row.iloc[idx_product]).strip(),
            "isin":       str(row.iloc[idx_isin]).strip(),
            "beurs":      str(row.iloc[idx_beurs]).strip().upper(),
            "action":     action,
            "quantity":   quantity,
            "price":      price,
            "currency":   currency,
            "amount_eur": amount_eur,
            "order_id":   str(row.iloc[min(idx_order, len(row)-1)]).strip(),
        })

    return rows, warnings


# ── Old format parser (Omschrijving-based) ────────────────────────────────────

_TX_PATTERN = re.compile(
    r"^(Koop|Verkoop|Buy|Sell)\s+([\d.,]+)\s+@\s+([\d.,]+)\s+([A-Z]{3})$",
    re.IGNORECASE,
)

def _parse_old(df: pd.DataFrame) -> tuple[list[dict], list[str]]:
    cols = [c.lower().strip() for c in df.columns]

    def ci(name: str, fallback: int) -> int:
        for i, c in enumerate(cols):
            if name in c:
                return i
        return fallback

    idx_datum   = ci("datum", 0)
    idx_product = ci("product", 3)
    idx_isin    = ci("isin", 4)
    idx_omschr  = ci("omschrijving", 5)
    idx_order   = ci("order", min(11, len(cols)-1))

    idx_mutatie = ci("mutatie", 7)
    idx_amount  = idx_mutatie + 1 if idx_mutatie + 1 < len(cols) else idx_mutatie

    rows, warnings = [], []

    for i, row in df.iterrows():
        omschr = str(row.iloc[idx_omschr]).strip()
        m = _TX_PATTERN.match(omschr)
        if not m:
            continue

        action = "buy" if m.group(1).lower() in ("koop", "buy") else "sell"
        quantity = _parse_number(m.group(2))
        price    = _parse_number(m.group(3))
        currency = m.group(4).upper()

        if np.isnan(quantity) or np.isnan(price):
            warnings.append(f"Rij {i}: kan prijs/aantal niet lezen uit '{omschr}'")
            continue

        amount_eur = abs(_parse_number(row.iloc[idx_amount]))

        datum_raw = str(row.iloc[idx_datum]).strip()
        try:
            date = pd.to_datetime(datum_raw, format="%d-%m-%Y")
        except Exception:
            try:
                date = pd.to_datetime(datum_raw, dayfirst=True)
            except Exception:
                warnings.append(f"Rij {i}: kan datum niet lezen: '{datum_raw}'")
                continue

        if np.isnan(amount_eur) or amount_eur == 0:
            amount_eur = quantity * price
            warnings.append(f"Rij {i}: EUR-bedrag geschat voor '{row.iloc[idx_product]}'")

        rows.append({
            "date":       date,
            "product":    str(row.iloc[idx_product]).strip(),
            "isin":       str(row.iloc[idx_isin]).strip(),
            "beurs":      "",
            "action":     action,
            "quantity":   quantity,
            "price":      price,
            "currency":   currency,
            "amount_eur": amount_eur,
            "order_id":   str(row.iloc[min(idx_order, len(row)-1)]).strip(),
        })

    return rows, warnings


# ── Public API ────────────────────────────────────────────────────────────────

def parse_degiro_csv(uploaded_file) -> tuple[pd.DataFrame, list[str]]:
    """
    Parse a DEGIRO transacties CSV export (new or old format).

    Returns:
        (transactions_df, warnings)

    transactions_df columns:
        date, product, isin, action ('buy'|'sell'), quantity, price,
        currency, amount_eur, order_id
    """
    raw = uploaded_file.read() if hasattr(uploaded_file, "read") else open(uploaded_file, "rb").read()
    text = _decode(raw)
    df_raw = _read_df(text)

    cols = list(df_raw.columns)
    if _is_new_format(cols):
        rows, warnings = _parse_new(df_raw)
    else:
        rows, warnings = _parse_old(df_raw)

    if not rows:
        raise ValueError(
            "Geen transacties gevonden in dit bestand.\n\n"
            "Exporteer via DEGIRO: Transacties → selecteer periode → Exporteer (CSV)."
        )

    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    return df, warnings
