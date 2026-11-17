import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, date, time as dtime
from zoneinfo import ZoneInfo
import uuid
import io
from concurrent.futures import ThreadPoolExecutor

# ---------- Page Setup ----------
st.set_page_config(
    page_title="Pro Day Trade Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern Cyber-Terminal Dark Theme CSS with Fixes for Expanders and Form Contrast
st.markdown("""
<style>
:root {
  --terminal-bg: #080c13;
  --panel: #101824;
  --panel-soft: #131e2c;
  --line: #243247;
  --muted: #91a2b8;
  --text: #e8eef7;
  --accent: #38bdf8;
  --green: #20c997;
  --red: #fb7185;
}
.stApp { background: radial-gradient(ellipse at 50% -18%, #17283d 0%, #0a101a 42%, var(--terminal-bg) 78%); color: var(--text); }
.block-container { max-width: 1840px; padding: 1.15rem clamp(.85rem, 2vw, 2rem) 2.5rem; }
header[data-testid="stHeader"] { background: rgba(8,12,19,.78); }
[data-testid="stAppViewContainer"] > .main { background: transparent; }
h1,h2,h3,h4 { color: #f4f8ff !important; letter-spacing: -.025em; }
h1 { font-weight: 850 !important; }
h2,h3 { font-weight: 750 !important; }
p, label, .stMarkdown, .stCaption { overflow-wrap: anywhere; }
.stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }
hr { border-color: #263449 !important; margin: 1.25rem 0 !important; }
/* Sidebar */
section[data-testid="stSidebar"] { background: linear-gradient(180deg,#101a28 0%,#0b111b 100%); border-right: 1px solid #263449; }
section[data-testid="stSidebar"] > div { padding-top: 1.2rem; }
section[data-testid="stSidebar"] h3 { color: #f2f7ff !important; }
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { color: #dce6f3 !important; }
/* Inputs */
.stTextInput input, .stNumberInput input, .stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div, .stTextArea textarea {
  background: #0b1320 !important; color: #edf5ff !important;
  border: 1px solid #2a3b52 !important; border-radius: 9px !important;
}
[data-baseweb="popover"] { color: #eaf1fb; }
/* Buttons */
.stButton button, .stDownloadButton button {
  border: 1px solid #344861; border-radius: 9px; font-weight: 650;
  transition: border-color .16s ease, background .16s ease, transform .16s ease;
  min-height: 2.55rem; white-space: normal;
}
.stButton button:hover, .stDownloadButton button:hover { border-color: #56b4e9; transform: translateY(-1px); }
.stButton button[kind="primary"] { background: linear-gradient(135deg,#087cae,#155e9a); border-color: #269bd0; color: white; }
section[data-testid="stSidebar"] .stButton button { background: #172438; color: #eaf2fc; border-color: #30445e; }
/* Cards and metrics */
div[data-testid="stMetric"] {
  background: linear-gradient(145deg,rgba(20,32,48,.96),rgba(13,22,34,.96));
  border: 1px solid #293b52; border-radius: 13px; padding: 13px 15px;
  box-shadow: 0 7px 22px rgba(0,0,0,.18); min-width: 0; overflow-wrap: anywhere;
}
div[data-testid="stMetric"] label { color: #9fb1c8 !important; font-size: .82rem !important; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #f5f9ff !important; font-weight: 760; font-size: clamp(1.1rem,1.7vw,1.55rem) !important; }
/* Data tables, charts, expanders */
div[data-testid="stDataFrame"], div[data-testid="stPlotlyChart"] { width: 100%; max-width: 100%; }
div[data-testid="stDataFrame"] { border: 1px solid #26364b; border-radius: 11px; overflow: hidden; }
div[data-testid="stExpander"] { background: rgba(16,25,39,.88); border: 1px solid #293b52; border-radius: 11px; }
div[data-testid="stExpander"] summary { color: #e8f0fb !important; font-weight: 650; }
div[data-testid="stAlert"] { border-radius: 10px; }
/* Signal banner */
.action-banner { font-size: clamp(1.2rem,2.2vw,1.75rem); font-weight: 850; text-align: center; padding: 13px 16px; border-radius: 12px; margin: 12px 0 16px; letter-spacing: .035em; box-shadow: 0 8px 24px rgba(0,0,0,.24); }
.buy { background: linear-gradient(110deg,#087f5b,#0c9b70); color: white; border: 1px solid #31c99a; }
.short { background: linear-gradient(110deg,#a92c43,#d34257); color: white; border: 1px solid #fa7185; }
.watch { background: linear-gradient(110deg,#174b82,#176ca5); color: white; border: 1px solid #3b9ed5; }
/* Hover information icons */
.info-tip { display:inline-flex; align-items:center; justify-content:center; width:17px; height:17px; margin-left:5px; border:1px solid #4b7595; border-radius:50%; color:#8ed8ff; font-size:11px; font-weight:800; cursor:help; vertical-align:middle; position:relative; }
.info-tip:hover { background:#12324a; border-color:#75cfff; color:#fff; }
.info-tip[title]:hover::after { content:attr(title); position:absolute; z-index:99999; left:50%; top:calc(100% + 8px); transform:translateX(-50%); width:230px; white-space:normal; padding:9px 11px; border:1px solid #41617e; border-radius:8px; background:#101c2b; color:#eaf4ff; font-size:12px; line-height:1.4; font-weight:500; box-shadow:0 8px 22px rgba(0,0,0,.45); pointer-events:none; }
/* Compact section labels */
.terminal-kicker { color:#72c9f2; text-transform:uppercase; letter-spacing:.16em; font-size:.72rem; font-weight:800; }
.terminal-hero { padding: 1.05rem 1.25rem; margin: .2rem 0 1rem; border:1px solid #2b4059; border-radius:15px; background:linear-gradient(115deg,rgba(20,40,62,.96),rgba(12,20,32,.96)); box-shadow:0 12px 30px rgba(0,0,0,.22); }
.terminal-hero h1 { margin:.2rem 0 .25rem; font-size:clamp(1.55rem,3vw,2.25rem); }
.terminal-hero p { margin:0; color:#a9bbd1; }
@media (max-width: 1100px) {
  div[data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap:.7rem; }
  div[data-testid="column"] { min-width:min(100%,220px) !important; }
}
@media (max-width: 700px) {
  .block-container { padding-left:.7rem; padding-right:.7rem; }
  .terminal-hero { padding:.85rem; }
  div[data-testid="stMetric"] { padding:10px; }
}
</style>
""", unsafe_allow_html=True)


def info_heading(label, explanation, level=3):
    """Render a compact heading with a hover-only explanation icon."""
    safe_label = str(label).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    safe_tip = str(explanation).replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    st.markdown(f'<h{level} style="margin:.35rem 0 .55rem">{safe_label}<span class="info-tip" title="{safe_tip}" aria-label="More information">i</span></h{level}>', unsafe_allow_html=True)

# ---------- Yahoo Finance symbol search / recommendations ----------
@st.cache_data(ttl=900, show_spinner=False)
def search_stock_symbols(query):
    """Search Yahoo Finance for equities, ETFs, and cryptocurrency pairs."""
    query = str(query or "").strip()
    if len(query) < 1:
        return []
    try:
        result = yf.Search(query, max_results=15)
        quotes = getattr(result, "quotes", []) or []
        matches = []
        for item in quotes:
            quote_type = str(item.get("quoteType", "")).upper()
            symbol = str(item.get("symbol", "")).upper()
            if symbol and quote_type in {"EQUITY", "ETF", "CRYPTOCURRENCY", "CRYPTO"}:
                matches.append({
                    "symbol": symbol,
                    "name": item.get("shortname") or item.get("longname") or ASSET_NAMES.get(symbol, symbol),
                    "type": "CRYPTO" if quote_type in {"CRYPTOCURRENCY", "CRYPTO"} else quote_type
                })
        return matches
    except Exception:
        return []

ASSET_NAMES = {
    "SPY": "SPDR S&P 500 ETF", "QQQ": "Invesco QQQ Trust", "IWM": "iShares Russell 2000 ETF",
    "DIA": "SPDR Dow Jones Industrial Average ETF", "AAPL": "Apple Inc.", "MSFT": "Microsoft Corporation",
    "NVDA": "NVIDIA Corporation", "AMD": "Advanced Micro Devices", "AMZN": "Amazon.com Inc.",
    "META": "Meta Platforms Inc.", "GOOGL": "Alphabet Inc.", "TSLA": "Tesla Inc.",
    "AVGO": "Broadcom Inc.", "NFLX": "Netflix Inc.", "JPM": "JPMorgan Chase & Co.",
    "XOM": "Exxon Mobil Corporation", "LLY": "Eli Lilly and Company", "COST": "Costco Wholesale",
    "PLTR": "Palantir Technologies", "ORCL": "Oracle Corporation",
    "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana", "XRP-USD": "XRP",
    "BNB-USD": "BNB", "DOGE-USD": "Dogecoin", "ADA-USD": "Cardano", "AVAX-USD": "Avalanche",
    "LINK-USD": "Chainlink", "LTC-USD": "Litecoin", "BCH-USD": "Bitcoin Cash", "DOT-USD": "Polkadot"
}
STOCK_RECOMMENDATION_UNIVERSE = [
    "SPY", "QQQ", "IWM", "DIA", "AAPL", "MSFT", "NVDA", "AMD", "AMZN", "META",
    "GOOGL", "TSLA", "AVGO", "NFLX", "JPM", "XOM", "LLY", "COST", "PLTR", "ORCL"
]
CRYPTO_RECOMMENDATION_UNIVERSE = [
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "BNB-USD", "DOGE-USD",
    "ADA-USD", "AVAX-USD", "LINK-USD", "LTC-USD", "BCH-USD", "DOT-USD"
]
RECOMMENDATION_UNIVERSE = STOCK_RECOMMENDATION_UNIVERSE + CRYPTO_RECOMMENDATION_UNIVERSE


def display_asset_name(symbol):
    """Readable asset name for known symbols; fall back to Yahoo Finance metadata."""
    return ASSET_NAMES.get(str(symbol).upper(), str(symbol).upper())


def price_decimals(price):
    """Use extra precision for low-priced crypto assets."""
    try:
        return 2 if abs(float(price)) >= 1 else 6
    except (TypeError, ValueError):
        return 2


def calculate_position_size(account_size, risk_fraction, entry, stop, target, is_crypto=False):
    """Calculate a conservative paper position size and its risk/reward estimates.

    Stocks are rounded down to whole shares; crypto is rounded down to six decimals.
    Notional exposure is capped at the paper account balance for both directions.
    """
    try:
        account = float(account_size)
        risk_fraction = float(risk_fraction)
        entry = float(entry)
        stop = float(stop)
        target = float(target)
    except (TypeError, ValueError):
        return {"valid": False, "reason": "Enter valid numeric values for the account, entry, stop and target."}

    if not all(np.isfinite(v) for v in (account, risk_fraction, entry, stop, target)):
        return {"valid": False, "reason": "All calculator values must be finite numbers."}
    if account <= 0 or not 0 < risk_fraction <= 1 or entry <= 0 or stop <= 0 or target <= 0:
        return {"valid": False, "reason": "Account, entry, stop and target must be above zero; risk must be between 0% and 100%."}

    # A stop below entry defines a LONG; a stop above entry defines a SHORT.
    side = "LONG" if stop < entry < target else ("SHORT" if target < entry < stop else None)
    if side is None:
        return {"valid": False, "reason": "LONG needs Stop < Entry < Target. SHORT needs Target < Entry < Stop."}

    stop_distance = abs(entry - stop)
    reward_distance = abs(target - entry)
    risk_budget = account * risk_fraction
    risk_based_qty = risk_budget / stop_distance
    buying_power_cap = account / entry
    raw_qty = min(risk_based_qty, buying_power_cap)

    if is_crypto:
        quantity = float(np.floor(raw_qty * 1_000_000) / 1_000_000)
        unit = "units"
    else:
        quantity = float(int(raw_qty))
        unit = "shares"

    if quantity <= 0:
        return {"valid": False, "reason": "The risk budget or account size is too small for one share/unit at these levels."}

    planned_risk = quantity * stop_distance
    potential_reward = quantity * reward_distance
    return {
        "valid": True,
        "side": side,
        "quantity": quantity,
        "unit": unit,
        "risk_budget": risk_budget,
        "planned_risk": planned_risk,
        "position_value": quantity * entry,
        "potential_reward": potential_reward,
        "reward_to_risk": reward_distance / stop_distance,
        "buying_power_cap": buying_power_cap,
        "risk_pct_used": (planned_risk / account) * 100,
        "stop_distance": stop_distance,
    }

def build_quick_trade_plan(signal, price, stop_gap, rr_ratio, side, digits=2):
    """Build an automatic side-specific paper plan with correctly ordered levels."""
    side = str(side).upper()
    if side not in {"LONG", "SHORT"}:
        raise ValueError("side must be LONG or SHORT")
    price = float(price)
    stop_gap = max(float(stop_gap), price * 0.0025, 0.000001)
    rr_ratio = float(rr_ratio)
    if not np.isfinite(price) or price <= 0 or not np.isfinite(rr_ratio) or rr_ratio <= 0:
        raise ValueError("price and reward-to-risk ratio must be positive finite numbers")

    if signal.get("side") == side:
        entry = float(signal["ideal_buy"])
        stop = float(signal["stop"])
        target = float(signal["ideal_sell"])
    elif side == "LONG":
        entry = price
        stop = round(max(0.000001, entry - stop_gap), digits)
        target = round(entry + stop_gap * rr_ratio, digits)
    else:
        entry = price
        stop = round(entry + stop_gap, digits)
        target = round(max(0.000001, entry - stop_gap * rr_ratio), digits)

    valid_levels = (stop < entry < target) if side == "LONG" else (target < entry < stop)
    if not valid_levels:
        # Signal-derived levels can become invalid after price precision rounding;
        # fall back to a clean current-price plan rather than disabling the side.
        entry = price
        if side == "LONG":
            stop = round(max(0.000001, entry - stop_gap), digits)
            target = round(entry + stop_gap * rr_ratio, digits)
        else:
            stop = round(entry + stop_gap, digits)
            target = round(max(0.000001, entry - stop_gap * rr_ratio), digits)

    return {"entry": float(entry), "stop": float(stop), "target": float(target), "side": side}


def scan_recommendation_candidates(scan_interval="15m", prepost=False, rr_ratio=1.8):
    """Rank a curated universe of liquid US stocks/ETFs and major crypto pairs."""
    rows = []
    for symbol in RECOMMENDATION_UNIVERSE:
        try:
            raw = get_intraday_data(symbol, scan_interval, prepost=prepost)
            if raw is None or raw.empty or len(raw) < 30:
                continue
            enriched = add_indicators(raw)
            daily = get_daily_stats(symbol)
            live_quote = get_fast_quote(symbol)
            stats = compute_price_targets_and_signal(
                enriched, live_quote, daily, scan_interval, rr_ratio
            )
            side = stats["side"]
            if side not in {"LONG", "SHORT"} or int(stats["score"]) < 3:
                continue
            current_price = float(stats["price"])
            entry_price = float(stats["ideal_buy"])
            target_price = float(stats["ideal_sell"])
            target_pct = ((target_price / max(entry_price, 0.000001)) - 1) * 100
            if side == "SHORT":
                target_pct = ((entry_price / max(target_price, 0.000001)) - 1) * 100
            day_change_pct = float(daily.get("change_pct", 0.0)) if daily else 0.0
            digits = price_decimals(current_price)
            rows.append({
                "Asset Name": display_asset_name(symbol),
                "Symbol": symbol,
                "Asset Type": "Crypto" if symbol.endswith("-USD") else "Stock / ETF",
                "Price": round(current_price, digits),
                "Today %": round(day_change_pct, 2),
                "Bias": "Bullish" if side == "LONG" else "Bearish",
                "Score": f'{stats["score"]}/5',
                "Target Price": round(target_price, digits),
                "Potential %": round(target_pct, 2),
                "Entry": round(entry_price, digits),
                "Stop": round(stats["stop"], digits),
                "RSI": round(stats["rsi"], 1),
                "_score": int(stats["score"]),
                "_reward_pct": float(target_pct),
                "_side": side
            })
        except Exception:
            continue
    rows.sort(key=lambda row: (row["_score"], row["_reward_pct"]), reverse=True)
    return rows

# ---------- Session State ----------
defaults = {
    "watchlist": ["SPY", "QQQ", "AAPL", "TSLA", "NVDA", "BTC-USD", "ETH-USD"],
    "active_ticker": "SPY",
    "paper_trades": [],
    "account_size": 25000.0,
    "daily_loss_limit": 300.0,
    "last_alert_action": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
# Add the two major crypto pairs to existing saved watchlists without removing user symbols.
for crypto_symbol in ["BTC-USD", "ETH-USD"]:
    if crypto_symbol not in st.session_state.watchlist:
        st.session_state.watchlist.append(crypto_symbol)

# ---------- Market Session Helper ----------
def get_market_session():
    now_est = datetime.now(ZoneInfo("America/New_York"))
    weekday = now_est.weekday()
    t = now_est.time()

    if weekday >= 5:
        return "🌙 Weekend / Closed", now_est
    if dtime(4, 0) <= t < dtime(9, 30):
        return "🌅 Pre-Market (Extended)", now_est
    elif dtime(9, 30) <= t < dtime(16, 0):
        return "🟢 Regular Market Open", now_est
    elif dtime(16, 0) <= t < dtime(20, 0):
        return "🌆 After-Hours (Extended)", now_est
    else:
        return "🌙 Overnight Session", now_est

# ---------- Data & Indicators ----------
@st.cache_data(ttl=5, show_spinner=False)
def get_intraday_data(ticker, interval, prepost=True):
    # Yahoo Finance supports 1m, 2m, 5m, 15m, 30m and 60m intraday bars.
    # 1m history is much more restricted than the larger intervals.
    period = "2d" if interval == "1m" else "60d"
    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        prepost=prepost,
        progress=False,
        auto_adjust=True
    )
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(set(df.columns)):
        return pd.DataFrame()
    return df.dropna(subset=["Open", "High", "Low", "Close"])

@st.cache_data(ttl=60, show_spinner=False)
def get_daily_stats(ticker):
    df_d = yf.download(ticker, period="1mo", interval="1d", progress=False, auto_adjust=True)
    if isinstance(df_d.columns, pd.MultiIndex):
        df_d.columns = df_d.columns.get_level_values(0)
    df_d = df_d.dropna()
    if len(df_d) < 5:
        return None

    prev_close = df_d["Close"].shift(1)
    tr = pd.concat([
        df_d["High"] - df_d["Low"],
        (df_d["High"] - prev_close).abs(),
        (df_d["Low"] - prev_close).abs()
    ], axis=1).max(axis=1)
    daily_atr = float(tr.rolling(14, min_periods=3).mean().iloc[-1])
    today_open = float(df_d["Open"].iloc[-1])
    prev_day_close = float(df_d["Close"].iloc[-2]) if len(df_d) >= 2 else today_open
    today_close = float(df_d["Close"].iloc[-1])
    change_pct = ((today_close - prev_day_close) / prev_day_close * 100) if prev_day_close else 0.0
    return {
        "daily_atr": daily_atr,
        "today_open": today_open,
        "today_close": today_close,
        "prev_close": prev_day_close,
        "change_pct": change_pct,
        "day_high": float(df_d["High"].iloc[-1]),
        "day_low": float(df_d["Low"].iloc[-1]),
    }

@st.cache_data(ttl=5, show_spinner=False)
def get_fast_quote(ticker):
    try:
        t = yf.Ticker(ticker)
        fi = t.fast_info
        last_px = getattr(fi, "last_price", None)
        if last_px and not np.isnan(last_px):
            return float(last_px)
    except Exception:
        pass
    return None

def add_indicators(df):
    df = df.copy()
    typical = (df["High"] + df["Low"] + df["Close"]) / 3
    vol_clean = df["Volume"].replace(0, np.nan).fillna(1)
    df["TP_Vol"] = typical * vol_clean
    df["Date"] = df.index.date
    df["Cum_Vol"] = df.groupby("Date")["Volume"].cumsum().replace(0, np.nan)
    df["Cum_TP_Vol"] = df.groupby("Date")["TP_Vol"].cumsum()
    df["VWAP"] = (df["Cum_TP_Vol"] / df["Cum_Vol"]).fillna(df["Close"])

    df["EMA9"] = df["Close"].ewm(span=9, adjust=False).mean()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["RSI"] = (100 - (100 / (1 + rs))).fillna(50.0)
    df["Vol_MA"] = df["Volume"].rolling(8).mean()

    prev_close = df["Close"].shift(1)
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - prev_close).abs(),
        (df["Low"] - prev_close).abs()
    ], axis=1).max(axis=1)
    df["ATR"] = tr.ewm(alpha=1/14, min_periods=14, adjust=False).mean().fillna(df["Close"] * 0.003)
    
    df["Signal"] = "HOLD"
    above_vwap = df["Close"] > df["VWAP"]
    below_vwap = df["Close"] < df["VWAP"]
    ema_up = df["EMA9"] > df["EMA20"]
    ema_down = df["EMA9"] < df["EMA20"]
    
    df.loc[above_vwap & ema_up & (df["RSI"] < 70), "Signal"] = "BUY"
    df.loc[below_vwap & ema_down & (df["RSI"] > 30), "Signal"] = "SELL"
    
    return df

