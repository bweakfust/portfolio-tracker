"""
Portfolio Tracker – DEGIRO editie
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Portfolio Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design system ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap');

/* ══════════════════════════════════════════════════════
   VARIABLES  — light mode
══════════════════════════════════════════════════════ */
:root {
  --bg:         #F4F8F5;
  --surface:    #FFFFFF;
  --card:       #FFFFFF;
  --border:     #C9DFD1;
  --accent:     #16A34A;
  --accent-dim: rgba(22,163,74,0.08);
  --accent-glow:rgba(22,163,74,0.12);
  --text:       #0A1A0D;
  --muted:      #527A5C;
  --red:        #DC2626;
  --yellow:     #CA8A04;
  --r:          10px;
}

/* ══════════════════════════════════════════════════════
   BASE
══════════════════════════════════════════════════════ */
html, body, [class*="css"] {
  font-family: 'IBM Plex Sans', system-ui, sans-serif !important;
}

/* ══════════════════════════════════════════════════════
   BACKGROUNDS
══════════════════════════════════════════════════════ */
[data-testid="stAppViewContainer"] {
  background-color: var(--bg) !important;
  background-image:
    radial-gradient(ellipse 60% 40% at 5% 0%,  rgba(22,163,74,0.06) 0%, transparent 60%),
    radial-gradient(ellipse 40% 30% at 95% 100%, rgba(22,163,74,0.04) 0%, transparent 60%);
}
[data-testid="stHeader"] {
  background: transparent !important;
  border-bottom: none !important;
}
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stToolbar"]    { display: none !important; }

/* ══════════════════════════════════════════════════════
   SIDEBAR
══════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebarContent"] { background: transparent !important; }

/* Sidebar brand */
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 4px 0 20px;
}
.sidebar-brand-dot {
  width: 8px;
  height: 8px;
  background: var(--accent);
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 6px rgba(22,163,74,0.4);
}
.sidebar-brand-text {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.82rem;
  font-weight: 500;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--text);
}
.sidebar-brand-sub {
  font-size: 0.62rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--muted);
  margin-top: 1px;
}

/* Sidebar section label */
.sidebar-section-label {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.62rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 8px;
}

/* Sidebar misc text */
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
  color: var(--muted) !important;
  font-size: 0.71rem !important;
}

/* Sidebar file uploader */
[data-testid="stSidebar"] [data-testid="stFileUploadDropzone"] {
  border-radius: 8px !important;
}

/* Sidebar widget labels */
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
  font-size: 0.68rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.07em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
}

/* ══════════════════════════════════════════════════════
   TYPOGRAPHY
══════════════════════════════════════════════════════ */
h1 {
  font-size: 1.75rem !important;
  font-weight: 300 !important;
  letter-spacing: -0.03em !important;
  color: var(--text) !important;
  line-height: 1.2 !important;
}
/* Green dot accent before the title */
h1::before {
  content: '';
  display: inline-block;
  width: 7px;
  height: 7px;
  background: var(--accent);
  border-radius: 50%;
  margin-right: 10px;
  vertical-align: middle;
  position: relative;
  top: -2px;
  box-shadow: 0 0 6px rgba(22,163,74,0.5);
}
h2, h3 {
  font-weight: 500 !important;
  letter-spacing: -0.015em !important;
  color: var(--text) !important;
}
p, li { color: var(--muted) !important; }

/* ══════════════════════════════════════════════════════
   METRIC CARDS
══════════════════════════════════════════════════════ */
[data-testid="stMetric"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-left: 2px solid var(--accent) !important;
  border-radius: var(--r) !important;
  padding: 16px 18px !important;
  transition: box-shadow 0.25s ease !important;
}
[data-testid="stMetric"]:hover {
  box-shadow:
    0 0 0 1px rgba(22,163,74,0.2),
    0 4px 20px var(--accent-glow) !important;
}

/* Label */
[data-testid="stMetricLabel"] > div,
[data-testid="stMetricLabel"] p,
[data-testid="stMetricLabel"] span {
  font-family: 'IBM Plex Sans', sans-serif !important;
  font-size: 0.65rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.09em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
}

/* Value */
[data-testid="stMetricValue"] > div {
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 1.45rem !important;
  font-weight: 500 !important;
  letter-spacing: -0.02em !important;
  color: var(--text) !important;
}

/* Delta */
[data-testid="stMetricDelta"] > div {
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.75rem !important;
}

/* ══════════════════════════════════════════════════════
   TABS
══════════════════════════════════════════════════════ */
div[data-testid="stTabs"] [role="tablist"] {
  border-bottom: 1px solid var(--border) !important;
  gap: 2px !important;
  background: transparent !important;
}
div[data-testid="stTabs"] button {
  font-family: 'IBM Plex Sans', sans-serif !important;
  font-size: 0.8rem !important;
  font-weight: 500 !important;
  color: var(--muted) !important;
  padding: 8px 18px !important;
  border-radius: 0 !important;
  border: none !important;
  transition: color 0.15s !important;
}
div[data-testid="stTabs"] button:hover {
  color: var(--text) !important;
  background: transparent !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
  color: var(--text) !important;
  border-bottom: 2px solid var(--accent) !important;
  background: transparent !important;
}

/* ══════════════════════════════════════════════════════
   RADIO → TIJDSFRAME PILLS
══════════════════════════════════════════════════════ */
[data-testid="stRadio"] [role="radiogroup"] {
  display: flex !important;
  flex-direction: row !important;
  gap: 5px !important;
  flex-wrap: wrap !important;
}
[data-testid="stRadio"] label {
  display: inline-flex !important;
  align-items: center !important;
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
  padding: 4px 13px !important;
  cursor: pointer !important;
  margin: 0 !important;
  transition: border-color 0.15s, background 0.15s !important;
}
[data-testid="stRadio"] label:hover {
  border-color: rgba(22,163,74,0.4) !important;
}
/* Hide the radio circle */
[data-testid="stRadio"] label > div:first-child {
  display: none !important;
}
[data-testid="stRadio"] label p,
[data-testid="stRadio"] label span {
  font-family: 'IBM Plex Sans', sans-serif !important;
  font-size: 0.77rem !important;
  font-weight: 500 !important;
  color: var(--muted) !important;
  letter-spacing: 0.01em !important;
}
/* Selected state */
[data-testid="stRadio"] label:has(input:checked) {
  background: var(--accent-dim) !important;
  border-color: var(--accent) !important;
}
[data-testid="stRadio"] label:has(input:checked) p,
[data-testid="stRadio"] label:has(input:checked) span {
  color: var(--accent) !important;
}

/* ══════════════════════════════════════════════════════
   BUTTONS
══════════════════════════════════════════════════════ */
.stButton > button {
  background: transparent !important;
  border: 1px solid var(--border) !important;
  color: var(--muted) !important;
  font-family: 'IBM Plex Sans', sans-serif !important;
  font-size: 0.77rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.02em !important;
  border-radius: 6px !important;
  transition: all 0.15s !important;
}
.stButton > button:hover {
  border-color: rgba(22,163,74,0.5) !important;
  color: var(--accent) !important;
  background: var(--accent-dim) !important;
  box-shadow: none !important;
}

/* ══════════════════════════════════════════════════════
   TEXT INPUTS  (ticker overrides)
══════════════════════════════════════════════════════ */
[data-testid="stTextInput"] input {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
  color: var(--text) !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.82rem !important;
}
[data-testid="stTextInput"] input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(22,163,74,0.15) !important;
}
[data-testid="stTextInput"] label p {
  color: var(--muted) !important;
  font-size: 0.72rem !important;
}

/* ══════════════════════════════════════════════════════
   FILE UPLOADER
══════════════════════════════════════════════════════ */
[data-testid="stFileUploadDropzone"] {
  background: var(--card) !important;
  border: 1px dashed var(--border) !important;
  border-radius: var(--r) !important;
  transition: border-color 0.15s !important;
}
[data-testid="stFileUploadDropzone"]:hover {
  border-color: rgba(22,163,74,0.5) !important;
}

/* ══════════════════════════════════════════════════════
   EXPANDER
══════════════════════════════════════════════════════ */
details[data-testid="stExpander"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r) !important;
}
details[data-testid="stExpander"] summary {
  color: var(--text) !important;
  font-size: 0.82rem !important;
}

/* ══════════════════════════════════════════════════════
   ALERTS
══════════════════════════════════════════════════════ */
[data-testid="stAlert"] {
  border-radius: var(--r) !important;
  font-size: 0.82rem !important;
}

/* ══════════════════════════════════════════════════════
   CAPTION / SMALL TEXT
══════════════════════════════════════════════════════ */
[data-testid="stCaptionContainer"] p,
.stCaption {
  color: var(--muted) !important;
  font-size: 0.71rem !important;
}

/* ══════════════════════════════════════════════════════
   PROGRESS BAR
══════════════════════════════════════════════════════ */
[role="progressbar"] > div {
  background: linear-gradient(90deg, var(--accent), #34D399) !important;
}

/* ══════════════════════════════════════════════════════
   DIVIDER
══════════════════════════════════════════════════════ */
hr { border-color: var(--border) !important; opacity: 0.7 !important; }

/* ══════════════════════════════════════════════════════
   DATAFRAME
══════════════════════════════════════════════════════ */
.stDataFrame {
  border: 1px solid var(--border) !important;
  border-radius: var(--r) !important;
}

/* ══════════════════════════════════════════════════════
   LAYOUT
══════════════════════════════════════════════════════ */
.block-container { padding-top: 1.5rem !important; }

/* Hide collapsed radio widget label (empty gray box) */
[data-testid="stRadio"] [data-testid="stWidgetLabel"],
[data-testid="stRadio"] > div:first-child > label {
  display: none !important;
  height: 0 !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* Force active tab underline to green */
div[data-testid="stTabs"] button[aria-selected="true"] {
  border-bottom: 2px solid var(--accent) !important;
}
div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
  background-color: var(--accent) !important;
}
div[data-testid="stTabs"] [data-baseweb="tab-border"] {
  background-color: var(--border) !important;
}

/* ══════════════════════════════════════════════════════
   SIDEBAR TOGGLE BUTTON
══════════════════════════════════════════════════════ */
/* Knop in sidebar header (collapse/expand) */
[data-testid="stSidebarHeader"] {
  padding: 12px 16px 4px !important;
}
[data-testid="stSidebarHeader"] button,
[data-testid="stSidebarCollapseButton"] button {
  color: var(--muted) !important;
  background: transparent !important;
  border: none !important;
}
[data-testid="stSidebarHeader"] button:hover,
[data-testid="stSidebarCollapseButton"] button:hover {
  color: var(--accent) !important;
  background: var(--accent-dim) !important;
}
/* Expand button (sidebar dicht) */
[data-testid="collapsedControl"] button {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-left: none !important;
  border-radius: 0 6px 6px 0 !important;
  color: var(--muted) !important;
  padding: 12px 6px !important;
  box-shadow: 2px 2px 8px rgba(0,0,0,0.08) !important;
}
[data-testid="collapsedControl"] button:hover {
  color: var(--accent) !important;
  border-color: var(--accent) !important;
}

/* ══════════════════════════════════════════════════════
   SCROLLBAR
══════════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }
</style>
""", unsafe_allow_html=True)

