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
    .stApp { background: linear-gradient(135deg, #07090e 0%, #0b0e14 100%); color: #e2e8f0; }
    /* Keep the full terminal readable and prevent widgets from being clipped. */
    .block-container { max-width: 1900px; padding-top: 1.15rem; padding-bottom: 2rem; padding-left: clamp(1rem, 2vw, 2.5rem); padding-right: clamp(1rem, 2vw, 2.5rem); }
    div[data-testid="stPlotlyChart"], div[data-testid="stDataFrame"] { width: 100%; max-width: 100%; }
    div[data-testid="stHorizontalBlock"] { gap: 0.8rem; }
    .stMarkdown, .stCaption { overflow-wrap: anywhere; }
    @media (max-width: 900px) {
        .block-container { padding-left: 0.8rem; padding-right: 0.8rem; }
        .action-banner { font-size: 1.25rem !important; }
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0f141f;
        border-right: 1px solid #1e293b;
    }
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] .stMarkdown {
        color: #f8fafc !important;
        font-weight: 500;
    }
    section[data-testid="stSidebar"] .stButton button {
        background-color: #1a2234 !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: #2563eb !important;
        border-color: #60a5fa !important;
        color: #ffffff !important;
        box-shadow: 0 0 12px rgba(37, 99, 235, 0.4);
    }
    
    h1, h2, h3, h4 { color: #f8fafc !important; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    
    /* Fix Expander & Background Flash Contrast */
    .streamlit-expanderHeader, div[data-testid="stExpander"] {
        background-color: #121824 !important;
        color: #f8fafc !important;
        border: 1px solid #1e293b !important;
        border-radius: 8px;
    }
    div[data-testid="stExpander"] div[role="region"] {
        background-color: #0b0e14 !important;
        color: #e2e8f0 !important;
    }

    /* Modern Action Banners */
    .action-banner {
        font-size: 1.8rem;
        font-weight: 800;
        text-align: center;
        padding: 14px;
        border-radius: 12px;
        margin: 10px 0 16px 0;
        letter-spacing: 0.5px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.5);
    }
    .buy   { background: linear-gradient(135deg, #059669, #047857); color: white; border: 1px #10b981 solid; }
    .short { background: linear-gradient(135deg, #dc2626, #b91c1c); color: white; border: 1px #f87171 solid; }
    .watch { background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white; border: 1px #60a5fa solid; }
    
    /* Glassmorphism Metric Cards */
    div[data-testid="stMetric"] {
        background: rgba(18, 24, 36, 0.85);
        backdrop-filter: blur(12px);
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 14px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetric"] label { color: #94a3b8 !important; font-size: 0.9rem !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 1.4rem !important;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Yahoo Finance symbol search / recommendations ----------
@st.cache_data(ttl=900, show_spinner=False)
def search_stock_symbols(query):
    """Search Yahoo Finance's current symbol catalog for matching equities/ETFs."""
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
            if symbol and quote_type in {"EQUITY", "ETF"}:
                matches.append({
                    "symbol": symbol,
                    "name": item.get("shortname") or item.get("longname") or symbol,
                    "type": quote_type
                })
        return matches
    except Exception:
        return []

RECOMMENDATION_UNIVERSE = [
    "SPY", "QQQ", "IWM", "DIA", "AAPL", "MSFT", "NVDA", "AMD",
    "AMZN", "META", "GOOGL", "TSLA", "AVGO", "NFLX", "JPM",
    "XOM", "LLY", "COST", "PLTR", "ORCL"
]

@st.cache_data(ttl=600, show_spinner=False)
def scan_recommendation_candidates(scan_interval="15m", prepost=False, rr_ratio=1.8):
    """Rank a liquid, predefined US-stock universe using transparent technical rules."""
    rows = []
    for symbol in RECOMMENDATION_UNIVERSE:
        try:
            raw = get_intraday_data(symbol, scan_interval, prepost=prepost)
            if raw is None or raw.empty or len(raw) < 30:
                continue
            enriched = add_indicators(raw)
            stats = compute_price_targets_and_signal(
                enriched, None, None, scan_interval, rr_ratio
            )
            side = stats["side"]
            if side not in {"LONG", "SHORT"}:
                continue
            rows.append({
                "Symbol": symbol,
                "Price": round(stats["price"], 2),
                "Bias": "Bullish" if side == "LONG" else "Bearish",
                "Score": f'{stats["score"]}/5',
                "RSI": round(stats["rsi"], 1),
                "Entry": round(stats["ideal_buy"], 2),
                "Stop": round(stats["stop"], 2),
                "Target": round(stats["ideal_sell"], 2),
                "_score": int(stats["score"]),
                "_side": side
            })
        except Exception:
            continue
    rows.sort(key=lambda row: row["_score"], reverse=True)
    return rows

# ---------- Session State ----------
defaults = {
    "watchlist": ["SPY", "QQQ", "AAPL", "TSLA", "NVDA"],
    "active_ticker": "SPY",
    "paper_trades": [],
    "account_size": 25000.0,
    "daily_loss_limit": 300.0,
    "last_alert_action": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("### 🎛️ Terminal Settings")
    dash_mode = st.radio(
        "Experience Level",
        ["Beginner (Simple)", "Advanced (Pro)"],
        index=0,
        help="Switch between learning view and pro trading view."
    )

    st.markdown("---")
    st.markdown("### 🔎 Find a Stock")
    search_query = st.text_input(
        "Search ticker or company",
        placeholder="Type e.g. Apple, NVDA, Microsoft",
        key="symbol_search_query",
        help="Press Enter or click Search to retrieve matching current Yahoo Finance symbols."
    )
    if st.button("Search symbols", key="run_symbol_search", use_container_width=True):
        st.session_state["symbol_search_results"] = search_stock_symbols(search_query)
    search_results = st.session_state.get("symbol_search_results", [])
    if search_results:
        options = {
            f'{item["symbol"]} — {item["name"]} ({item["type"]})': item["symbol"]
            for item in search_results
        }
        selected_label = st.selectbox("Matching symbols · select to autofill", list(options.keys()), key="symbol_search_pick")
        selected_symbol = options[selected_label]
        if st.button("＋ Add selected to Watchlist", key="add_search_symbol", use_container_width=True):
            if selected_symbol not in st.session_state.watchlist:
                st.session_state.watchlist.append(selected_symbol)
            st.session_state.active_ticker = selected_symbol
            st.rerun()
    elif search_query and st.session_state.get("symbol_search_results") == []:
        st.caption("Run Search symbols to see matching stocks and ETFs.")

    st.markdown("### ⭐ Your Watchlist")
    manual_sym = st.text_input("Or enter a ticker manually", placeholder="e.g. META", key="manual_watch_symbol").upper().strip()
    if st.button("➕ Add manual ticker", key="add_manual_symbol") and manual_sym:
        if manual_sym not in st.session_state.watchlist:
            st.session_state.watchlist.append(manual_sym)
        st.session_state.active_ticker = manual_sym
        st.rerun()

    st.write("Quick Select:")
    for sym in st.session_state.watchlist:
        btn_type = "primary" if sym == st.session_state.active_ticker else "secondary"
        if st.button(f"⚡ {sym}", key=f"btn_{sym}", type=btn_type, use_container_width=True):
            st.session_state.active_ticker = sym
            st.rerun()

    st.markdown("---")
    st.markdown("### 📈 Chart & Risk Controls")

    chart_type = st.selectbox(
        "Chart Style",
        ["Candlestick", "Line Chart"],
        index=0
    )

    timeframe_options = ["1m", "2m", "5m", "15m", "30m", "60m"]
    interval = st.selectbox(
        "Chart Timeframe",
        timeframe_options,
        index=0,
        format_func=lambda value: "1h (60m)" if value == "60m" else value,
        help="Yahoo Finance intraday intervals. 1m data has a shorter lookback than larger intervals."
    )
    trend_interval = st.selectbox(
        "Trend / Bullish-Bearish Timeframe",
        timeframe_options,
        index=3,
        format_func=lambda value: "1h (60m)" if value == "60m" else value,
        help="Choose the timeframe used for the separate trend confirmation reading."
    )

    include_247 = st.checkbox(
        "Include Pre/Post-Market",
        value=True,
        help="Pulls 4:00 AM – 8:00 PM EST extended session data."
    )

    # Expanded Account Size Range ($50 to $100,000+)
    st.session_state.account_size = st.number_input(
        "Account Size ($)",
        min_value=50.0,
        max_value=1000000.0,
        value=st.session_state.account_size,
        step=500.0
    )

    # Expanded Risk Percentage Range (up to 5.0%)
    risk_pct = st.slider(
        "Risk Per Trade (%)",
        0.1, 5.0, 0.5, 0.1
    ) / 100

    # Expanded Reward-to-Risk Range (up to 5.0x)
    rr_ratio = st.slider(
        "Reward-to-Risk Target",
        1.0, 5.0, 1.8, 0.1
    )

    st.session_state.daily_loss_limit = st.number_input(
        "Max Daily Loss ($)",
        min_value=10.0,
        value=st.session_state.daily_loss_limit,
        step=50.0
    )

    refresh_sec = st.slider("Auto-Refresh Rate (sec)", 8, 60, 8)
    auto = st.checkbox("Enable Live Auto-Refresh", value=True)

    st.markdown("---")
    st.caption("Yahoo Finance data can be delayed or rate-limited. Intraday history varies by timeframe.")

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
    return {
        "daily_atr": daily_atr,
        "today_open": today_open,
        "prev_close": prev_day_close,
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
    long_stop = round(long_entry - stop_dist, 2)
    short_stop = round(short_entry + stop_dist, 2)
    long_target = round(long_entry + stop_dist * float(rr_ratio), 2)
    short_target = round(short_entry - stop_dist * float(rr_ratio), 2)

    # Keep legacy output keys while making their meaning direction-aware.
    if long_score >= 4 and long_score > short_score and price <= long_entry + atr * 0.35:
        action = "🚀 BUY NOW (STRONG SETUP)"
        reasons = [
            f"Long setup score is {long_score}/5 with price above VWAP",
            "EMA 9 is above EMA 20 and momentum is not overextended",
            f"Illustrative long target ${long_target:.2f}; stop ${long_stop:.2f}"
        ]
        side, score = "LONG", long_score
        ideal_buy, stop, ideal_sell = round(long_entry, 2), long_stop, long_target
    elif short_score >= 4 and short_score > long_score:
        action = "🔻 SHORT / SELL NOW"
        reasons = [
            f"Short setup score is {short_score}/5 with price below VWAP",
            "EMA 9 is below EMA 20 and downside momentum is aligned",
            f"Illustrative short target ${short_target:.2f}; stop ${short_stop:.2f}"
        ]
        side, score = "SHORT", short_score
        ideal_buy, stop, ideal_sell = round(short_entry, 2), short_stop, short_target
    elif long_score >= 3 and long_score > short_score:
        action = f"⏳ WAIT FOR PULLBACK TO ${long_entry:.2f}"
        reasons = ["Bullish conditions are developing, but entry confirmation is incomplete.",
                   f"Watch the long entry area near ${long_entry:.2f}."]
        side, score = "LONG", long_score
        ideal_buy, stop, ideal_sell = round(long_entry, 2), long_stop, long_target
    elif short_score >= 3 and short_score > long_score:
        action = f"⏳ WAIT FOR SHORT SETUP NEAR ${short_entry:.2f}"
        reasons = ["Bearish conditions are developing, but entry confirmation is incomplete.",
                   f"Watch the short entry area near ${short_entry:.2f}."]
        side, score = "SHORT", short_score
        ideal_buy, stop, ideal_sell = round(short_entry, 2), short_stop, short_target
    else:
        action = "🛡️ WAIT (NO CLEAR SETUP)"
        reasons = ["Trend, momentum, and volume are not sufficiently aligned.",
                   f"VWAP is ${vwap:.2f}; wait for a confirmed reclaim or rejection."]
        side, score = "None", max(long_score, short_score)
        ideal_buy, stop, ideal_sell = round(price, 2), round(price - stop_dist, 2), round(price + stop_dist * float(rr_ratio), 2)

    mins_per_bar = {"1m": 1, "2m": 2, "5m": 5, "15m": 15, "30m": 30, "60m": 60}.get(interval, 1)
    hourly_expected_move = atr * np.sqrt(60 / mins_per_bar) * 0.55
    bias_mult = 1.0 if (above_vwap and ema_up) else (-1.0 if (below_vwap and ema_down) else 0.0)
    hourly_target = round(price + hourly_expected_move * bias_mult, 2)

    if daily_stats:
        d_atr = max(float(daily_stats["daily_atr"]), 0.0)
        anchor = float(daily_stats["today_open"])
        daily_target = round(price + d_atr * 0.35 * bias_mult, 2)
        daily_range = (round(anchor - d_atr * 0.75, 2), round(anchor + d_atr * 0.75, 2))
    else:
        daily_target = round(price + hourly_expected_move * 2.5 * bias_mult, 2)
        daily_range = (round(swing_low, 2), round(swing_high, 2))

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

# ---------- LIVE DASHBOARD FRAGMENT ----------
run_interval = refresh_sec if auto else None

@st.fragment(run_every=run_interval)
def render_dashboard():
    ticker = st.session_state.active_ticker
    session_label, now_est = get_market_session()

    try:
        df_raw = get_intraday_data(ticker, interval, prepost=include_247)
        if df_raw.empty:
            st.error("Could not load data. Check the stock symbol.")
            return

        df = add_indicators(df_raw)
        fast_px = get_fast_quote(ticker)
        daily_stats = get_daily_stats(ticker)
        sig = compute_price_targets_and_signal(df, fast_px, daily_stats, interval, rr_ratio)

        price = sig["price"]
        
        if "BUY NOW" in sig["action"] or "SHORT" in sig["action"]:
            if st.session_state.last_alert_action != sig["action"]:
                st.toast(f"🚨 ALERT: {sig['action']} on {ticker} @ ${price:.2f}!", icon="⚡")
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
                qty = int(trade.get("shares", 0))
                if trade.get("side") == "LONG":
                    today_unrealized += (mark - trade["entry"]) * qty
                else:
                    today_unrealized += (trade["entry"] - mark) * qty
        today_pnl = today_realized + today_unrealized
        limit_hit = today_pnl <= -st.session_state.daily_loss_limit

        st.markdown(f"## ⚡ {ticker} — ${price:.2f}")
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
        c1.metric("Current Price", f"${price:.2f}", help="The latest available quote. Yahoo Finance data may be delayed.")
        c2.metric("VWAP (Fair Value)", f"${sig['vwap']:.2f}", help="Volume-Weighted Average Price; a session reference, not a prediction.")
        c3.metric("RSI (Momentum)", f"{sig['rsi']:.0f}", help="Momentum gauge from 0 to 100. It can remain high or low during strong trends.")
        c4, c5 = st.columns(2)
        c4.metric("Setup Score", f"{sig['score']}/5", help="How many of the five technical checks are met. This is not a probability of success.")
        c5.metric(
            f"{'1h' if trend_interval == '60m' else trend_interval} Trend",
            get_higher_tf_bias(ticker, include_247, trend_interval),
            help=f"EMA 9 versus EMA 20 trend confirmation on the selected {trend_interval} timeframe."
        )

        if dash_mode == "Advanced (Pro)":
            st.markdown("##### 🔬 Advanced Pro Telemetry")
            ac1, ac2, ac3, ac4 = st.columns(4)
            ac1.metric("ATR (Volatility)", f"${df.iloc[-1]['ATR']:.2f}", help="Average True Range measures how much the stock typically moves per candle.")
            ac2.metric("Volume vs MA", f"{df.iloc[-1]['Volume'] / max(df.iloc[-1]['Vol_MA'], 1):.2f}x", help="Current volume compared to its 8-period average. Higher means stronger interest.")
            ac3.metric("EMA 9 / EMA 20 Spread", f"${df.iloc[-1]['EMA9'] - df.iloc[-1]['EMA20']:+.2f}", help="Distance between short-term trend averages.")
            ac4.metric("Session High / Low", f"${df.tail(45)['High'].max():.2f} / ${df.tail(45)['Low'].min():.2f}", help="Highest and lowest prices reached in the current trading window.")

        st.markdown("#### 🎯 Live Price Targets & Trade Zones")
        t1, t2, t3, t4 = st.columns(4)
        buy_delta = ((sig["ideal_buy"] - price) / price) * 100
        sell_delta = ((sig["ideal_sell"] - price) / price) * 100
        hr_delta = ((sig["hourly_target"] - price) / price) * 100
        day_delta = ((sig["daily_target"] - price) / price) * 100

        t1.metric("Ideal Buy Price", f"${sig['ideal_buy']:.2f}", f"{buy_delta:+.2f}% from now", help="The recommended entry price based on pullback support so you don't chase peaks.")
        t2.metric("Ideal Sell Price", f"${sig['ideal_sell']:.2f}", f"{sell_delta:+.2f}% from now", help="Your target exit price for taking profit based on your Reward-to-Risk ratio.")
        t3.metric("Hourly Target (1H)", f"${sig['hourly_target']:.2f}", f"{hr_delta:+.2f}% projected", help="Expected price movement over the next hour based on volatility.")
        t4.metric(
            "Daily Target (EOD)",
            f"${sig['daily_target']:.2f}",
            f"{day_delta:+.2f}% (Range: ${sig['daily_range'][0]}–${sig['daily_range'][1]})",
            help="Projected end-of-day price boundary based on 14-day average volatility."
        )

        left, right = st.columns(2)
        with left:
            st.markdown("#### 💡 Why this setup?")
            for r in sig["reasons"]:
                st.markdown(f"- {r}")

            # Beginner Glossary / Dark-Themed Expander
            with st.expander("👶 Beginner's Guide: What do these terms mean?"):
                st.markdown("""
- **VWAP (Fair Value Line)**: The average price people paid today, weighted by volume. If price is above VWAP, buyers are winning. If below, sellers are winning.
- **RSI (Momentum Gauge)**: Tells you if a stock has moved too fast. Above 70 means it might be due for a cooldown; below 30 means it might bounce back up.
- **EMA 9 & EMA 20 (Trend Lines)**: Short-term averages. When the faster line (9) is *above* the slower line (20), the short-term trend is pointing up.
- **Stop Loss**: Your emergency exit price to limit losses if the trade goes against you.
- **Take Profit / Target**: The price where you automatically cash out your winnings.
                """)

        with right:
            st.markdown("#### ⚡ Quick Trade Execution")
            st.markdown(f"**Ideal Entry**: `${sig['ideal_buy']:.2f}`  |  **Stop Loss**: `${sig['stop']:.2f}`  |  **Take Profit**: `${sig['ideal_sell']:.2f}`")

            risk_dollars = st.session_state.account_size * risk_pct
            stop_dist = max(float(sig["stop_dist"]), 0.01)
            risk_based_shares = int(risk_dollars / stop_dist)
            buying_power_shares = int(st.session_state.account_size / max(price, 0.01))
            shares = max(0, min(risk_based_shares, buying_power_shares))
            actual_risk = shares * stop_dist
            st.markdown(
                f"**Position Size**: `{shares}` shares "
                f"(risk budget `${risk_dollars:,.2f}`; estimated risk `${actual_risk:,.2f}`; "
                f"buying-power cap `{buying_power_shares}` shares)"
            )

            already_open = any(
                t["ticker"] == ticker and t["status"] == "OPEN"
                for t in st.session_state.paper_trades
            )

            if not limit_hit and shares > 0:
                b1, b2 = st.columns(2)
                if already_open:
                    st.info(f"You already have an open paper trade on {ticker}.")
                else:
                    if b1.button(f"🚀 Paper BUY @ ${price:.2f}", type="primary", use_container_width=True, disabled=(sig["side"] != "LONG")):
                        st.session_state.paper_trades.append({
                            "id": str(uuid.uuid4())[:8],
                            "time": datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M"),
                            "ticker": ticker,
                            "side": "LONG",
                            "entry": round(price, 2),
                            "stop": sig["stop"],
                            "target": sig["ideal_sell"],
                            "shares": shares,
                            "status": "OPEN",
                            "exit": None,
                            "pnl": None,
                            "notes": "Quick Execution Signal"
                        })
                        st.rerun()

                    if b2.button(f"🔻 Paper SHORT @ ${price:.2f}", type="secondary", use_container_width=True, disabled=(sig["side"] != "SHORT")):
                        short_stop = round(price + stop_dist, 2)
                        short_target = round(price - stop_dist * rr_ratio, 2)
                        st.session_state.paper_trades.append({
                            "id": str(uuid.uuid4())[:8],
                            "time": datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M"),
                            "ticker": ticker,
                            "side": "SHORT",
                            "entry": round(price, 2),
                            "stop": short_stop,
                            "target": short_target,
                            "shares": shares,
                            "status": "OPEN",
                            "exit": None,
                            "pnl": None,
                            "notes": "Quick Execution Signal"
                        })
                        st.rerun()

        # ---------- DYNAMIC CHART WITH ZOOM / TOOLBAR & MARKERS ----------
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

        fig.add_hline(y=sig["ideal_buy"], line_dash="dot", line_color="#10b981", annotation_text=f"Ideal Buy ${sig['ideal_buy']:.2f}", row=1, col=1)
        fig.add_hline(y=sig["ideal_sell"], line_dash="dot", line_color="#ef4444", annotation_text=f"Ideal Sell ${sig['ideal_sell']:.2f}", row=1, col=1)
        fig.add_hline(y=sig["hourly_target"], line_dash="dash", line_color="#06b6d4", annotation_text=f"1H Target ${sig['hourly_target']:.2f}", row=1, col=1)

        bar_colors = ["#10b981" if c >= o else "#ef4444" for c, o in zip(plot_df["Close"], plot_df["Open"])]
        fig.add_trace(go.Bar(x=plot_df.index, y=plot_df["Volume"], name="Volume", marker_color=bar_colors, opacity=0.6), row=2, col=1)

        fig.update_layout(
            height=470,
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

        # ---------- PRO TRADING JOURNAL & PROGRESS ANALYTICS ----------
        st.markdown("---")
        st.markdown("### 📓 Trading Journal & Progress Analytics")

        open_trades = [t for t in st.session_state.paper_trades if t["status"] == "OPEN"]
        closed_trades = [t for t in st.session_state.paper_trades if t["status"] == "CLOSED"]

        with st.expander("✍️ Add Custom Trade to Journal"):
            with st.form("manual_trade_form"):
                jc1, jc2, jc3, jc4 = st.columns(4)
                j_ticker = jc1.text_input("Ticker", value=ticker).upper()
                j_side = jc2.selectbox("Side", ["LONG", "SHORT"])
                j_entry = jc3.number_input("Entry Price", value=float(price), format="%.2f")
                j_shares = jc4.number_input("Shares", min_value=1, value=100)
                
                jc5, jc6 = st.columns(2)
                j_stop = jc5.number_input("Stop Loss", value=float(price * 0.99), format="%.2f")
                j_target = jc6.number_input("Take Profit", value=float(price * 1.02), format="%.2f")
                
                j_notes = st.text_area("Trading Notes / Psychology / Strategy Setup", placeholder="e.g. VWAP reclaim on strong morning volume...")
                
                submitted = st.form_submit_button("Save Trade to Journal")
                if submitted:
                    valid_levels = (j_entry > 0 and j_shares > 0 and
                                    ((j_side == "LONG" and j_stop < j_entry < j_target) or
                                     (j_side == "SHORT" and j_target < j_entry < j_stop)))
                    if not valid_levels:
                        st.error("Check trade levels: LONG requires stop < entry < target; SHORT requires target < entry < stop.")
                        st.stop()
                    st.session_state.paper_trades.append({
                        "id": str(uuid.uuid4())[:8],
                        "time": datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M"),
                        "ticker": j_ticker,
                        "side": j_side,
                        "entry": j_entry,
                        "stop": j_stop,
                        "target": j_target,
                        "shares": j_shares,
                        "status": "OPEN",
                        "exit": None,
                        "pnl": None,
                        "notes": j_notes
                    })
                    st.success("Trade logged successfully!")
                    st.rerun()

        if open_trades:
            st.markdown("#### 📂 Active Positions")
            for t in open_trades:
                live_px = price if t["ticker"] == ticker else (get_fast_quote(t["ticker"]) or t["entry"])
                unrealized = (live_px - t["entry"]) * t["shares"] if t["side"] == "LONG" else (t["entry"] - live_px) * t["shares"]

                cols = st.columns([1.2, 0.9, 0.9, 1.0, 1.2, 1.0])
                cols[0].write(f"**{t['ticker']}** ({t['side']})\n\n{t['shares']} sh")
                cols[1].write(f"Entry: `${t['entry']}`\n\nLive: `${live_px:.2f}`")
                cols[2].write(f"Stop: `${t['stop']}`\n\nTarget: `${t['target']}`")
                cols[3].write(f"Unrealized:\n\n**${unrealized:+.2f}**")
                exit_px = cols[4].number_input("Exit Price", value=float(live_px), key=f"ex_{t['id']}", format="%.2f")
                if cols[5].button("Close Trade", key=f"cl_{t['id']}", use_container_width=True):
                    pnl = (exit_px - t["entry"]) * t["shares"] if t["side"] == "LONG" else (t["entry"] - exit_px) * t["shares"]
                    t["exit"] = exit_px
                    t["pnl"] = round(pnl, 2)
                    t["closed_at"] = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M")
                    t["status"] = "CLOSED"
                    st.rerun()

        if closed_trades:
            st.markdown("#### 📊 Progress Analytics & Closed History")
            cdf = pd.DataFrame(closed_trades)
            
            total_pnl = sum(t["pnl"] for t in closed_trades if t["pnl"] is not None)
            wins = [t for t in closed_trades if t["pnl"] and t["pnl"] > 0]
            losses = [t for t in closed_trades if t["pnl"] and t["pnl"] < 0]
            win_rate = (len(wins) / len(closed_trades)) * 100 if closed_trades else 0
            
            pk1, pk2, pk3, pk4 = st.columns(4)
            pk1.metric("Total P&L", f"${total_pnl:+,.2f}")
            pk2.metric("Win Rate", f"{win_rate:.1f}%", f"{len(wins)} Wins / {len(losses)} Losses")
            pk3.metric("Avg Win", f"${sum(w['pnl'] for w in wins)/len(wins):,.2f}" if wins else "$0.00")
            pk4.metric("Avg Loss", f"${sum(l['pnl'] for l in losses)/len(losses):,.2f}" if losses else "$0.00")

            cdf["cumulative_pnl"] = cdf["pnl"].cumsum()
            fig_eq = px.line(
                cdf, x="time", y="cumulative_pnl", 
                title="📈 Cumulative Equity Curve (Progress Over Time)",
                labels={"cumulative_pnl": "Net P&L ($)", "time": "Trade Time"},
                markers=True
            )
            fig_eq.update_layout(
                paper_bgcolor="#121824", plot_bgcolor="#121824",
                font=dict(color="#f8fafc"), height=300,
                xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b")
            )
            fig_eq.update_traces(line_color="#10b981" if total_pnl >= 0 else "#ef4444", line_width=3)
            st.plotly_chart(fig_eq, use_container_width=True)

            st.dataframe(
                cdf[["time", "ticker", "side", "entry", "exit", "shares", "pnl", "notes"]],
                use_container_width=True,
                hide_index=True
            )

            col_exp, col_clr = st.columns([1, 1])
            with col_exp:
                csv_buffer = io.StringIO()
                cdf.to_csv(csv_buffer, index=False)
                st.download_button(
                    "📥 Export Journal as CSV",
                    csv_buffer.getvalue(),
                    file_name=f"trading_journal_{date.today()}.csv",
                    mime="text/csv"
                )
            with col_clr:
                if st.button("🗑️ Clear Journal History"):
                    st.session_state.paper_trades = []
                    st.rerun()

        if st.session_state.paper_trades and not closed_trades and not open_trades:
            st.info("No active trades in journal.")

    except Exception as e:
        st.error(f"Something went wrong: {e}")

render_dashboard()

# ---------- SEPARATE MARKET IDEAS PANEL (not the personal watchlist) ----------
with st.expander("⭐ Market Candidate Scanner — separate from your watchlist", expanded=False):
    st.caption(
        "Screens a curated universe of liquid US stocks/ETFs using technical conditions. "
        "These are research candidates, not personalized investment advice."
    )
    rec_col1, rec_col2, rec_col3 = st.columns([1, 1, 2])
    with rec_col1:
        rec_interval = st.selectbox(
            "Scanner timeframe",
            ["1m", "5m", "15m", "30m", "60m"],
            index=2,
            format_func=lambda value: "1h" if value == "60m" else value,
            key="recommendation_interval"
        )
    with rec_col2:
        rec_prepost = st.checkbox("Include extended hours in scan", value=False, key="recommendation_prepost")
    with rec_col3:
        st.write("")
        refresh_recs = st.button("🔄 Scan / Refresh candidates", key="refresh_recommendations")

    if "recommendation_rows" not in st.session_state:
        st.session_state.recommendation_rows = []
    if refresh_recs:
        with st.spinner(f"Scanning the candidate list on {rec_interval} bars…"):
            st.session_state.recommendation_rows = scan_recommendation_candidates(
                rec_interval, rec_prepost, rr_ratio
            )
            st.session_state.recommendation_scan_time = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %I:%M:%S %p ET")

    rec_rows = st.session_state.recommendation_rows
    if rec_rows:
        if st.session_state.get("recommendation_scan_time"):
            st.caption(f"Last scan: {st.session_state.recommendation_scan_time}")
        display_recs = pd.DataFrame(rec_rows).drop(columns=["_score", "_side"], errors="ignore")
        st.dataframe(
            display_recs,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Symbol": st.column_config.TextColumn("Ticker"),
                "Bias": st.column_config.TextColumn("Technical bias"),
                "Score": st.column_config.TextColumn("Setup score")
            }
        )
        candidate_symbols = [row["Symbol"] for row in rec_rows]
        chosen_candidate = st.selectbox("Choose a candidate to add", candidate_symbols, key="candidate_to_add")
        if st.button("＋ Add selected candidate to Watchlist", key="add_top_candidate"):
            if chosen_candidate not in st.session_state.watchlist:
                st.session_state.watchlist.append(chosen_candidate)
            st.session_state.active_ticker = chosen_candidate
            st.rerun()
    else:
        st.info("The scanner has not run yet. Select ‘Scan / Refresh candidates’ when you want to look for setups.")

st.markdown("---")
st.warning("""
**⚠️ Educational Disclaimer**  
This tool uses Yahoo Finance data, which may be delayed, incomplete, or unavailable. Signals and price targets are rule-based estimates, not predictions or investment advice.  
Paper trades are simulations only; no broker orders are placed. Verify quotes and levels independently before making any real trading decision.
""")
