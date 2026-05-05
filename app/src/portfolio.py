"""
Portfolio calculations: positions, P&L, history, CAGR, metrics.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from dataclasses import dataclass, field


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class Position:
    isin: str
    product: str
    ticker: str | None
    shares: float = 0.0
    total_cost_eur: float = 0.0        # cost basis of current holding
    fifo_lots: list = field(default_factory=list)   # [[qty, cost_per_share]]
    realized_pnl_eur: float = 0.0

    @property
    def avg_cost_eur(self) -> float:
        return self.total_cost_eur / self.shares if self.shares > 1e-6 else 0.0


# ── Position building ─────────────────────────────────────────────────────────

def build_positions(transactions: pd.DataFrame, ticker_map: dict) -> dict[str, Position]:
    """
    Walk transactions chronologically, build FIFO positions.
    Returns {isin: Position}.
    """
    positions: dict[str, Position] = {}

    for _, tx in transactions.sort_values("date").iterrows():
        isin = tx["isin"]
        if isin not in positions:
            positions[isin] = Position(
                isin=isin,
                product=tx["product"],
                ticker=ticker_map.get(isin),
            )

        pos = positions[isin]
        qty = tx["quantity"]
        amt = tx["amount_eur"]
        cost_per_share = amt / qty if qty > 1e-9 else 0.0

        if tx["action"] == "buy":
            pos.shares += qty
            pos.total_cost_eur += amt
            pos.fifo_lots.append([qty, cost_per_share])

        else:  # sell
            sell_price = amt / qty if qty > 1e-9 else 0.0
            remaining = qty

            while remaining > 1e-9 and pos.fifo_lots:
                lot_qty, lot_cost = pos.fifo_lots[0]
                sold = min(remaining, lot_qty)
                pos.realized_pnl_eur += sold * (sell_price - lot_cost)
                pos.total_cost_eur -= sold * lot_cost
                pos.fifo_lots[0][0] -= sold
                remaining -= sold
                if pos.fifo_lots[0][0] < 1e-9:
                    pos.fifo_lots.pop(0)

            pos.shares = max(pos.shares - qty, 0.0)
            pos.total_cost_eur = max(pos.total_cost_eur, 0.0)

    return positions


# ── Portfolio history ─────────────────────────────────────────────────────────

def build_portfolio_history(
    transactions: pd.DataFrame,
    ticker_map: dict[str, str | None],
    all_prices: dict[str, pd.Series],   # {ticker: EUR price Series}
) -> pd.DataFrame:
    """
    Build daily portfolio value (in EUR).

    Returns DataFrame with DatetimeIndex and columns:
        value     – total market value in EUR
        invested  – cumulative net cash invested in EUR (buys minus sell proceeds)
    """
    if transactions.empty or not all_prices:
        return pd.DataFrame()

    # Collect all trading dates from price data
    all_dates = None
    for s in all_prices.values():
        if not s.empty:
            all_dates = s.index if all_dates is None else all_dates.union(s.index)

    if all_dates is None or all_dates.empty:
        return pd.DataFrame()

    start_date = pd.Timestamp(transactions["date"].min())
    all_dates = all_dates[all_dates >= start_date]

    # Map transactions to tickers
    tx = transactions.copy()
    tx["ticker"] = tx["isin"].map(ticker_map)
    tx_valid = tx.dropna(subset=["ticker"])

    if tx_valid.empty:
        return pd.DataFrame()

    # Signed quantities and costs
    tx_valid = tx_valid.copy()
    tx_valid["signed_qty"] = np.where(tx_valid["action"] == "buy", tx_valid["quantity"], -tx_valid["quantity"])
    tx_valid["signed_cost"] = np.where(tx_valid["action"] == "buy", tx_valid["amount_eur"], -tx_valid["amount_eur"])
    tx_valid["date"] = pd.to_datetime(tx_valid["date"])

    # Pivot: date × ticker
    qty_changes = (
        tx_valid.groupby(["date", "ticker"])["signed_qty"]
        .sum()
        .unstack(fill_value=0.0)
        .reindex(all_dates, fill_value=0.0)
    )
    cost_changes = (
        tx_valid.groupby(["date", "ticker"])["signed_cost"]
        .sum()
        .unstack(fill_value=0.0)
        .reindex(all_dates, fill_value=0.0)
    )

    holdings = qty_changes.cumsum().clip(lower=0)
    invested = cost_changes.sum(axis=1).cumsum().clip(lower=0)

    # Portfolio value: holdings × EUR price
    value = pd.Series(0.0, index=all_dates)
    for ticker in holdings.columns:
        if ticker not in all_prices or all_prices[ticker].empty:
            continue
        price = all_prices[ticker].reindex(all_dates).ffill()
        value += holdings[ticker] * price.fillna(0.0)

    result = pd.DataFrame({"value": value, "invested": invested})
    result = result[result["value"] > 0.0]
    return result


# ── Positions summary table ───────────────────────────────────────────────────

def positions_summary(
    positions: dict[str, Position],
    current_prices_eur: dict[str, float],  # {isin: current price in EUR}
) -> pd.DataFrame:
    """
    Build a per-stock summary DataFrame for display.
    """
    rows = []
    for isin, pos in positions.items():
        if pos.shares < 1e-6:
            continue

        current_price = current_prices_eur.get(isin, 0.0)
        current_value = pos.shares * current_price
        unrealized = current_value - pos.total_cost_eur
        unrealized_pct = (unrealized / pos.total_cost_eur * 100) if pos.total_cost_eur > 1e-6 else 0.0

        rows.append(
            {
                "ISIN": isin,
                "Aandeel": pos.product,
                "Ticker": pos.ticker or "—",
                "Aandelen": round(pos.shares, 4),
                "Gem. kostprijs (€)": round(pos.avg_cost_eur, 2),
                "Huidige prijs (€)": round(current_price, 2),
                "Waarde (€)": round(current_value, 2),
                "Ongerealiseerd (€)": round(unrealized, 2),
                "Ongerealiseerd (%)": round(unrealized_pct, 2),
                "Gerealiseerd (€)": round(pos.realized_pnl_eur, 2),
                # keep for charts
                "_isin": isin,
                "_unrealized_pnl": unrealized,
                "_unrealized_pct": unrealized_pct,
                "_value": current_value,
            }
        )

    return pd.DataFrame(rows)


# ── Metrics ───────────────────────────────────────────────────────────────────

def calculate_cagr(start_val: float, end_val: float, start_dt, end_dt) -> float:
    years = (pd.Timestamp(end_dt) - pd.Timestamp(start_dt)).days / 365.25
    if years < 0.1 or start_val <= 0:
        return 0.0
    return (end_val / start_val) ** (1.0 / years) - 1.0


def filter_timeframe(df: pd.DataFrame | pd.Series, tf: str):
    """Slice a date-indexed series/dataframe to the given timeframe string."""
    now = pd.Timestamp.today().normalize()
    starts = {
        "1M": now - pd.DateOffset(months=1),
        "3M": now - pd.DateOffset(months=3),
        "6M": now - pd.DateOffset(months=6),
        "YTD": pd.Timestamp(now.year, 1, 1),
        "1Y": now - pd.DateOffset(years=1),
        "3Y": now - pd.DateOffset(years=3),
        "5Y": now - pd.DateOffset(years=5),
        "Alles": df.index.min() if len(df) > 0 else now,
    }
    start = starts.get(tf, df.index.min())
    return df[df.index >= start]


def _get_value_at(series: pd.Series, dt: pd.Timestamp) -> float:
    """Get portfolio value at or before a given date (last available value)."""
    available = series[series.index <= dt]
    return float(available.iloc[-1]) if not available.empty else 0.0


def _net_cash_flow_in_range(
    transactions: pd.DataFrame,
    start_dt: pd.Timestamp,
    end_dt: pd.Timestamp,
) -> float:
    """Net cash invested (buys - sells) in a half-open range (start, end]."""
    mask = (pd.to_datetime(transactions["date"]) > start_dt) & \
           (pd.to_datetime(transactions["date"]) <= end_dt)
    tx = transactions[mask]
    buys  = tx.loc[tx["action"] == "buy",  "amount_eur"].sum()
    sells = tx.loc[tx["action"] == "sell", "amount_eur"].sum()
    return float(buys - sells)


def _modified_dietz(
    v_start: float,
    v_end: float,
    transactions: pd.DataFrame,
    start_dt: pd.Timestamp,
    end_dt: pd.Timestamp,
) -> float:
    """
    Modified Dietz return — industrie standaard voor periodes met cash flows.

    Weegt elke storting/onttrekking op basis van het tijdstip in de periode,
    zodat nieuwe stortingen het rendement niet optrekken.

    Return = (V_end - V_start - NetCF) / (V_start + WeightedCF)
    """
    if v_start <= 0:
        return 0.0

    period_days = (end_dt - start_dt).days
    if period_days <= 0:
        return 0.0

    # Transacties binnen het venster (exclusief startdatum, inclusief einddatum)
    mask = (pd.to_datetime(transactions["date"]) > start_dt) & \
           (pd.to_datetime(transactions["date"]) <= end_dt)
    tx = transactions[mask]

    net_cf = 0.0
    weighted_cf = 0.0

    for _, row in tx.iterrows():
        # Buy = geld in (positief), sell = geld uit (negatief)
        cf = row["amount_eur"] if row["action"] == "buy" else -row["amount_eur"]
        days_remaining = (end_dt - pd.Timestamp(row["date"])).days
        net_cf += cf
        weighted_cf += cf * (days_remaining / period_days)

    denominator = v_start + weighted_cf
    if abs(denominator) < 1.0:
        return 0.0

    return (v_end - v_start - net_cf) / denominator


def compute_metrics(
    portfolio_history: pd.DataFrame,
    transactions: pd.DataFrame,
    positions: dict[str, Position],
    current_prices_eur: dict[str, float],
    sp500: pd.Series,
    timeframe: str = "Alles",
) -> dict:
    """Compute all summary metrics for the dashboard."""
    if portfolio_history.empty:
        return {}

    ph = filter_timeframe(portfolio_history["value"], timeframe)
    if ph.empty:
        return {}

    current_value = float(ph.iloc[-1])
    start_value   = float(ph.iloc[0])

    # Netto geïnvesteerd: direct uit transacties (inclusief tickers zonder koers)
    total_invested = float(
        transactions.loc[transactions["action"] == "buy",  "amount_eur"].sum() -
        transactions.loc[transactions["action"] == "sell", "amount_eur"].sum()
    )

    # Ongerealiseerde P&L: alleen posities met bekende huidige prijs
    unrealized = sum(
        pos.shares * current_prices_eur[isin] - pos.total_cost_eur
        for isin, pos in positions.items()
        if pos.shares > 1e-6 and isin in current_prices_eur
    )
    realized = sum(pos.realized_pnl_eur for pos in positions.values())

    # All-time: geïnvesteerd kapitaal als basis
    total_return_pct = (current_value / total_invested - 1.0) if total_invested > 1 else 0.0
    cagr_all = calculate_cagr(total_invested, current_value, portfolio_history.index.min(), pd.Timestamp.today())

    # Tijdsframe-specifiek rendement via Modified Dietz
    start_dt = ph.index[0]
    end_dt   = ph.index[-1]

    if timeframe == "Alles":
        portfolio_return_tf = total_return_pct
        cagr_tf = cagr_all
    else:
        portfolio_return_tf = _modified_dietz(start_value, current_value, transactions, start_dt, end_dt)
        years = (end_dt - start_dt).days / 365.25
        cagr_tf = (1 + portfolio_return_tf) ** (1.0 / years) - 1.0 if years > 0.1 else portfolio_return_tf

    # S&P 500 return over hetzelfde venster (simpel: begin vs eind, geen CF)
    sp_tf = filter_timeframe(sp500, timeframe)
    sp500_return = (sp_tf.iloc[-1] / sp_tf.iloc[0] - 1.0) if len(sp_tf) >= 2 and sp_tf.iloc[0] > 0 else 0.0

    vs_sp500 = portfolio_return_tf - sp500_return

    # ── Vorige periode berekeningen ────────────────────────────────────────────
    ph_full = portfolio_history["value"]

    # Absolute waardeverandering in huidige periode
    curr_cf         = _net_cash_flow_in_range(transactions, start_dt, end_dt)
    value_change    = current_value - start_value          # bruto verandering incl. stortingen
    period_gain_eur = current_value - start_value - curr_cf  # puur beleggingsrendement in €

    # Belegd in huidige periode (netto instroom)
    invested_this_period = curr_cf

    if timeframe != "Alles":
        duration       = end_dt - start_dt
        prev_end_dt    = start_dt
        prev_start_dt  = prev_end_dt - duration

        prev_val_end   = _get_value_at(ph_full, prev_end_dt)   # = start_value huidige periode
        prev_val_start = _get_value_at(ph_full, prev_start_dt)

        prev_cf        = _net_cash_flow_in_range(transactions, prev_start_dt, prev_end_dt)
        prev_return_tf = _modified_dietz(prev_val_start, prev_val_end, transactions, prev_start_dt, prev_end_dt)
        prev_gain_eur  = prev_val_end - prev_val_start - prev_cf
        prev_value_change = prev_val_end - prev_val_start
        invested_prev_period = prev_cf

        # S&P 500 vorige periode
        sp_prev = sp500
        if not sp_prev.empty:
            sp_prev_slice = sp_prev[(sp_prev.index >= prev_start_dt) & (sp_prev.index <= prev_end_dt)]
            sp500_prev_return = (
                sp_prev_slice.iloc[-1] / sp_prev_slice.iloc[0] - 1.0
                if len(sp_prev_slice) >= 2 and sp_prev_slice.iloc[0] > 0
                else 0.0
            )
        else:
            sp500_prev_return = 0.0
        prev_vs_sp500 = prev_return_tf - sp500_prev_return
    else:
        prev_return_tf       = None
        prev_gain_eur        = None
        prev_value_change    = None
        invested_prev_period = None
        prev_vs_sp500        = None

    return {
        "current_value": current_value,
        "total_invested": total_invested,
        "unrealized_pnl": unrealized,
        "realized_pnl": realized,
        "total_pnl": unrealized + realized,
        "total_return_pct": total_return_pct,
        "cagr_all": cagr_all,
        "cagr_tf": cagr_tf,
        "sp500_return": sp500_return,
        "portfolio_return_tf": portfolio_return_tf,
        "vs_sp500": vs_sp500,
        # periode-specifiek
        "value_change": value_change,
        "period_gain_eur": period_gain_eur,
        "invested_this_period": invested_this_period,
        # vorige periode
        "prev_portfolio_return_tf": prev_return_tf,
        "prev_gain_eur": prev_gain_eur,
        "prev_value_change": prev_value_change,
        "invested_prev_period": invested_prev_period,
        "prev_vs_sp500": prev_vs_sp500,
    }