# ── Lazy imports (after page config) ─────────────────────────────────────────
from src.parser import parse_degiro_csv
from src.ticker_resolver import resolve_tickers, save_override, get_overrides, clear_failed
clear_failed()  # verwijder gecachede mislukte lookups zodat ze opnieuw geprobeerd worden
from src.prices import batch_prices_eur, get_sp500, prices_in_eur, get_ticker_currency
from src.portfolio import (
    build_positions,
    build_portfolio_history,
    positions_summary,
    compute_metrics,
    filter_timeframe,
)
from src.charts import (
    portfolio_value_chart,
    performance_chart,
    allocation_chart,
    pnl_bar_chart,
    monthly_returns_heatmap,
    POSITION_COLORS,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt_eur(val: float, show_sign: bool = False) -> str:
    sign = "+" if (show_sign and val > 0) else ""
    return f"{sign}€{val:,.0f}"


def fmt_pct(val: float, show_sign: bool = True) -> str:
    sign = "+" if (show_sign and val > 0) else ""
    return f"{sign}{val * 100:.1f}%"


def allocation_table_html(
    pos_df,
    colors: list,
    all_prices: dict,
    ticker_map: dict,
    current_prices_eur: dict,
    period_start,          # pd.Timestamp — start van het geselecteerde tijdsframe
    timeframe: str,
) -> str:
    """Render positions as a styled HTML table.
    Gain column reflects the selected timeframe (price return over the period).
    For 'Alles': shows all-time unrealized P&L.
    """
    import pandas as pd

    df = (
        pos_df[pos_df["Waarde (€)"] > 0]
        .copy()
        .sort_values("Waarde (€)", ascending=False)
        .reset_index(drop=True)
    )
    if df.empty:
        return ""

    total = df["Waarde (€)"].sum()
    gain_label = "Winst" if timeframe == "Alles" else f"Winst ({timeframe})"

    # Build ISIN → (gain_eur, gain_pct) lookup for the period
    isin_to_ticker = {v: k for k, v in ticker_map.items() if v}  # ticker → isin
    period_gains: dict[str, tuple] = {}  # isin → (gain_eur, gain_pct)

    for _, row in df.iterrows():
        isin   = row["ISIN"]
        ticker = ticker_map.get(isin)

        if timeframe == "Alles" or not ticker or ticker not in all_prices:
            # Fall back to all-time unrealized P&L
            period_gains[isin] = (row["Ongerealiseerd (€)"], row["Ongerealiseerd (%)"])
            continue

        price_series = all_prices[ticker].dropna()
        current_price = current_prices_eur.get(isin)
        if not current_price or price_series.empty:
            period_gains[isin] = (row["Ongerealiseerd (€)"], row["Ongerealiseerd (%)"])
            continue

        # Last available price at or before period start
        before = price_series[price_series.index <= period_start]
        if before.empty:
            period_gains[isin] = (row["Ongerealiseerd (€)"], row["Ongerealiseerd (%)"])
            continue

        start_price = float(before.iloc[-1])
        if start_price <= 0:
            period_gains[isin] = (row["Ongerealiseerd (€)"], row["Ongerealiseerd (%)"])
            continue

        gain_pct = (current_price / start_price - 1) * 100
        # Approximate € gain for current holding: shares × price_change
        # shares ≈ current_value / current_price
        shares = row["Waarde (€)"] / current_price
        gain_eur = shares * (current_price - start_price)
        period_gains[isin] = (gain_eur, gain_pct)

    rows = ""
    for i, row in df.iterrows():
        color  = colors[i % len(colors)]
        value  = row["Waarde (€)"]
        cost   = max(value - row["Ongerealiseerd (€)"], 0)
        alloc  = value / total * 100 if total > 0 else 0
        name   = str(row["Aandeel"])[:32]
        ticker = str(row["Ticker"]) if row["Ticker"] != "—" else ""
        isin   = row["ISIN"]

        gain, pct = period_gains.get(isin, (row["Ongerealiseerd (€)"], row["Ongerealiseerd (%)"]))
        gcls  = "gp" if gain >= 0 else "gn"
        gsign = "+" if gain >= 0 else ""
        psign = "+" if pct  >= 0 else ""

        rows += f"""
<div class="ar">
  <div class="arb" style="background:{color}"></div>
  <div class="arc">
    <div class="anm">{name}</div>
    <div class="atk">{ticker}</div>
  </div>
  <div class="avc">
    <div class="av1">€{value:,.0f}</div>
    <div class="av2">€{cost:,.0f}</div>
  </div>
  <div class="agc">
    <div class="ag1 {gcls}">{gsign}€{abs(gain):,.0f}</div>
    <div class="ag2 {gcls}">{psign}{pct:.1f}%</div>
  </div>
  <div class="aac">
    <div class="aa1">{alloc:.1f}%</div>
    <div class="aabar"><div class="aafill" style="width:{min(alloc,100):.1f}%;background:{color}"></div></div>
  </div>
</div>"""

    return f"""
<style>
.awt{{font-family:'IBM Plex Sans',sans-serif;width:100%;}}
.ahdr{{display:grid;grid-template-columns:4px 1fr 140px 120px 100px;gap:0 16px;
       padding:0 12px 8px 0;border-bottom:1px solid #C9DFD1;margin-bottom:4px;}}
.ahdr span{{font-size:0.62rem;font-weight:600;letter-spacing:0.08em;
            text-transform:uppercase;color:#527A5C;}}
.ahdr .ch1{{padding-left:16px;}}
.ar{{display:grid;grid-template-columns:4px 1fr 140px 120px 100px;gap:0 16px;
     align-items:center;padding:10px 12px 10px 0;border-bottom:1px solid #EDF5F0;
     transition:background 0.12s;}}
.ar:hover{{background:#F0FAF3;border-radius:8px;}}
.arb{{width:4px;height:38px;border-radius:2px;flex-shrink:0;}}
.anm{{font-size:0.85rem;font-weight:500;color:#0A1A0D;line-height:1.3;}}
.atk{{font-size:0.7rem;color:#527A5C;font-family:'IBM Plex Mono',monospace;margin-top:2px;}}
.av1{{font-family:'IBM Plex Mono',monospace;font-size:0.85rem;font-weight:500;color:#0A1A0D;}}
.av2{{font-family:'IBM Plex Mono',monospace;font-size:0.72rem;color:#527A5C;margin-top:2px;}}
.ag1{{font-family:'IBM Plex Mono',monospace;font-size:0.85rem;font-weight:500;}}
.ag2{{font-family:'IBM Plex Mono',monospace;font-size:0.72rem;margin-top:2px;}}
.gp{{color:#16A34A;}}.gn{{color:#DC2626;}}
.aa1{{font-family:'IBM Plex Mono',monospace;font-size:0.82rem;color:#0A1A0D;font-weight:500;}}
.aabar{{height:4px;background:#E8F5EC;border-radius:2px;margin-top:5px;overflow:hidden;}}
.aafill{{height:100%;border-radius:2px;}}
</style>
<div class="awt">
  <div class="ahdr">
    <span></span>
    <span class="ch1">Positie</span>
    <span>Waarde / Kostprijs</span>
    <span>{gain_label}</span>
    <span>Verdeling</span>
  </div>
  {rows}
</div>"""


SAVED_CSV = Path("data/last_upload.csv")
SAVED_META = Path("data/last_upload_meta.json")


@st.cache_data(show_spinner=False)
def cached_parse(file_bytes: bytes, file_name: str):
    """Parse is expensive; cache by file content hash."""
    import io
    return parse_degiro_csv(io.BytesIO(file_bytes))


def save_upload(file_bytes: bytes, filename: str):
    SAVED_CSV.parent.mkdir(parents=True, exist_ok=True)
    SAVED_CSV.write_bytes(file_bytes)
    import json
    from datetime import datetime
    SAVED_META.write_text(
        json.dumps({"filename": filename, "saved_at": datetime.now().strftime("%d-%m-%Y %H:%M")})
    )


def load_saved_meta() -> dict:
    if SAVED_META.exists():
        import json
        try:
            return json.loads(SAVED_META.read_text())
        except Exception:
            pass
    return {}


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
      <div class="sidebar-brand-dot"></div>
      <div>
        <div class="sidebar-brand-text">Portfolio Tracker</div>
        <div class="sidebar-brand-sub">DEGIRO · powered by yfinance</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-label">Transacties</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload DEGIRO Transacties CSV",
        type=["csv"],
        help="Ga in DEGIRO naar: Activiteiten → Transacties → Exporteer",
    )

    # Show saved file info
    meta = load_saved_meta()
    if meta and not uploaded:
        st.caption(f"🗂 Opgeslagen: **{meta.get('filename','')}**  \n{meta.get('saved_at','')}")
        if st.button("Verwijder opgeslagen data", use_container_width=True):
            SAVED_CSV.unlink(missing_ok=True)
            SAVED_META.unlink(missing_ok=True)
            st.cache_data.clear()
            st.rerun()

    st.markdown('<div style="margin: 20px 0 8px"><div class="sidebar-section-label">Instellingen</div></div>', unsafe_allow_html=True)

    if st.button("Prijzen verversen", use_container_width=True):
        # Clear price cache
        cache_dir = Path("cache")
        removed = 0
        for f in cache_dir.glob("px_*.parquet"):
            f.unlink()
            removed += 1
        st.cache_data.clear()
        st.success(f"{removed} prijsbestanden verwijderd. Herlaad de pagina.")

    st.markdown(
        "<small style='color:var(--muted);font-size:0.65rem;letter-spacing:0.03em'>Koersen zijn vertraagd · yfinance free tier</small>",
        unsafe_allow_html=True,
    )