def compute_price_targets_and_signal(df, live_price, daily_stats, interval, rr_ratio):
    """Build directional levels from ATR and return a transparent 0-5 setup score."""
    if df is None or df.empty:
        raise ValueError("No intraday bars available.")

    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else latest
    price = float(live_price) if live_price is not None and np.isfinite(live_price) else float(latest["Close"])
    if not np.isfinite(price) or price <= 0:
        raise ValueError("Latest price is invalid.")

    vwap = float(latest["VWAP"])
    ema9 = float(latest["EMA9"])
    ema20 = float(latest["EMA20"])
    rsi = float(latest["RSI"])
    atr = float(latest["ATR"])
    vol = float(latest["Volume"])
    vol_ma = float(latest["Vol_MA"]) if pd.notna(latest["Vol_MA"]) and latest["Vol_MA"] > 0 else max(vol, 1.0)
    atr = max(atr if np.isfinite(atr) else price * 0.003, price * 0.001)
    digits = price_decimals(price)

    recent = df.tail(45)
    swing_high = float(recent["High"].max())
    swing_low = float(recent["Low"].min())

    above_vwap, below_vwap = price > vwap, price < vwap
    ema_up, ema_down = ema9 > ema20, ema9 < ema20
    reclaim_up = float(prev["Close"]) <= float(prev["VWAP"]) and price > vwap
    reclaim_down = float(prev["Close"]) >= float(prev["VWAP"]) and price < vwap
    vol_ok = vol >= vol_ma * 0.85
    rsi_long_ok = 40 < rsi < 70
    rsi_short_ok = 30 < rsi < 60

    long_score = int(above_vwap) + int(ema_up) + int(reclaim_up or price > ema9) + int(vol_ok) + int(rsi_long_ok)
    short_score = int(below_vwap) + int(ema_down) + int(reclaim_down or price < ema9) + int(vol_ok) + int(rsi_short_ok)

    stop_dist = max(atr * 1.25, price * 0.0025)
    long_entry = min(price, max(vwap, min(ema9, price)))
    short_entry = max(price, min(vwap, max(ema9, price)))
    long_stop = round(max(0.000001, long_entry - stop_dist), digits)
    short_stop = round(short_entry + stop_dist, digits)
    long_target = round(long_entry + stop_dist * float(rr_ratio), digits)
    short_target = round(max(0.000001, short_entry - stop_dist * float(rr_ratio)), digits)

    # Keep legacy output keys while making their meaning direction-aware.
    if long_score >= 4 and long_score > short_score and price <= long_entry + atr * 0.35:
        action = "🚀 BUY NOW (STRONG SETUP)"
        reasons = [
            f"Long setup score is {long_score}/5 with price above VWAP",
            "EMA 9 is above EMA 20 and momentum is not overextended",
            f"Illustrative long target ${long_target:,.{digits}f}; stop ${long_stop:,.{digits}f}"
        ]
        side, score = "LONG", long_score
        ideal_buy, stop, ideal_sell = round(long_entry, digits), long_stop, long_target
    elif short_score >= 4 and short_score > long_score:
        action = "🔻 SHORT / SELL NOW"
        reasons = [
            f"Short setup score is {short_score}/5 with price below VWAP",
            "EMA 9 is below EMA 20 and downside momentum is aligned",
            f"Illustrative short target ${short_target:,.{digits}f}; stop ${short_stop:,.{digits}f}"
        ]
        side, score = "SHORT", short_score
        ideal_buy, stop, ideal_sell = round(short_entry, digits), short_stop, short_target
    elif long_score >= 3 and long_score > short_score:
        action = f"⏳ WAIT FOR PULLBACK TO ${long_entry:,.{digits}f}"
        reasons = ["Bullish conditions are developing, but entry confirmation is incomplete.",
                   f"Watch the long entry area near ${long_entry:,.{digits}f}."]
        side, score = "LONG", long_score
        ideal_buy, stop, ideal_sell = round(long_entry, digits), long_stop, long_target
    elif short_score >= 3 and short_score > long_score:
        action = f"⏳ WAIT FOR SHORT SETUP NEAR ${short_entry:,.{digits}f}"
        reasons = ["Bearish conditions are developing, but entry confirmation is incomplete.",
                   f"Watch the short entry area near ${short_entry:,.{digits}f}."]
        side, score = "SHORT", short_score
        ideal_buy, stop, ideal_sell = round(short_entry, digits), short_stop, short_target
    else:
        action = "🛡️ WAIT (NO CLEAR SETUP)"
        reasons = ["Trend, momentum, and volume are not sufficiently aligned.",
                   f"VWAP is ${vwap:,.{digits}f}; wait for a confirmed reclaim or rejection."]
        side, score = "None", max(long_score, short_score)
        ideal_buy, stop, ideal_sell = round(price, digits), round(price - stop_dist, digits), round(price + stop_dist * float(rr_ratio), digits)

    mins_per_bar = {"1m": 1, "2m": 2, "5m": 5, "15m": 15, "30m": 30, "60m": 60}.get(interval, 1)
    hourly_expected_move = atr * np.sqrt(60 / mins_per_bar) * 0.55
    bias_mult = 1.0 if (above_vwap and ema_up) else (-1.0 if (below_vwap and ema_down) else 0.0)
    hourly_target = round(price + hourly_expected_move * bias_mult, digits)

    if daily_stats:
        d_atr = max(float(daily_stats["daily_atr"]), 0.0)
        anchor = float(daily_stats["today_open"])
        daily_target = round(price + d_atr * 0.35 * bias_mult, digits)
        daily_range = (round(anchor - d_atr * 0.75, digits), round(anchor + d_atr * 0.75, digits))
    else:
        daily_target = round(price + hourly_expected_move * 2.5 * bias_mult, digits)
        daily_range = (round(swing_low, digits), round(swing_high, digits))

    return {
        "action": action, "reasons": reasons, "side": side, "score": score,
        "price": price, "vwap": vwap, "rsi": rsi,
        "ideal_buy": ideal_buy, "ideal_sell": ideal_sell, "stop": stop,
        "stop_dist": abs(ideal_buy - stop), "hourly_target": hourly_target,
        "daily_target": daily_target, "daily_range": daily_range,
        "long_score": long_score, "short_score": short_score
    }

