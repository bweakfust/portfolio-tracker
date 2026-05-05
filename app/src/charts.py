"""
Plotly chart builders for the portfolio dashboard.
Dark theme throughout.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# ── Position colour palette (shared between chart + table) ───────────────────
POSITION_COLORS = [
    "#16A34A", "#2563EB", "#7C3AED", "#EA580C",
    "#0891B2", "#DB2777", "#65A30D", "#DC2626",
    "#0D9488", "#9333EA", "#CA8A04", "#0369A1",
]

# ── Palette ───────────────────────────────────────────────────────────────────
_C = {
    "bg":       "#F4F8F5",
    "card":     "#EEF5F0",
    "border":   "#C9DFD1",
    "text":     "#0A1A0D",
    "muted":    "#527A5C",
    "blue":     "#16A34A",   # dark green — portfolio line
    "green":    "#15803D",   # positive P&L
    "red":      "#DC2626",
    "yellow":   "#CA8A04",
    "sp500":    "#78909C",   # blue-gray — S&P 500 line
}

_BASE_LAYOUT = dict(
    template="plotly_white",
    paper_bgcolor=_C["bg"],
    plot_bgcolor=_C["bg"],
    font=dict(color=_C["text"], family="'IBM Plex Sans', system-ui, sans-serif", size=12),
    margin=dict(l=10, r=10, t=36, b=10),
    xaxis=dict(showgrid=True, gridcolor=_C["card"], zeroline=False, showline=False),
    yaxis=dict(showgrid=True, gridcolor=_C["card"], zeroline=False, showline=False),
    hovermode="x unified",
    hoverlabel=dict(bgcolor=_C["card"], bordercolor=_C["border"], font_size=12,
                    font_family="'IBM Plex Mono', monospace"),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        bgcolor="rgba(0,0,0,0)",
        font=dict(size=11, color=_C["muted"]),
    ),
)


def _apply(fig: go.Figure, **overrides) -> go.Figure:
    layout = {**_BASE_LAYOUT, **overrides}
    fig.update_layout(**layout)
    return fig


# ── Chart 1: Portfolio value + invested capital ───────────────────────────────

def portfolio_value_chart(history: pd.DataFrame) -> go.Figure:
    """Absolute portfolio value vs invested capital over time."""
    if history.empty:
        return go.Figure()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=history.index, y=history["invested"].round(0),
        name="Geïnvesteerd",
        line=dict(color=_C["muted"], width=1.5, dash="dot"),
        hovertemplate="Geïnvesteerd: €%{y:,.0f}<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=history.index, y=history["value"].round(0),
        name="Portfoliowaarde",
        line=dict(color=_C["blue"], width=2.5),
        fill="tonexty",
        fillcolor="rgba(22,163,74,0.07)",
        hovertemplate="Waarde: €%{y:,.0f}<extra></extra>",
    ))

    return _apply(
        fig,
        yaxis=dict(
            title="Waarde (EUR)",
            tickprefix="€",
            showgrid=True,
            gridcolor=_C["card"],
        ),
        xaxis=dict(title="", showgrid=True, gridcolor=_C["card"]),
    )


# ── Chart 2: Normalized performance vs S&P 500 ───────────────────────────────

def performance_chart(portfolio_value: pd.Series, sp500: pd.Series) -> go.Figure:
    """
    Both series normalized to 100 at their common start date.
    Shows % return lines — scale and currency differences don't matter.
    """
    if portfolio_value.empty:
        return go.Figure()

    pv = portfolio_value.dropna()
    fig = go.Figure()

    # Align S&P 500 to portfolio dates first, so both share the same base date
    sp_aligned = pd.Series(dtype=float)
    if sp500 is not None and not sp500.empty:
        sp_aligned = sp500.reindex(pv.index, method="ffill").dropna()

    # Common start: latest first date between both series
    common_start = pv.index[0]
    if not sp_aligned.empty:
        common_start = max(pv.index[0], sp_aligned.index[0])

    pv = pv[pv.index >= common_start]
    sp_aligned = sp_aligned[sp_aligned.index >= common_start] if not sp_aligned.empty else sp_aligned

    if pv.empty:
        return go.Figure()

    # Normalize both to 100 at the common start date
    pv_norm = pv / pv.iloc[0] * 100
    end_val = pv_norm.iloc[-1]
    port_color = _C["green"] if end_val >= 100 else _C["red"]

    # If we have both, shade the area between the two lines
    sp_norm = pd.Series(dtype=float)
    if not sp_aligned.empty:
        sp_norm = sp_aligned / sp_aligned.iloc[0] * 100

    # Area between lines (portfolio vs benchmark)
    if not sp_norm.empty:
        above = pv_norm.copy()
        below = pv_norm.copy()
        above[pv_norm < sp_norm] = np.nan
        below[pv_norm >= sp_norm] = np.nan

        fig.add_trace(go.Scatter(
            x=sp_norm.index, y=sp_norm.round(2),
            name="_sp_base",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=above.index, y=above.round(2),
            name="_above",
            fill="tonexty",
            fillcolor="rgba(22,163,74,0.09)",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ))

    # Portfolio line
    fig.add_trace(go.Scatter(
        x=pv_norm.index, y=pv_norm.round(2),
        name="Mijn portfolio",
        line=dict(color=port_color, width=2.5),
        hovertemplate="Portfolio: %{y:.1f}<extra></extra>",
    ))

    # S&P 500 line
    if not sp_norm.empty:
        fig.add_trace(go.Scatter(
                x=sp_norm.index, y=sp_norm.round(2),
                name="S&P 500",
                line=dict(color=_C["sp500"], width=1.5, dash="dash"),
                hovertemplate="S&P 500: %{y:.1f}<extra></extra>",
            ))

    # Zero line at 100
    fig.add_hline(y=100, line_width=1, line_dash="dot", line_color=_C["border"])

    return _apply(
        fig,
        yaxis=dict(
            title="Geïndexeerd rendement (basis = 100)",
            showgrid=True,
            gridcolor=_C["card"],
        ),
        xaxis=dict(title="", showgrid=True, gridcolor=_C["card"]),
    )


# ── Chart 3: Allocation pie ───────────────────────────────────────────────────

def allocation_chart(positions_df: pd.DataFrame) -> go.Figure:
    """Donut chart — sorted by value desc to match table colour order."""
    if positions_df.empty or "Waarde (€)" not in positions_df.columns:
        return go.Figure()

    df = (
        positions_df[positions_df["Waarde (€)"] > 0]
        .copy()
        .sort_values("Waarde (€)", ascending=False)
        .reset_index(drop=True)
    )
    if df.empty:
        return go.Figure()

    colors = [POSITION_COLORS[i % len(POSITION_COLORS)] for i in range(len(df))]

    fig = go.Figure(go.Pie(
        labels=df["Aandeel"],
        values=df["Waarde (€)"].round(0),
        hole=0.58,
        marker=dict(colors=colors, line=dict(color=_C["bg"], width=3)),
        textinfo="none",
        hovertemplate="%{label}<br>€%{value:,.0f}<br>%{percent}<extra></extra>",
        direction="clockwise",
        sort=False,
    ))

    return _apply(
        fig,
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
    )


# ── Chart 4: P&L per position (horizontal bar) ───────────────────────────────

def pnl_bar_chart(positions_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of unrealized P&L per stock."""
    if positions_df.empty:
        return go.Figure()

    df = positions_df[["Aandeel", "Ongerealiseerd (€)", "Ongerealiseerd (%)"]].dropna()
    df = df.sort_values("Ongerealiseerd (€)")

    colors = [_C["green"] if v >= 0 else _C["red"] for v in df["Ongerealiseerd (€)"]]

    fig = go.Figure(go.Bar(
        x=df["Ongerealiseerd (€)"].round(0),
        y=df["Aandeel"],
        orientation="h",
        marker_color=colors,
        text=df["Ongerealiseerd (%)"].apply(lambda x: f"{x:+.1f}%"),
        textposition="outside",
        hovertemplate="%{y}<br>P&L: €%{x:,.0f}<extra></extra>",
    ))

    return _apply(
        fig,
        showlegend=False,
        xaxis=dict(
            title="Ongerealiseerde P&L (EUR)",
            tickprefix="€",
            showgrid=True,
            gridcolor=_C["card"],
            zeroline=True,
            zerolinecolor=_C["border"],
        ),
        yaxis=dict(title="", showgrid=False, automargin=True),
        margin=dict(l=10, r=80, t=20, b=10),
    )