# ── Main content ──────────────────────────────────────────────────────────────

st.markdown("# Portfolio Tracker")

if not uploaded and not SAVED_CSV.exists():
    # Welcome screen
    st.markdown("""
    ### Welkom! Upload je DEGIRO transacties om te beginnen.

    **Hoe exporteer je je transacties uit DEGIRO?**
    1. Log in op DEGIRO
    2. Ga naar **Activiteiten** (linkermenu)
    3. Klik op **Transacties**
    4. Kies een periode (zo lang mogelijk voor de beste inzichten)
    5. Klik **Exporteer** → sla op als CSV
    6. Upload het bestand hierboven ↑

    ---
    **Wat je krijgt:**
    - 📊 Portfolio waarde & P&L over tijd
    - 📈 Vergelijking met S&P 500
    - 🧮 CAGR per tijdsframe
    - 🥧 Verdeling per aandeel
    - 📅 Maandelijks rendement heatmap
    """)
    st.stop()


# ── Parse CSV ─────────────────────────────────────────────────────────────────

with st.spinner("CSV verwerken..."):
    try:
        if uploaded:
            file_bytes = uploaded.read()
            filename = uploaded.name
            save_upload(file_bytes, filename)      # persist for next session
        else:
            file_bytes = SAVED_CSV.read_bytes()
            filename = load_saved_meta().get("filename", "opgeslagen bestand")

        transactions, parse_warnings = cached_parse(file_bytes, filename)
    except Exception as e:
        st.error(f"**Fout bij inlezen:** {e}")
        st.stop()