def get_higher_tf_bias(ticker, prepost, trend_interval="15m"):
    """Return EMA trend confirmation for the user-selected timeframe."""
    try:
        df = get_intraday_data(ticker, trend_interval, prepost=prepost)
        if len(df) < 25:
            return "Not enough data"
        df = add_indicators(df)
        latest = df.iloc[-1]
        ema9 = float(latest["EMA9"])
        ema20 = float(latest["EMA20"])
        if ema9 > ema20:
            return "🟢 Bullish (Up)"
        if ema9 < ema20:
            return "🔴 Bearish (Down)"
        return "⚪ Neutral"
    except Exception:
        return "Unavailable"

# ---------- ALWAYS-REFRESHING MARKET CANDIDATES ----------
@st.cache_resource
def get_market_scan_executor():
    """One background worker keeps the candidate scan from blocking the dashboard."""
    return ThreadPoolExecutor(max_workers=1, thread_name_prefix="market-candidate-scan")


def normalize_candidate_row(raw_row):
    """Backfill fields when Streamlit session state contains rows from an older app version."""
    row = dict(raw_row) if not isinstance(raw_row, dict) else raw_row.copy()
    symbol = str(row.get("Symbol") or row.get("symbol") or "UNKNOWN").upper()
    row["Symbol"] = symbol
    row["Asset Name"] = row.get("Asset Name") or row.get("Name") or row.get("name") or display_asset_name(symbol)
    row["Asset Type"] = row.get("Asset Type") or ("Crypto" if symbol.endswith("-USD") else "Stock / ETF")
    row["Bias"] = row.get("Bias") or ("Bullish" if row.get("_side", "LONG") == "LONG" else "Bearish")
    row["_side"] = row.get("_side") or ("SHORT" if str(row["Bias"]).lower() in {"bearish", "short"} else "LONG")
    row.setdefault("Price", 0.0)
    row.setdefault("Today %", 0.0)
    row.setdefault("Score", "—")
    row.setdefault("Potential %", 0.0)
    row.setdefault("Target Price", row.get("Price", 0.0))
    row.setdefault("Entry", row.get("Price", 0.0))
    row.setdefault("Stop", row.get("Price", 0.0))
    row.setdefault("RSI", 0.0)
    return row