# ── Chart 5: Monthly returns heatmap ─────────────────────────────────────────

def monthly_returns_heatmap(portfolio_history: pd.DataFrame) -> go.Figure:
    """Calendar heatmap of monthly portfolio returns."""
    if portfolio_history.empty:
        return go.Figure()

    monthly = portfolio_history["value"].resample("ME").last()
    monthly_ret = monthly.pct_change().dropna() * 100

    if monthly_ret.empty:
        return go.Figure()

    df = monthly_ret.reset_index()
    df.columns = ["date", "return"]
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["month_label"] = df["date"].dt.strftime("%b")

    pivot = df.pivot(index="year", columns="month", values="return")
    month_names = ["Jan", "Feb", "Mrt", "Apr", "Mei", "Jun",
                   "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"]

    pivot.columns = [month_names[c - 1] for c in pivot.columns]

    fig = go.Figure(go.Heatmap(
        z=pivot.values.round(2),
        x=list(pivot.columns),
        y=[str(y) for y in pivot.index],
        colorscale=[
            [0.0, _C["red"]],
            [0.5, "#EEF5F0"],
            [1.0, _C["green"]],
        ],
        zmid=0,
        text=np.where(
            pd.isna(pivot.values),
            "",
            [[f"{v:.1f}%" if not np.isnan(v) else "" for v in row] for row in pivot.values],
        ),
        texttemplate="%{text}",
        hovertemplate="%{y} %{x}: %{z:.2f}%<extra></extra>",
        showscale=True,
        colorbar=dict(
            title="Rendement",
            ticksuffix="%",
            len=0.8,
        ),
    ))

    return _apply(
        fig,
        xaxis=dict(title="", showgrid=False, side="top"),
        yaxis=dict(title="", showgrid=False, autorange="reversed"),
        margin=dict(l=60, r=80, t=40, b=10),
    )