if parse_warnings:
    with st.expander(f"⚠️ {len(parse_warnings)} waarschuwingen bij het inlezen"):
        for w in parse_warnings:
            st.caption(w)



# ── Ticker resolution ─────────────────────────────────────────────────────────

# Build {isin: {product, beurs}} for resolver
isin_info = (
    transactions.groupby("isin")
    .agg(product=("product", "first"), beurs=("beurs", "first"))
    .to_dict("index")
)
isin_product_map = {isin: info["product"] for isin, info in isin_info.items()}

# Load cached + overrides
overrides = get_overrides()

if "ticker_map" not in st.session_state:
    st.session_state.ticker_map = {}

# Find ISINs not yet resolved in session
unresolved = {
    isin: info
    for isin, info in isin_info.items()
    if isin not in st.session_state.ticker_map
}

if unresolved:
    def _progress(i, total, name):
        _bar.progress(i / total, text=f"Ticker ophalen: {name} ({i}/{total})")

    _bar = st.progress(0, text="Tickers ophalen via OpenFIGI (ISIN + Beurs)...")
    resolved = resolve_tickers(unresolved, progress_callback=_progress)
    _bar.empty()
    st.session_state.ticker_map.update(resolved)

ticker_map = st.session_state.ticker_map.copy()
# Apply manual overrides
ticker_map.update({k: v for k, v in overrides.items() if v})