@st.fragment(run_every=15)
def render_top_market_candidates(compact=False):
    """Poll a single background scan; retain the last good results during refresh."""
    if compact:
        info_heading("⭐ Top Market Candidates", "Automatically refreshed technical watch ideas from a curated liquid-stock universe. A score is a checklist count, not a probability or prediction.", 3)
    else:
        info_heading("⭐ Top Market Candidates", "Automatically refreshed technical watch ideas from a curated liquid-stock universe. Target distances are rule-based scenarios, not promised returns.", 2)

    if st.button("↻ Refresh candidates", key="top_candidate_refresh", use_container_width=True):
        st.session_state["recommendation_force_refresh"] = True

    future = st.session_state.get("recommendation_future")
    requested_at = st.session_state.get("recommendation_requested_at", 0.0)
    now_ts = datetime.now().timestamp()
    force_refresh = st.session_state.pop("recommendation_force_refresh", False)

    if force_refresh:
        # Do not discard the last completed list; it remains visible while the new scan runs.
        future = None

    if future is None or (future.done() and now_ts - requested_at >= 300):
        future = get_market_scan_executor().submit(scan_recommendation_candidates, "15m", False, 1.8)
        st.session_state["recommendation_future"] = future
        st.session_state["recommendation_requested_at"] = now_ts

    if future.done():
        try:
            rows = future.result()
            st.session_state["recommendation_rows"] = rows
            st.session_state["recommendation_scan_time"] = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %I:%M:%S %p ET")
            st.session_state["recommendation_last_error"] = None
        except Exception as exc:
            st.session_state["recommendation_last_error"] = str(exc)

    # Older session-state entries may predate the Asset Name / Asset Type fields.
    # Normalize at display time so deployments and browser sessions do not crash.
    candidates = [normalize_candidate_row(row) for row in st.session_state.get("recommendation_rows", [])]
    st.session_state["recommendation_rows"] = candidates
    scan_time = st.session_state.get("recommendation_scan_time")
    if scan_time:
        st.caption(f"Updated {scan_time}")
    if not future.done():
        st.caption("⏳ Scanning in background… showing previous results until complete." if candidates else "⏳ First scan running in background…")
    if st.session_state.get("recommendation_last_error"):
        st.caption("Latest scan had a temporary data issue; retry with Refresh candidates.")
    if not candidates:
        return

    bullish = [row for row in candidates if row["_side"] == "LONG"]
    bearish = [row for row in candidates if row["_side"] == "SHORT"]
    if compact:
        for row in candidates[:8]:
            tint = "🟢" if row["_side"] == "LONG" else "🔴"
            digits = price_decimals(row["Price"])
            st.markdown(
                f'<div style="padding:8px 9px;margin:5px 0;border:1px solid #293b52;border-radius:8px;background:#111d2b">'
                f'<div style="font-weight:750;color:#f0f6ff;line-height:1.25">{tint} {row["Asset Name"]}</div>'
                f'<div style="display:flex;justify-content:space-between;gap:8px;margin-top:3px"><b style="color:#8ed8ff">{row["Symbol"]}</b><b>${row["Price"]:,.{digits}f}</b></div>'
                f'<span style="color:#9fb1c8;font-size:11px">{row["Asset Type"]} · {row["Bias"]} · {row["Today %"]:+.2f}% today · Score {row["Score"]} · Target {row["Potential %"]:+.2f}%</span></div>',
                unsafe_allow_html=True
            )
        choices = [row["Symbol"] for row in candidates]
        chosen = st.selectbox("Load candidate", choices, key="top_candidate_pick_sidebar")
        if st.button("Load selected candidate", key="top_candidate_load_sidebar", use_container_width=True):
            st.session_state.active_ticker = chosen
            st.rerun()
        return

    if bullish:
        st.markdown("#### 🟢 Bullish candidates")
        bullish_df = pd.DataFrame(bullish[:8]).drop(columns=["_score", "_reward_pct", "_side"], errors="ignore")
        for col in ["Price", "Target Price", "Entry", "Stop"]:
            bullish_df[col] = bullish_df[col].map(lambda value: f"${float(value):,.{price_decimals(value)}f}")
        bullish_df = bullish_df.rename(columns={"Price": "Current Price", "Today %": "Day Change %", "Target Price": "Target Price", "Potential %": "Target Distance %", "Entry": "Entry Area"})
        st.dataframe(bullish_df, use_container_width=True, hide_index=True)
    else:
        st.info("No bullish candidates currently meet the scanner's minimum technical score.")
    if bearish:
        with st.expander("🔻 Bearish / short candidates", expanded=False):
            bearish_df = pd.DataFrame(bearish[:6]).drop(columns=["_score", "_reward_pct", "_side"], errors="ignore")
            for col in ["Price", "Target Price", "Entry", "Stop"]:
                bearish_df[col] = bearish_df[col].map(lambda value: f"${float(value):,.{price_decimals(value)}f}")
            bearish_df = bearish_df.rename(columns={"Price": "Current Price", "Today %": "Day Change %", "Target Price": "Target Price", "Potential %": "Target Distance %", "Entry": "Entry Area"})
            st.dataframe(bearish_df, use_container_width=True, hide_index=True)
    choices = [row["Symbol"] for row in candidates]
    pick_col, add_col = st.columns([2, 1])
    with pick_col:
        chosen = st.selectbox("Choose a candidate", choices, key="top_candidate_pick_main")
    with add_col:
        st.write("")
        if st.button("＋ Add to watchlist", key="top_candidate_add_main", use_container_width=True):
            if chosen not in st.session_state.watchlist:
                st.session_state.watchlist.append(chosen)
            st.session_state.active_ticker = chosen
            st.rerun()


# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("### 🎛️ Terminal Settings")
    dash_mode = st.radio(
        "Experience Level",
        ["Beginner (Simple)", "Advanced (Pro)"],
        index=0,
        help="Beginner mode explains signals in plain language. Advanced mode exposes more technical detail."
    )

    # Stock discovery and market candidates sit at the top of the left rail.
    info_heading("🔎 Find Stocks & Crypto", "Search stocks, ETFs, or crypto by name or ticker (for example Apple, NVDA, Bitcoin, or BTC-USD). Choose a result to load it or add it to your watchlist.", 3)
    sidebar_query = st.text_input("Ticker or company", placeholder="Apple, NVDA, Bitcoin, BTC-USD…", key="sidebar_symbol_search")
    if sidebar_query.strip():
        sidebar_matches = search_stock_symbols(sidebar_query)
        if sidebar_matches:
            ASSET_NAMES.update({x["symbol"]: x["name"] for x in sidebar_matches})
            sidebar_labels = [f'{x["name"]} — {x["symbol"]} ({x["type"]})' for x in sidebar_matches]
            sidebar_choice = st.selectbox("Matching symbols", sidebar_labels, key="sidebar_symbol_match")
            sidebar_symbol = sidebar_matches[sidebar_labels.index(sidebar_choice)]["symbol"]
            sb_load, sb_add = st.columns(2)
            if sb_load.button("Load", key="sidebar_load_symbol", type="primary", use_container_width=True):
                st.session_state.active_ticker = sidebar_symbol
                st.rerun()
            if sb_add.button("＋ Watch", key="sidebar_add_symbol", use_container_width=True):
                if sidebar_symbol not in st.session_state.watchlist:
                    st.session_state.watchlist.append(sidebar_symbol)
                st.session_state.active_ticker = sidebar_symbol
                st.rerun()
        else:
            st.caption("No symbols found. Try a company name, coin name, or Yahoo symbol such as BTC-USD or ETH-USD.")

    render_top_market_candidates(compact=True)

    info_heading("⭐ Your Watchlist", "Your saved symbols. Select one to load its live chart and trading analysis.", 3)
    manual_sym = st.text_input("Add ticker manually", placeholder="e.g. META or BTC-USD", key="manual_watch_symbol").upper().strip()
    if st.button("➕ Add manual ticker", key="add_manual_symbol", use_container_width=True) and manual_sym:
        if manual_sym not in st.session_state.watchlist:
            st.session_state.watchlist.append(manual_sym)
        st.session_state.active_ticker = manual_sym
        st.rerun()

    for sym in st.session_state.watchlist:
        btn_type = "primary" if sym == st.session_state.active_ticker else "secondary"
        if st.button(f"⚡ {display_asset_name(sym)} · {sym}", key=f"btn_{sym}", type=btn_type, use_container_width=True):
            st.session_state.active_ticker = sym
            st.rerun()

    st.markdown("---")
    info_heading("📈 Chart & Risk Controls", "Set the chart display, confirmation timeframe, position sizing assumptions and account risk limits.", 3)
    chart_type = st.selectbox("Chart Style", ["Candlestick", "Line Chart"], index=0,
                              help="Candlesticks show open, high, low and close. Line charts connect closing prices.")
    timeframe_options = ["1m", "2m", "5m", "15m", "30m", "60m"]
    interval = st.selectbox("Chart Timeframe", timeframe_options, index=0,
                            format_func=lambda value: "1h (60m)" if value == "60m" else value,
                            help="Length represented by each chart candle. Shorter intervals move faster and can be noisier.")
    trend_interval = st.selectbox("Trend Confirmation Timeframe", timeframe_options, index=3,
                                  format_func=lambda value: "1h (60m)" if value == "60m" else value,
                                  help="Independent timeframe used to check the broader short-term trend.")
    include_247 = st.checkbox("Include Extended Hours (Stocks / ETFs)", value=True,
                              help="Includes pre-market and after-hours bars for supported stocks and ETFs. Crypto trades 24/7 and does not use this setting.")
    st.session_state.account_size = st.number_input("Account Size ($)", min_value=50.0, max_value=1000000.0,
                                                     value=st.session_state.account_size, step=500.0,
                                                     help="Paper account value used for position sizing. No real funds are connected.")
    risk_pct = st.slider("Risk Per Trade (%)", 0.1, 5.0, 0.5, 0.1,
                         help="Maximum planned account percentage at risk if the stop is reached.") / 100
    rr_ratio = st.slider("Reward-to-Risk Target", 1.0, 5.0, 1.8, 0.1,
                         help="Target reward divided by the amount planned to risk. For example, 2.0 means 2 dollars targeted for each 1 dollar risked.")
    st.session_state.daily_loss_limit = st.number_input("Max Daily Loss ($)", min_value=10.0,
                                                         value=st.session_state.daily_loss_limit, step=50.0,
                                                         help="Paper-trading loss threshold used to pause new quick executions.")
    refresh_sec = st.slider("Dashboard Refresh (sec)", 8, 60, 8,
                            help="How often the live dashboard refreshes quotes and chart data.")
    auto = st.checkbox("Enable Live Auto-Refresh", value=True,
                       help="Automatically refresh the main dashboard. Candidate scans have their own refresh control.")
    st.markdown("---")
    st.caption("Yahoo Finance quotes can be delayed, incomplete or rate-limited.")

# ---------- LIVE DASHBOARD FRAGMENT ----------
run_interval = refresh_sec if auto else None