# Show unresolved tickers + manual input
missing = {isin: isin_product_map[isin] for isin, t in ticker_map.items() if not t and isin in isin_product_map}

if missing:
    st.warning(
        f"**{len(missing)} tickers niet gevonden.** "
        "Voer de yfinance ticker handmatig in (bijv. ASML.AS, ADYEN.AS, VOW3.DE)."
    )
    with st.expander("Tickers handmatig invullen", expanded=True):
        cols = st.columns(3)
        for i, (isin, product) in enumerate(missing.items()):
            col = cols[i % 3]
            val = col.text_input(f"{product[:30]}", key=f"ticker_{isin}", placeholder="bijv. ASML.AS")
            if val:
                save_override(isin, val)
                ticker_map[isin] = val.strip().upper()
                st.session_state.ticker_map[isin] = val.strip().upper()


# ── Fetch prices ──────────────────────────────────────────────────────────────

active_tickers = list({t for t in ticker_map.values() if t})
start_date = transactions["date"].min().strftime("%Y-%m-%d")

if not active_tickers:
    st.error("Geen geldige tickers gevonden. Voer tickers handmatig in.")
    st.stop()

with st.spinner(f"Koersdata ophalen voor {len(active_tickers)} aandelen..."):
    all_prices = batch_prices_eur(active_tickers, start_date)
    sp500 = get_sp500(start_date)

# Get current prices per ISIN (most recent price)
current_prices_eur: dict[str, float] = {}
for isin, ticker in ticker_map.items():
    if ticker and ticker in all_prices and not all_prices[ticker].empty:
        current_prices_eur[isin] = float(all_prices[ticker].dropna().iloc[-1])


# ── Build portfolio ────────────────────────────────────────────────────────────

positions = build_positions(transactions, ticker_map)
portfolio_history = build_portfolio_history(transactions, ticker_map, all_prices)
pos_df = positions_summary(positions, current_prices_eur)

if portfolio_history.empty:
    st.error(
        "Kan geen portfoliogeschiedenis berekenen. "
        "Controleer of de tickers correct zijn opgegeven."
    )
    st.stop()


# ── Tijdsframe selector ────────────────────────────────────────────────────────

active_count = len(pos_df) if not pos_df.empty else 0
found_count  = transactions["isin"].nunique()
tx_count     = len(transactions)

st.markdown("---")
timeframe = st.radio(
    "Tijdsframe",
    options=["1M", "3M", "6M", "YTD", "1Y", "3Y", "5Y", "Alles"],
    index=7,
    horizontal=True,
    label_visibility="collapsed",
)

st.caption(
    f"{tx_count} transacties · "
    f"{found_count} aandelen gevonden · "
    f"{active_count} actief in portfolio · "
    f"Tijdsframe: {timeframe}"
)
st.markdown("---")