@st.fragment(run_every=run_interval)
def render_dashboard():
    ticker = st.session_state.active_ticker
    session_label, now_est = get_market_session()

    try:
        df_raw = get_intraday_data(ticker, interval, prepost=include_247)
        if df_raw.empty:
            st.error("Could not load market data. Check the ticker; crypto symbols usually use the -USD format (for example BTC-USD).")
            return

        df = add_indicators(df_raw)
        fast_px = get_fast_quote(ticker)
        daily_stats = get_daily_stats(ticker)
        sig = compute_price_targets_and_signal(df, fast_px, daily_stats, interval, rr_ratio)

        price = sig["price"]
        
        if "BUY NOW" in sig["action"] or "SHORT" in sig["action"]:
            if st.session_state.last_alert_action != sig["action"]:
                st.toast(f"🚨 ALERT: {sig['action']} on {ticker} @ ${price:,.{price_decimals(price)}f}!", icon="⚡")
                st.session_state.last_alert_action = sig["action"]

        last_bar_time = df.index[-1]
        try:
            age_sec = int((datetime.now(last_bar_time.tzinfo) - last_bar_time).total_seconds())
            age_str = f"{age_sec // 60}m {age_sec % 60}s ago" if age_sec >= 0 else "Live"
        except Exception:
            age_str = "Latest available"

        today = datetime.now(ZoneInfo("America/New_York")).date().isoformat()
        today_realized = sum(
            float(t["pnl"]) for t in st.session_state.paper_trades
            if t.get("pnl") is not None and t.get("closed_at", t.get("time", "")).startswith(today)
        )
        today_unrealized = 0.0
        for trade in st.session_state.paper_trades:
            if trade.get("status") == "OPEN" and trade.get("time", "").startswith(today):
                mark = price if trade.get("ticker") == ticker else (get_fast_quote(trade["ticker"]) or trade["entry"])
                qty = float(trade.get("shares", 0))
                if trade.get("side") == "LONG":
                    today_unrealized += (mark - trade["entry"]) * qty
                else:
                    today_unrealized += (trade["entry"] - mark) * qty
        today_pnl = today_realized + today_unrealized
        limit_hit = today_pnl <= -st.session_state.daily_loss_limit

        ticker_digits = price_decimals(price)
        asset_name = display_asset_name(ticker)
        st.markdown(f"## ⚡ {asset_name} ({ticker}) — ${price:,.{ticker_digits}f}")
        st.caption(f"Chart: {interval}  •  Trend confirmation: {'1h' if trend_interval == '60m' else trend_interval}")
        st.caption(
            f"Session: **{session_label}**  •  EST Time: {now_est.strftime('%I:%M:%S %p')}  •  "
            f"Last Candle: {age_str}  •  Refresh: {refresh_sec}s"
        )

        css = "buy" if "BUY" in sig["action"] else ("short" if "SHORT" in sig["action"] or "SELL" in sig["action"] else "watch")
        st.markdown(f'<div class="action-banner {css}">{sig["action"]}</div>', unsafe_allow_html=True)

        if limit_hit:
            st.error(f"⚠️ Daily loss limit reached (${st.session_state.daily_loss_limit:.0f}). Stop trading for today.")

        # Metrics Row with Info Tooltips
        c1, c2, c3 = st.columns(3)
        c1.metric("Current Price", f"${price:,.{ticker_digits}f}", help="The latest available quote. Yahoo Finance data may be delayed.")
        c2.metric("VWAP (Fair Value)", f"${sig['vwap']:,.{ticker_digits}f}", help="Volume-Weighted Average Price; a session reference, not a prediction.")
        c3.metric("RSI (Momentum)", f"{sig['rsi']:.0f}", help="Momentum gauge from 0 to 100. It can remain high or low during strong trends.")
        c4, c5 = st.columns(2)
        c4.metric("Setup Score", f"{sig['score']}/5", help="How many of the five technical checks are met. This is not a probability of success.")
        c5.metric(
            f"{'1h' if trend_interval == '60m' else trend_interval} Trend",
            get_higher_tf_bias(ticker, include_247, trend_interval),
            help=f"EMA 9 versus EMA 20 trend confirmation on the selected {trend_interval} timeframe."
        )

        if dash_mode == "Advanced (Pro)":
            info_heading("🔬 Advanced Pro Telemetry", "Additional technical readings: ATR measures volatility, volume versus average compares activity, and EMA spread shows trend separation.", 5)
            ac1, ac2, ac3, ac4 = st.columns(4)
            ac1.metric("ATR (Volatility)", f"${df.iloc[-1]['ATR']:,.{ticker_digits}f}", help="Average True Range measures how much the stock typically moves per candle.")
            ac2.metric("Volume vs MA", f"{df.iloc[-1]['Volume'] / max(df.iloc[-1]['Vol_MA'], 1):.2f}x", help="Current volume compared to its 8-period average. Higher means stronger interest.")
            ac3.metric("EMA 9 / EMA 20 Spread", f"${df.iloc[-1]['EMA9'] - df.iloc[-1]['EMA20']:+,.{ticker_digits}f}", help="Distance between short-term trend averages.")
            ac4.metric("Session High / Low", f"${df.tail(45)['High'].max():,.{ticker_digits}f} / ${df.tail(45)['Low'].min():,.{ticker_digits}f}", help="Highest and lowest prices reached in the current trading window.")

        info_heading("🎯 Live Price Targets & Trade Zones", "Illustrative entry, stop and target levels calculated from the selected chart interval and reward-to-risk setting.", 4)
        t1, t2, t3, t4 = st.columns(4)
        buy_delta = ((sig["ideal_buy"] - price) / price) * 100
        sell_delta = ((sig["ideal_sell"] - price) / price) * 100
        hr_delta = ((sig["hourly_target"] - price) / price) * 100
        day_delta = ((sig["daily_target"] - price) / price) * 100

        t1.metric("Ideal Buy Price", f"${sig['ideal_buy']:,.{ticker_digits}f}", f"{buy_delta:+.2f}% from now", help="The recommended entry price based on pullback support so you don't chase peaks.")
        t2.metric("Ideal Sell Price", f"${sig['ideal_sell']:,.{ticker_digits}f}", f"{sell_delta:+.2f}% from now", help="Your target exit price for taking profit based on your Reward-to-Risk ratio.")
        t3.metric("Hourly Target (1H)", f"${sig['hourly_target']:,.{ticker_digits}f}", f"{hr_delta:+.2f}% projected", help="Expected price movement over the next hour based on volatility.")
        t4.metric(
            "Daily Target (EOD)",
            f"${sig['daily_target']:,.{ticker_digits}f}",
            f"{day_delta:+.2f}% (Range: ${sig['daily_range'][0]}–${sig['daily_range'][1]})",
            help="Projected end-of-day price boundary based on 14-day average volatility."
        )

        info_heading("💡 Why this setup?", "A short explanation of which technical checks are supporting or weakening the current signal.", 4)
        for r in sig["reasons"]:
            st.markdown(f"- {r}")

        # Beginner Glossary / Dark-Themed Expander
        with st.expander("👶 Beginner's Guide: What do these terms mean?"):
            st.markdown("""
- **VWAP (Fair Value Line)**: The average price people paid today, weighted by volume. If price is above VWAP, buyers are winning. If below, sellers are winning.
- **RSI (Momentum Gauge)**: Tells you if a stock has moved too fast. Above 70 means it might be due for a cooldown; below 30 means it might bounce back up.
- **EMA 9 & EMA 20 (Trend Lines)**: Short-term averages. When the faster line (9) is *above* the slower line (20), the short-term trend is pointing up.
- **Stop Loss**: Your planned exit if price moves against the trade.
- **Take Profit / Target**: The price where the simulated trade aims to close for a gain.
            """)

        # Full-width, automatic Quick Trade Execution. Build a separate calculator
        # for each side so the SHORT button never inherits the LONG quantity/levels.
        st.markdown("---")
        info_heading(
            "⚡ Quick Trade Execution",
            "Automatically calculates entry, stop, target, position size and estimated risk from the latest quote and your account/risk settings. Both buttons are available for paper practice when their own calculator is valid; they do not send broker orders.",
            3
        )
        is_crypto = ticker.endswith("-USD")
        auto_digits = price_decimals(price)
        stop_gap = max(float(sig["stop_dist"]), float(price) * 0.0025, 0.000001)
        long_ready = sig["long_score"] >= 3 and sig["long_score"] > sig["short_score"]
        short_ready = sig["short_score"] >= 3 and sig["short_score"] > sig["long_score"]

        long_plan = build_quick_trade_plan(sig, price, stop_gap, rr_ratio, "LONG", auto_digits)
        short_plan = build_quick_trade_plan(sig, price, stop_gap, rr_ratio, "SHORT", auto_digits)
        long_calc = calculate_position_size(
            st.session_state.account_size, risk_pct,
            long_plan["entry"], long_plan["stop"], long_plan["target"],
            is_crypto=is_crypto,
        )
        short_calc = calculate_position_size(
            st.session_state.account_size, risk_pct,
            short_plan["entry"], short_plan["stop"], short_plan["target"],
            is_crypto=is_crypto,
        )

        # Display the stronger technical direction at the top, while keeping both
        # side-specific paper calculators independent and visible below.
        auto_side = "LONG" if sig["long_score"] >= sig["short_score"] else "SHORT"
        auto_plan = long_plan if auto_side == "LONG" else short_plan
        auto_calc = long_calc if auto_side == "LONG" else short_calc
        price_fmt = lambda value: f"${float(value):,.{auto_digits}f}"
        st.caption(
            f"Automatic {auto_side} reference plan for **{display_asset_name(ticker)} ({ticker})** · "
            "Both BUY and SHORT paper plans calculate independently and update with the dashboard."
        )
        level1, level2, level3 = st.columns(3)
        level1.metric("Planned Entry", price_fmt(auto_plan["entry"]), help="Automatically selected entry price for the stronger current technical side.")
        level2.metric("Stop Loss", price_fmt(auto_plan["stop"]), help="Protective exit level used to calculate planned dollar risk.")
        level3.metric("Take Profit", price_fmt(auto_plan["target"]), help="Target level used to calculate potential simulated reward.")

        if auto_calc.get("valid"):
            auto_qty_text = f"{auto_calc['quantity']:,.6f}" if is_crypto else f"{int(auto_calc['quantity']):,}"
            result1, result2, result3, result4 = st.columns(4)
            result1.metric("Position Size", f"{auto_qty_text} {auto_calc['unit']}", help="Automatic quantity. Stocks use whole shares; crypto supports fractional units.")
            result2.metric("Position Value", f"${auto_calc['position_value']:,.2f}", help="Estimated notional value of the reference position.")
            result3.metric("Estimated Risk", f"-${auto_calc['planned_risk']:,.2f}", help="Estimated loss if the stop is reached, before fees or slippage.")
            result4.metric("Potential Profit", f"+${auto_calc['potential_reward']:,.2f}", help="Estimated gain if the target is reached, before fees or slippage.")
            st.caption(
                f"Risk budget: **${auto_calc['risk_budget']:,.2f}** · "
                f"Reward-to-risk: **{auto_calc['reward_to_risk']:.2f}:1** · "
                f"Account risk used: **{auto_calc['risk_pct_used']:.2f}%**"
            )
        else:
            st.warning(auto_calc.get("reason", "The automatic position calculator could not create a valid reference plan."))

        already_open = any(
            t.get("ticker") == ticker and t.get("status") == "OPEN"
            for t in st.session_state.paper_trades
        )
        buy_col, short_col = st.columns(2)
        buy_qty_text = (f"{long_calc['quantity']:,.6f}" if is_crypto else f"{int(long_calc['quantity']):,}") if long_calc.get("valid") else "—"
        short_qty_text = (f"{short_calc['quantity']:,.6f}" if is_crypto else f"{int(short_calc['quantity']):,}") if short_calc.get("valid") else "—"
        buy_col.caption(
            f"LONG · Entry {price_fmt(long_plan['entry'])} · Stop {price_fmt(long_plan['stop'])} · "
            f"Target {price_fmt(long_plan['target'])} · Risk "
            f"{('$' + format(long_calc['planned_risk'], ',.2f')) if long_calc.get('valid') else '—'}"
        )
        short_col.caption(
            f"SHORT · Entry {price_fmt(short_plan['entry'])} · Stop {price_fmt(short_plan['stop'])} · "
            f"Target {price_fmt(short_plan['target'])} · Risk "
            f"{('$' + format(short_calc['planned_risk'], ',.2f')) if short_calc.get('valid') else '—'}"
        )
        buy_disabled = already_open or limit_hit or not long_calc.get("valid", False)
        short_disabled = already_open or limit_hit or not short_calc.get("valid", False)
        if already_open:
            st.info(f"You already have an open paper position on {ticker}. The buttons stay visible, but close that position before opening another on the same asset.")
        if buy_col.button(
            f"🚀 Paper BUY · {buy_qty_text} {long_calc.get('unit', 'shares')}",
            key=f"quick_auto_buy_{ticker}",
            type="primary",
            use_container_width=True,
            disabled=buy_disabled,
            help="Opens the automatically sized simulated LONG position. The bullish setup score is shown separately; this is paper practice only.",
        ):
            st.session_state.paper_trades.append({
                "id": str(uuid.uuid4())[:8],
                "time": datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M"),
                "ticker": ticker,
                "side": "LONG",
                "entry": float(long_plan["entry"]),
                "stop": float(long_plan["stop"]),
                "target": float(long_plan["target"]),
                "shares": float(long_calc["quantity"]),
                "status": "OPEN",
                "exit": None,
                "pnl": None,
                "notes": f"Automatic Quick Execution LONG · risk budget ${long_calc['risk_budget']:.2f}",
            })
            st.rerun()

        if short_col.button(
            f"🔻 Paper SHORT · {short_qty_text} {short_calc.get('unit', 'shares')}",
            key=f"quick_auto_short_{ticker}",
            type="secondary",
            use_container_width=True,
            disabled=short_disabled,
            help="Opens the automatically sized simulated SHORT position. It has a stop above entry and target below entry. Paper practice only.",
        ):
            st.session_state.paper_trades.append({
                "id": str(uuid.uuid4())[:8],
                "time": datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M"),
                "ticker": ticker,
                "side": "SHORT",
                "entry": float(short_plan["entry"]),
                "stop": float(short_plan["stop"]),
                "target": float(short_plan["target"]),
                "shares": float(short_calc["quantity"]),
                "status": "OPEN",
                "exit": None,
                "pnl": None,
                "notes": f"Automatic Quick Execution SHORT · risk budget ${short_calc['risk_budget']:.2f}",
            })
            st.rerun()

        if limit_hit:
            st.error("Quick execution is paused because your daily loss limit has been reached.")
        elif not long_calc.get("valid", False) and not short_calc.get("valid", False):
            st.caption("Neither paper side can be sized safely with the current account balance, risk setting and stop distances.")
        else:
            current_bias = "bullish" if long_ready else ("bearish" if short_ready else "not confirmed")
            st.caption(
                f"Technical setup: **{current_bias}** (Long {sig['long_score']}/5 · Short {sig['short_score']}/5). "
                "Paper BUY and SHORT remain available for simulation when their individual calculators are valid; "
                "use the setup score as context, not as a guarantee."
            )

        # ---------- DYNAMIC CHART WITH ZOOM / TOOLBAR & MARKERS ----------
        info_heading("📊 Live Price Chart", "Candles show open, high, low and close. VWAP is a volume-weighted session reference; EMA lines smooth price trends; volume bars show trading activity.", 4)
        plot_df = df.tail(90)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.78, 0.22], vertical_spacing=0.02)

        if chart_type == "Candlestick":
            fig.add_trace(go.Candlestick(
                x=plot_df.index, open=plot_df["Open"], high=plot_df["High"], low=plot_df["Low"], close=plot_df["Close"],
                name="Price",
                increasing_line_color="#10b981", decreasing_line_color="#ef4444",
                increasing_fillcolor="#10b981", decreasing_fillcolor="#ef4444"
            ), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(
                x=plot_df.index, y=plot_df["Close"],
                name="Close Price",
                line=dict(color="#3b82f6", width=2.5)
            ), row=1, col=1)

        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["VWAP"], name="VWAP", line=dict(color="#fbbf24", width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["EMA9"], name="EMA 9", line=dict(color="#f97316", width=1.3)), row=1, col=1)
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["EMA20"], name="EMA 20", line=dict(color="#a855f7", width=1.3)), row=1, col=1)

        buy_signals = plot_df[plot_df["Signal"] == "BUY"]
        sell_signals = plot_df[plot_df["Signal"] == "SELL"]

        if not buy_signals.empty:
            fig.add_trace(go.Scatter(
                x=buy_signals.index, y=buy_signals["Low"] * 0.998,
                mode="markers",
                marker=dict(symbol="triangle-up", size=13, color="#10b981", line=dict(width=1, color="white")),
                name="Buy Marker"
            ), row=1, col=1)

        if not sell_signals.empty:
            fig.add_trace(go.Scatter(
                x=sell_signals.index, y=sell_signals["High"] * 1.002,
                mode="markers",
                marker=dict(symbol="triangle-down", size=13, color="#ef4444", line=dict(width=1, color="white")),
                name="Sell Marker"
            ), row=1, col=1)

        fig.add_hline(y=sig["ideal_buy"], line_dash="dot", line_color="#10b981", annotation_text=f"Ideal Buy ${sig['ideal_buy']:,.{ticker_digits}f}", row=1, col=1)
        fig.add_hline(y=sig["ideal_sell"], line_dash="dot", line_color="#ef4444", annotation_text=f"Ideal Sell ${sig['ideal_sell']:,.{ticker_digits}f}", row=1, col=1)
        fig.add_hline(y=sig["hourly_target"], line_dash="dash", line_color="#06b6d4", annotation_text=f"1H Target ${sig['hourly_target']:,.{ticker_digits}f}", row=1, col=1)

        bar_colors = ["#10b981" if c >= o else "#ef4444" for c, o in zip(plot_df["Close"], plot_df["Open"])]
        fig.add_trace(go.Bar(x=plot_df.index, y=plot_df["Volume"], name="Volume", marker_color=bar_colors, opacity=0.6), row=2, col=1)

        fig.update_layout(
            height=560,
            autosize=True,
            paper_bgcolor="#121824",
            plot_bgcolor="#121824",
            font=dict(color="#f8fafc"),
            margin=dict(l=0, r=10, t=10, b=0),
            xaxis_rangeslider_visible=False,
            showlegend=True,
            legend=dict(orientation="h", y=1.02, x=0, bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(gridcolor="#1e293b", type="category", nticks=10),
            yaxis=dict(gridcolor="#1e293b", side="right"),
            yaxis2=dict(gridcolor="#1e293b", side="right"),
        )
        st.plotly_chart(
            fig, 
            use_container_width=True, 
            config={
                "displayModeBar": True,
                "scrollZoom": True,
                "displaylogo": False,
                "modeBarButtonsToRemove": ["lasso2d", "select2d"]
            }
        )

        # ---------- PAPER TRADING WORKSPACE ----------
        st.markdown("---")
        info_heading("🧪 Paper Trading Desk", "A simulated portfolio for practicing entries, exits and risk management. No broker orders or real money are involved.", 3)

        # Normalize older session records so one incomplete trade cannot break this section.
        paper_records = st.session_state.get("paper_trades", [])
        if not isinstance(paper_records, list):
            paper_records = []
        normalized_records = []
        for record in paper_records:
            if not isinstance(record, dict):
                continue
            trade = dict(record)
            trade.setdefault("id", str(uuid.uuid4())[:8])
            trade.setdefault("ticker", "UNKNOWN")
            trade.setdefault("side", "LONG")
            trade.setdefault("entry", 0.0)
            trade.setdefault("stop", 0.0)
            trade.setdefault("target", 0.0)
            trade.setdefault("shares", 0.0)
            trade.setdefault("status", "OPEN")
            trade.setdefault("exit", None)
            trade.setdefault("pnl", None)
            trade.setdefault("notes", "")
            trade["ticker"] = str(trade["ticker"]).upper()
            trade["side"] = "SHORT" if str(trade["side"]).upper() == "SHORT" else "LONG"
            trade["status"] = "CLOSED" if str(trade["status"]).upper() == "CLOSED" else "OPEN"
            normalized_records.append(trade)
        st.session_state.paper_trades = normalized_records

        open_trades = [t for t in normalized_records if t["status"] == "OPEN"]
        closed_trades = [t for t in normalized_records if t["status"] == "CLOSED"]
        realized_pnl = sum(float(t.get("pnl") or 0) for t in closed_trades)
        unrealized_pnl = 0.0
        marked_positions = []
        for trade in open_trades:
            try:
                mark = price if trade["ticker"] == ticker else (get_fast_quote(trade["ticker"]) or float(trade["entry"]))
                qty = float(trade["shares"])
                entry = float(trade["entry"])
                pnl = (mark - entry) * qty if trade["side"] == "LONG" else (entry - mark) * qty
                unrealized_pnl += pnl
                marked_positions.append((trade, float(mark), float(pnl)))
            except (TypeError, ValueError, KeyError):
                marked_positions.append((trade, float(trade.get("entry") or 0), 0.0))
        portfolio_equity = float(st.session_state.account_size) + realized_pnl + unrealized_pnl
        total_return = ((portfolio_equity / float(st.session_state.account_size)) - 1) * 100 if st.session_state.account_size else 0.0

        p1, p2, p3, p4, p5 = st.columns(5)
        p1.metric("Starting Balance", f"${st.session_state.account_size:,.2f}")
        p2.metric("Portfolio Equity", f"${portfolio_equity:,.2f}", f"{total_return:+.2f}%")
        p3.metric("Realized P&L", f"${realized_pnl:+,.2f}")
        p4.metric("Open P&L", f"${unrealized_pnl:+,.2f}")
        p5.metric("Open Positions", str(len(open_trades)))
        st.caption("Portfolio equity = starting balance + closed-trade P&L + estimated open-trade P&L. Quotes may be delayed or unavailable.")

        with st.expander("➕ Add a Paper Trade", expanded=not bool(open_trades and closed_trades)):
            st.caption("Choose LONG to practice buying first, or SHORT to practice selling first. Stop and target defaults adjust to the selected side.")
            mc1, mc2, mc3, mc4 = st.columns([1.2, 0.8, 1, 1])
            manual_ticker = mc1.text_input("Ticker / Crypto Pair", value=ticker, key="paper_manual_ticker").strip().upper()
            manual_side = mc2.selectbox("Position Side", ["LONG", "SHORT"], key="paper_manual_side")
            manual_entry = mc3.number_input("Entry Price", min_value=0.000001, value=float(price), step=0.01 if not ticker.endswith("-USD") else 0.000001, format="%.6f" if ticker.endswith("-USD") else "%.2f", key="paper_manual_entry")
            manual_qty = mc4.number_input("Shares / Units", min_value=0.000001, value=1.0, step=0.01, format="%.6f", key="paper_manual_qty")
            manual_crypto = manual_ticker.endswith("-USD")
            manual_digits = 6 if manual_crypto else 2
            default_gap = max(float(manual_entry) * 0.01, 0.000001 if manual_crypto else 0.01)
            if manual_side == "LONG":
                default_stop, default_target = max(0.000001, manual_entry - default_gap), manual_entry + default_gap * 2
            else:
                default_stop, default_target = manual_entry + default_gap, max(0.000001, manual_entry - default_gap * 2)
            mc5, mc6, mc7 = st.columns([1, 1, 2])
            manual_stop = mc5.number_input("Stop Loss", min_value=0.000001, value=float(default_stop), step=0.01 if not manual_crypto else 0.000001, format=f"%.{manual_digits}f", key=f"paper_stop_{manual_side}")
            manual_target = mc6.number_input("Take Profit", min_value=0.000001, value=float(default_target), step=0.01 if not manual_crypto else 0.000001, format=f"%.{manual_digits}f", key=f"paper_target_{manual_side}")
            manual_notes = mc7.text_input("Trade Notes", placeholder="Setup, reason for entry, or lesson learned", key="paper_manual_notes")
            valid_manual = bool(manual_ticker) and manual_entry > 0 and manual_qty > 0 and (
                (manual_side == "LONG" and manual_stop < manual_entry < manual_target) or
                (manual_side == "SHORT" and manual_target < manual_entry < manual_stop)
            )
            if st.button("Save Paper Trade", type="primary", disabled=not valid_manual, key="save_manual_paper_trade"):
                if any(t["ticker"] == manual_ticker and t["status"] == "OPEN" for t in normalized_records):
                    st.warning(f"There is already an open paper position for {manual_ticker}. Close it before opening another.")
                else:
                    normalized_records.append({
                        "id": str(uuid.uuid4())[:8],
                        "time": datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M"),
                        "ticker": manual_ticker, "side": manual_side,
                        "entry": float(manual_entry), "stop": float(manual_stop),
                        "target": float(manual_target), "shares": float(manual_qty),
                        "status": "OPEN", "exit": None, "pnl": None, "notes": manual_notes
                    })
                    st.session_state.paper_trades = normalized_records
                    st.success(f"{manual_side} paper position saved for {manual_ticker}.")
                    st.rerun()
            if not valid_manual:
                st.warning("Check your levels: LONG requires Stop < Entry < Target. SHORT requires Target < Entry < Stop.")

        if open_trades:
            info_heading("📂 Open Paper Positions", "Live/last-available mark, unrealized P&L and your planned stop/target. Enter an exit price to close and realize the simulated result.", 4)
            for trade, live_px, unrealized in marked_positions:
                trade_ticker = trade["ticker"]
                digits = price_decimals(live_px)
                unit = "units" if trade_ticker.endswith("-USD") else "shares"
                stop_hit = live_px <= float(trade["stop"]) if trade["side"] == "LONG" else live_px >= float(trade["stop"])
                target_hit = live_px >= float(trade["target"]) if trade["side"] == "LONG" else live_px <= float(trade["target"])
                with st.container(border=True):
                    h1, h2, h3, h4 = st.columns([1.3, 1, 1, 1])
                    h1.markdown(f"**{display_asset_name(trade_ticker)}**  \n`{trade_ticker}` · {trade['side']} · {float(trade['shares']):,.6f} {unit}")
                    h2.metric("Entry / Mark", f"${float(trade['entry']):,.{digits}f}", f"Mark ${live_px:,.{digits}f}")
                    h3.metric("Stop / Target", f"${float(trade['stop']):,.{digits}f}", f"Target ${float(trade['target']):,.{digits}f}")
                    h4.metric("Unrealized P&L", f"${unrealized:+,.2f}", help="Estimated open profit/loss before closing the simulated trade.")
                    if stop_hit:
                        st.warning("The latest available price has crossed your stop level. Review the quote and close the simulation if appropriate.")
                    elif target_hit:
                        st.success("The latest available price has reached your target level. Review the quote and close the simulation if appropriate.")
                    x1, x2, x3 = st.columns([1.2, 1, 1])
                    exit_key = f"paper_exit_{trade['id']}"
                    exit_price = x1.number_input("Exit Price", min_value=0.000001, value=float(live_px if live_px > 0 else trade["entry"]), step=0.01 if not trade_ticker.endswith("-USD") else 0.000001, format=f"%.{digits}f", key=exit_key)
                    x2.caption(f"Opened: {trade.get('time', '—')}  \nNotes: {trade.get('notes') or '—'}")
                    if x3.button("Close Position", key=f"close_paper_{trade['id']}", use_container_width=True):
                        if exit_price <= 0 or not np.isfinite(exit_price):
                            st.error("Enter a valid exit price above zero.")
                        else:
                            pnl = (exit_price - float(trade["entry"])) * float(trade["shares"]) if trade["side"] == "LONG" else (float(trade["entry"]) - exit_price) * float(trade["shares"])
                            trade["exit"] = float(exit_price)
                            trade["pnl"] = round(pnl, 2)
                            trade["closed_at"] = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M")
                            trade["status"] = "CLOSED"
                            st.session_state.paper_trades = normalized_records
                            st.rerun()

        if closed_trades:
            info_heading("📊 Closed Trades & Performance", "Review realized simulated results. Win rate counts profitable closed trades divided by all closed trades, including break-even trades.", 4)
            closed_sorted = sorted(closed_trades, key=lambda t: str(t.get("closed_at") or t.get("time") or ""))
            cdf = pd.DataFrame(closed_sorted)
            pnl_values = [float(t.get("pnl") or 0) for t in closed_sorted]
            total_closed = len(closed_sorted)
            wins = [v for v in pnl_values if v > 0]
            losses = [v for v in pnl_values if v < 0]
            win_rate = (len(wins) / total_closed) * 100 if total_closed else 0
            avg_win = sum(wins) / len(wins) if wins else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            a1, a2, a3, a4 = st.columns(4)
            a1.metric("Net Realized P&L", f"${sum(pnl_values):+,.2f}")
            a2.metric("Win Rate", f"{win_rate:.1f}%", f"{len(wins)} wins · {len(losses)} losses")
            a3.metric("Average Winner", f"${avg_win:+,.2f}")
            a4.metric("Average Loser", f"${avg_loss:+,.2f}")
            cdf["pnl"] = pd.to_numeric(cdf["pnl"], errors="coerce").fillna(0)
            cdf["cumulative_pnl"] = cdf["pnl"].cumsum()
            eq = px.line(cdf, x="closed_at" if "closed_at" in cdf else "time", y="cumulative_pnl", title="Cumulative Realized P&L", markers=True)
            eq.update_layout(paper_bgcolor="#121824", plot_bgcolor="#121824", font=dict(color="#f8fafc"), height=300, margin=dict(l=10, r=10, t=45, b=10), xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b", title="P&L ($)"))
            eq.update_traces(line_color="#10b981" if sum(pnl_values) >= 0 else "#ef4444", line_width=3)
            st.plotly_chart(eq, use_container_width=True)
            display_cols = [c for c in ["time", "closed_at", "ticker", "side", "entry", "exit", "stop", "target", "shares", "pnl", "notes"] if c in cdf.columns]
            st.dataframe(cdf[display_cols], use_container_width=True, hide_index=True)
            csv_buffer = io.StringIO()
            cdf.to_csv(csv_buffer, index=False)
            st.download_button("📥 Export Paper Journal (CSV)", csv_buffer.getvalue(), file_name=f"paper_trading_journal_{date.today()}.csv", mime="text/csv", key="export_paper_journal")

        if not normalized_records:
            st.info("Your paper-trading desk is ready. Add a simulated trade above to start tracking positions and performance.")
        elif not open_trades and not closed_trades:
            st.info("No active or closed paper positions yet.")

        if normalized_records:
            with st.expander("⚙️ Paper Journal Controls"):
                st.caption("Clearing removes all simulated positions and history from this browser session.")
                if st.button("Clear Paper Trading History", key="request_clear_paper_history"):
                    st.session_state.confirm_clear_paper = True
                if st.session_state.get("confirm_clear_paper", False):
                    st.warning("Are you sure? This cannot be undone.")
                    cc1, cc2 = st.columns(2)
                    if cc1.button("Yes, clear all paper trades", type="primary", key="confirm_clear_paper_history"):
                        st.session_state.paper_trades = []
                        st.session_state.confirm_clear_paper = False
                        st.rerun()
                    if cc2.button("Cancel", key="cancel_clear_paper_history"):
                        st.session_state.confirm_clear_paper = False
                        st.rerun()

    except Exception as e:
        st.error(f"Something went wrong: {e}")

st.markdown("""
<div class="terminal-hero">
  <div class="terminal-kicker">Market intelligence · live monitoring · simulated execution</div>
  <h1>⚡ PRO DAY TRADE TERMINAL</h1>
  <p>A focused trading workspace with market candidates, multi-timeframe confirmation, risk planning and a built-in paper-trading journal.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
render_dashboard()

st.markdown("---")
st.warning("""
**⚠️ Educational Disclaimer**  
This tool uses Yahoo Finance data, which may be delayed, incomplete, or unavailable. Signals and price targets are rule-based estimates, not predictions or investment advice.  
Paper trades are simulations only; no broker orders are placed. Verify quotes and levels independently before making any real trading decision.
""")