# Filter history to selected timeframe
ph_filtered = filter_timeframe(portfolio_history, timeframe)
metrics = compute_metrics(portfolio_history, transactions, positions, current_prices_eur, sp500, timeframe)


# ── Scorecards ────────────────────────────────────────────────────────────────

show_cagr = timeframe in ("3Y", "5Y", "Alles")
is_all    = timeframe == "Alles"

# Hulpwaarden
curr_val    = metrics.get("current_value", 0)
val_change  = metrics.get("value_change", 0)
prev_val_ch = metrics.get("prev_value_change")
ret_tf      = metrics.get("portfolio_return_tf", 0)
prev_ret    = metrics.get("prev_portfolio_return_tf")
gain_eur    = metrics.get("period_gain_eur", 0)
prev_gain   = metrics.get("prev_gain_eur")
invested    = metrics.get("total_invested", 0)
inv_this    = metrics.get("invested_this_period", 0)
inv_prev    = metrics.get("invested_prev_period")
vs_sp       = metrics.get("vs_sp500", 0)
prev_vs_sp  = metrics.get("prev_vs_sp500")

k1, k2, k3, k4, k5 = st.columns(5)

# ── K1: Portfoliowaarde ────────────────────────────────────────────────────────
with k1:
    if is_all:
        delta1 = fmt_eur(metrics.get("total_pnl", 0), show_sign=True)
        help1  = "All-time ongerealiseerde winst/verlies"
    else:
        delta1 = fmt_eur(val_change, show_sign=True)
        help1  = f"Waardeverandering deze {timeframe} (inclusief nieuwe stortingen)"
    st.metric("Portfoliowaarde", fmt_eur(curr_val), delta=delta1, delta_color="normal", help=help1)

# ── K2: Rendement % ───────────────────────────────────────────────────────────
with k2:
    if is_all:
        delta2 = None
        help2  = "Totaalrendement vs netto geïnvesteerd kapitaal"
    elif prev_ret is not None:
        diff_pp = ret_tf - prev_ret
        delta2  = fmt_pct(diff_pp, show_sign=True)
        help2   = f"Verschil in rendement vs vorige {timeframe} ({fmt_pct(prev_ret)}). Modified Dietz, gecorrigeerd voor stortingen."
    else:
        delta2 = None
        help2  = "Modified Dietz, gecorrigeerd voor stortingen"
    st.metric(f"Rendement", fmt_pct(ret_tf), delta=delta2, delta_color="normal", help=help2)

# ── K3: CAGR (3Y/5Y/Alles) of Rendement in € (overige) ───────────────────────
with k3:
    if show_cagr:
        label3 = "CAGR"
        delta3 = fmt_pct(metrics.get("cagr_all", 0)) if not is_all else None
        help3  = "Samengesteld jaarlijks groeipercentage van dit tijdsframe" if not is_all else "All-time CAGR"
        st.metric(label3, fmt_pct(metrics.get("cagr_tf", 0)), delta=delta3, delta_color="off", help=help3)
    else:
        if prev_gain is not None:
            diff_eur = gain_eur - prev_gain
            delta3   = fmt_eur(diff_eur, show_sign=True)
            help3    = f"Verschil in rendement (€) vs vorige {timeframe} ({fmt_eur(prev_gain, show_sign=True)}). Excl. nieuwe stortingen."
        else:
            delta3 = None
            help3  = "Puur beleggingsrendement in €, exclusief nieuwe stortingen"
        st.metric("Rendement in €", fmt_eur(gain_eur, show_sign=True), delta=delta3, delta_color="normal", help=help3)

# ── K4: Belegd bedrag ─────────────────────────────────────────────────────────
with k4:
    if is_all:
        st.metric("Belegd", fmt_eur(invested), delta=None,
                  help="Totaal netto geïnvesteerd all-time (aankopen minus verkoopopbrengsten)")
    else:
        if inv_prev is not None and inv_prev != 0:
            diff_inv = inv_this - inv_prev
            delta4   = fmt_eur(diff_inv, show_sign=True)
            help4    = f"Verschil in inleg vs vorige {timeframe} ({fmt_eur(inv_prev, show_sign=True)})"
        elif inv_this != 0:
            delta4 = fmt_eur(inv_this, show_sign=True)
            help4  = f"Netto inleg deze {timeframe}"
        else:
            delta4 = None
            help4  = f"Geen inleg deze {timeframe}"
        st.metric("Belegd", fmt_eur(invested), delta=delta4, delta_color="off", help=help4)

# ── K5: vs S&P 500 ────────────────────────────────────────────────────────────
with k5:
    if prev_vs_sp is not None:
        diff_alpha = vs_sp - prev_vs_sp
        delta5     = fmt_pct(diff_alpha, show_sign=True)
        help5      = f"Verschil in alpha vs vorige {timeframe} ({fmt_pct(prev_vs_sp, show_sign=True)}). Portfolio {fmt_pct(ret_tf)} / S&P {fmt_pct(metrics.get('sp500_return', 0))}."
    else:
        delta5 = None
        help5  = f"Portfolio {fmt_pct(ret_tf)} vs S&P {fmt_pct(metrics.get('sp500_return', 0))}"
    st.metric("vs S&P 500", fmt_pct(vs_sp, show_sign=True), delta=delta5, delta_color="normal", help=help5)

if timeframe != "Alles":
    st.caption("\\* Rendement gecorrigeerd voor stortingen/onttrekkingen via Modified Dietz methode.")

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs([
    "Portfoliowaarde",
    "vs S&P 500",
    "Verdeling",
])


# ── Tab 1: Portfolio value ────────────────────────────────────────────────────
with tab1:
    st.plotly_chart(
        portfolio_value_chart(ph_filtered),
        use_container_width=True,
        config={"displayModeBar": False},
    )


# ── Tab 2: Benchmark ──────────────────────────────────────────────────────────
with tab2:
    pv_filtered = filter_timeframe(portfolio_history["value"], timeframe)
    sp_filtered  = filter_timeframe(sp500, timeframe) if not sp500.empty else pd.Series(dtype=float)
    st.plotly_chart(
        performance_chart(pv_filtered, sp_filtered),
        use_container_width=True,
        config={"displayModeBar": False},
    )
    st.caption(
        "Beide lijnen genormaliseerd naar 100 op de eerste dag van het tijdsframe. "
        "Groen vlak = portfolio boven S&P 500."
    )


# ── Tab 3: Allocation ─────────────────────────────────────────────────────────
with tab3:
    if not pos_df.empty:
        col_donut, col_table = st.columns([4, 6], gap="large")

        with col_donut:
            st.plotly_chart(
                allocation_chart(pos_df),
                use_container_width=True,
                config={"displayModeBar": False},
            )

        with col_table:
            period_start = ph_filtered.index[0] if not ph_filtered.empty else pd.Timestamp.today()
            st.markdown(
                allocation_table_html(
                    pos_df,
                    POSITION_COLORS,
                    all_prices,
                    ticker_map,
                    current_prices_eur,
                    period_start,
                    timeframe,
                ),
                unsafe_allow_html=True,
            )
    else:
        st.info("Geen open posities gevonden.")

