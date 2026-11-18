import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from zoneinfo import ZoneInfo
import html
from urllib.parse import quote

# ---------- Page Setup ----------
st.set_page_config(
    page_title="Pro Day Trade Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Modern Cyber-Terminal Dark Theme CSS ----------
st.markdown("""
<style>
:root {
  color-scheme: dark;
  --tv-bg: #131722;
  --tv-panel: #1e222d;
  --tv-panel-2: #191d28;
  --tv-border: #2a2e39;
  --tv-grid: #252a36;
  --tv-text: #d1d4dc;
  --tv-strong: #f0f3fa;
  --tv-muted: #8b919e;
  --tv-blue: #2962ff;
  --tv-green: #089981;
  --tv-red: #f23645;
}
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {
  background: var(--tv-bg) !important;
  color: var(--tv-text) !important;
}
.block-container {
  max-width: 1680px;
  padding: 1rem clamp(.8rem, 1.5vw, 1.6rem) 2rem;
}
header[data-testid="stHeader"] {
  background: rgba(19,23,34,.96) !important;
  border-bottom: 1px solid var(--tv-border);
}
h1, h2, h3, h4, h5, h6 {
  color: var(--tv-strong) !important;
  letter-spacing: -.015em;
  font-weight: 650 !important;
}
p, li, label, legend, [data-testid="stMarkdownContainer"] { color: var(--tv-text); }
[data-testid="stCaptionContainer"], .stCaption, small { color: var(--tv-muted) !important; }
hr { border-color: var(--tv-border) !important; margin: 1rem 0 !important; }

/* Sidebar */
section[data-testid="stSidebar"] {
  background: var(--tv-panel) !important;
  border-right: 1px solid var(--tv-border);
}

/* Inputs */
.stTextInput input, .stNumberInput input, .stTextArea textarea,
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea,
[data-baseweb="select"] > div, [data-baseweb="select"] input {
  background: #111622 !important;
  color: var(--tv-strong) !important;
  -webkit-text-fill-color: var(--tv-strong) !important;
  border: 1px solid #3a4050 !important;
  border-radius: 6px !important;
}
[data-baseweb="popover"], [data-baseweb="menu"],
[role="listbox"], [role="option"] {
  background: #1e222d !important;
  color: var(--tv-text) !important;
}
[role="option"]:hover, [role="option"][aria-selected="true"] {
  background: #2a3142 !important;
  color: #ffffff !important;
}

/* Buttons */
.stButton > button, .stDownloadButton > button {
  min-height: 2.45rem;
  border-radius: 6px !important;
  border: 1px solid #3a4050 !important;
  background: #252a36 !important;
  color: var(--tv-text) !important;
  font-weight: 600 !important;
}
.stButton > button:hover {
  background: #303747 !important;
  color: #ffffff !important;
  border-color: #65718a !important;
}
.stButton > button[kind="primary"] {
  background: var(--tv-blue) !important;
  border-color: var(--tv-blue) !important;
  color: #ffffff !important;
}

/* Metric Cards */
[data-testid="stMetric"] {
  background: var(--tv-panel) !important;
  border: 1px solid var(--tv-border) !important;
  border-radius: 7px !important;
  padding: 11px 13px !important;
}
[data-testid="stMetric"] [data-testid="stMetricLabel"] {
  color: var(--tv-muted) !important;
  font-size: .8rem !important;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
  color: var(--tv-strong) !important;
  font-size: clamp(1.05rem, 1.5vw, 1.4rem) !important;
  font-weight: 650 !important;
}
[data-testid="stMetric"] [data-testid="stMetricDelta"] {
  display: inline-flex !important;
  padding: 2px 7px !important;
  margin-top: 3px !important;
  border: 1px solid #3b4658 !important;
  border-radius: 5px !important;
  background: #252c39 !important;
  color: #dce5f2 !important;
  font-weight: 600 !important;
}

/* Custom Headings, Tooltips, Banners & Notices */
.info-tip {
  display:inline-flex; align-items:center; justify-content:center;
  width:16px; height:16px; margin-left:6px;
  border:1px solid #59657a; border-radius:50%;
  color:#aab6ca; font-size:10px; font-weight:700;
  cursor:help; vertical-align:middle; position:relative;
}
.info-tip:hover { background:#273247; border-color:#8294b4; color:#ffffff; }
.info-tip[title]:hover::after {
  content:attr(title); position:absolute; z-index:99999;
  left:50%; top:calc(100% + 7px); transform:translateX(-50%);
  width:240px; white-space:normal; padding:9px 11px;
  border:1px solid #46536a; border-radius:6px;
  background:#1e222d; color:#d1d4dc; font-size:12px;
  line-height:1.4; font-weight:400; box-shadow:0 5px 16px rgba(0,0,0,.45);
  pointer-events:none;
}
.terminal-kicker {
  color:#8b9bb8; text-transform:uppercase; letter-spacing:.12em;
  font-size:.72rem; font-weight:700;
}
.terminal-hero {
  padding: .9rem 1.1rem; margin:.15rem 0 .9rem;
  border:1px solid var(--tv-border); border-radius:8px;
  background:var(--tv-panel);
}
.terminal-hero h1 { margin:.15rem 0 .25rem; font-size:clamp(1.45rem,2.4vw,1.9rem); }
.terminal-hero p { margin:0; color:var(--tv-muted) !important; }
.action-banner {
  font-size:clamp(1.05rem,1.8vw,1.35rem); font-weight:750;
  text-align:center; padding:11px 14px; border-radius:7px;
  margin:10px 0 14px; letter-spacing:.02em;
}
.buy { background:rgba(8,153,129,.16); color:#35c9ac; border:1px solid rgba(8,153,129,.55); }
.short { background:rgba(242,54,69,.15); color:#ff6b78; border:1px solid rgba(242,54,69,.55); }
.watch { background:rgba(41,98,255,.13); color:#83a7ff; border:1px solid rgba(41,98,255,.5); }

.terminal-notice {
  margin: .55rem 0 .8rem; padding: .75rem .9rem;
  border: 1px solid #40506a; border-left: 3px solid #6f9df5;
  border-radius: 7px; background: #222b3a !important;
  color: #dce5f2 !important; line-height: 1.5; font-size: .9rem;
}
.terminal-notice-learning { border-left-color: #d6a84f; background: #302b20 !important; color: #f0dfb4 !important; }

.educational-disclaimer {
  margin: 1.2rem 0 1.5rem; padding: 1rem 1.1rem;
  border: 1px solid #3a4050; border-left: 3px solid #d6a84f;
  border-radius: 8px; background: #1e222d !important;
  color: #d1d4dc !important; line-height: 1.55; font-size: .88rem;
}
.educational-disclaimer .disclaimer-heading {
  color: #e5c879 !important; font-size: .95rem; font-weight: 700; margin-bottom: .35rem;
}
</style>
""", unsafe_allow_html=True)

# ---------- UI Helper Functions ----------
def info_heading(label, explanation, level=3):
    safe_label = html.escape(str(label))
    safe_tip = html.escape(str(explanation), quote=True)
    st.markdown(
        f'<h{level} style="margin:.35rem 0 .55rem">{safe_label}'
        f'<span class="info-tip" title="{safe_tip}" aria-label="More information">i</span></h{level}>',
        unsafe_allow_html=True
    )

def render_terminal_notice(message, kind="info"):
    safe_message = html.escape(str(message))
    safe_kind = kind if kind in {"info", "learning", "position"} else "info"
    st.markdown(
        f'<div class="terminal-notice terminal-notice-{safe_kind}" role="status">{safe_message}</div>',
        unsafe_allow_html=True,
    )

# ---------- Universe & Search ----------
ASSET_NAMES = {
    "SPY": "SPDR S&P 500 ETF", "QQQ": "Invesco QQQ Trust", "IWM": "iShares Russell 2000 ETF",
    "AAPL": "Apple Inc.", "MSFT": "Microsoft Corporation", "NVDA": "NVIDIA Corporation",
    "AMD": "Advanced Micro Devices", "AMZN": "Amazon.com Inc.", "META": "Meta Platforms Inc.",
    "GOOGL": "Alphabet Inc.", "TSLA": "Tesla Inc.", "PLTR": "Palantir Technologies",
    "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana", "XRP-USD": "XRP",
    "DOGE-USD": "Dogecoin", "AVAX-USD": "Avalanche", "LINK-USD": "Chainlink"
}

@st.cache_data(ttl=900, show_spinner=False)
def search_stock_symbols(query):
    query = str(query or "").strip()
    if not query:
        return []
    try:
        result = yf.Search(query, max_results=25)
        quotes = getattr(result, "quotes", []) or []
        matches = []
        for item in quotes:
            qtype = str(item.get("quoteType", "")).upper()
            symbol = str(item.get("symbol", "")).upper()
            if symbol and qtype in {"EQUITY", "ETF", "CRYPTOCURRENCY", "CRYPTO"}:
                matches.append({
                    "symbol": symbol,
                    "name": item.get("shortname") or item.get("longname") or ASSET_NAMES.get(symbol, symbol),
                    "type": "CRYPTO" if "CRYPTO" in qtype else qtype
                })
        return matches
    except Exception:
        return []

def price_decimals(price):
    try:
        return 2 if abs(float(price)) >= 1 else 6
    except (TypeError, ValueError):
        return 2

def robinhood_asset_url(symbol):
    symbol = str(symbol or "").strip().upper()
    if not symbol:
        return "https://robinhood.com/"
    if symbol.endswith("-USD"):
        return f"https://robinhood.com/us/en/crypto/{quote(symbol[:-4].lower(), safe='')}/"
    return f"https://robinhood.com/us/en/stocks/{quote(symbol.lower(), safe='')}/"

# ---------- Core Quantitative Math ----------
def calculate_position_size(account_size, risk_fraction, entry, stop, target, is_crypto=False):
    try:
        account, risk_fraction, entry, stop, target = map(float, (account_size, risk_fraction, entry, stop, target))
    except (TypeError, ValueError):
        return {"valid": False, "reason": "Enter valid numeric values."}

    if account <= 0 or not (0 < risk_fraction <= 1) or min(entry, stop, target) <= 0:
        return {"valid": False, "reason": "All prices/account must be > 0 and risk between 0% and 100%."}

    side = "LONG" if stop < entry < target else ("SHORT" if target < entry < stop else None)
    if side is None:
        return {"valid": False, "reason": "LONG requires Stop < Entry < Target. SHORT requires Target < Entry < Stop."}

    stop_distance = abs(entry - stop)
    reward_distance = abs(target - entry)
    risk_budget = account * risk_fraction
    raw_qty = min(risk_budget / stop_distance, account / entry)

    if is_crypto:
        quantity = float(np.floor(raw_qty * 1_000_000) / 1_000_000)
        unit = "units"
    else:
        quantity = float(int(raw_qty))
        unit = "shares"

    if quantity <= 0:
        return {"valid": False, "reason": "Risk budget or account size is too small for 1 share/unit."}

    planned_risk = quantity * stop_distance
    return {
        "valid": True,
        "side": side,
        "quantity": quantity,
        "unit": unit,
        "risk_budget": risk_budget,
        "planned_risk": planned_risk,
        "position_value": quantity * entry,
        "potential_reward": quantity * reward_distance,
        "reward_to_risk": reward_distance / stop_distance,
        "risk_pct_used": (planned_risk / account) * 100,
    }

AI_FEATURE_NAMES = ("setup_strength", "vwap_alignment", "ema_alignment", "momentum_alignment", "volume_confirmation")

def directional_learning_features(signal, side):
    direction = 1.0 if side.upper() == "LONG" else -1.0
    score = float(signal.get("long_score" if direction > 0 else "short_score", 0.0))
    rsi = float(signal.get("rsi", 50.0))
    vwap_gap = float(signal.get("vwap_gap_pct", 0.0))
    ema_spread = float(signal.get("ema_spread_pct", 0.0))
    volume_ratio = float(signal.get("volume_ratio", 1.0))
    clip = lambda v: float(np.clip(v, -1.0, 1.0))
    return {
        "setup_strength": clip((score / 5.0) * 2.0 - 1.0),
        "vwap_alignment": clip(direction * vwap_gap / 0.50),
        "ema_alignment": clip(direction * ema_spread / 0.30),
        "momentum_alignment": clip(direction * (rsi - 50.0) / 25.0),
        "volume_confirmation": clip((volume_ratio - 1.0) / 1.50),
    }

def evaluate_perceptron_trade(features_dict, weights_dict, bias):
    activation = float(bias) + sum(float(weights_dict.get(k, 0.0)) * float(features_dict.get(k, 0.0)) for k in AI_FEATURE_NAMES)
    probability = 1.0 / (1.0 + np.exp(-np.clip(activation, -30.0, 30.0)))
    return probability, activation

# ---------- Market Data & Technical Engine ----------
@st.cache_data(ttl=120, show_spinner=False)
def fetch_intraday_data(symbol, period="5d", interval="5m"):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if df is None or df.empty:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna(subset=["Close", "High", "Low", "Open"]).copy()
        df["EMA9"] = df["Close"].ewm(span=9, adjust=False).mean()
        df["EMA21"] = df["Close"].ewm(span=21, adjust=False).mean()
        typical_price = (df["High"] + df["Low"] + df["Close"]) / 3.0
        cum_vol = df["Volume"].replace(0, np.nan).ffill().fillna(1).cumsum()
        df["VWAP"] = (typical_price * df["Volume"]).cumsum() / cum_vol

        delta = df["Close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        df["RSI"] = 100 - (100 / (1 + rs))
        df["RSI"] = df["RSI"].fillna(50.0)
        return df
    except Exception:
        return pd.DataFrame()

def analyze_signal(df, rr_ratio=2.0):
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last
    price = float(last["Close"])
    ema9 = float(last["EMA9"])
    ema21 = float(last["EMA21"])
    vwap = float(last["VWAP"])
    rsi = float(last["RSI"])
    avg_vol = float(df["Volume"].tail(20).mean()) or 1.0
    vol_ratio = float(last["Volume"]) / avg_vol

    vwap_gap_pct = (price - vwap) / vwap * 100.0
    ema_spread_pct = (ema9 - ema21) / ema21 * 100.0

    long_score = sum([
        price > vwap,
        ema9 > ema21,
        45 <= rsi <= 68,
        vol_ratio >= 1.1,
        price > float(prev["Close"])
    ])
    short_score = sum([
        price < vwap,
        ema9 < ema21,
        32 <= rsi <= 55,
        vol_ratio >= 1.1,
        price < float(prev["Close"])
    ])

    atr = float((df["High"] - df["Low"]).tail(14).mean())
    stop_gap = max(atr * 1.2, price * 0.003)
    digits = price_decimals(price)

    if long_score >= 3 and long_score > short_score:
        side = "LONG"
        stop = round(price - stop_gap, digits)
        target = round(price + stop_gap * rr_ratio, digits)
    elif short_score >= 3 and short_score > long_score:
        side = "SHORT"
        stop = round(price + stop_gap, digits)
        target = round(price - stop_gap * rr_ratio, digits)
    else:
        side = "WATCH"
        stop = round(price - stop_gap, digits)
        target = round(price + stop_gap * rr_ratio, digits)

    return {
        "price": price, "prev_close": float(prev["Close"]),
        "ema9": ema9, "ema21": ema21, "vwap": vwap, "rsi": rsi,
        "volume_ratio": vol_ratio, "vwap_gap_pct": vwap_gap_pct,
        "ema_spread_pct": ema_spread_pct, "long_score": long_score,
        "short_score": short_score, "side": side,
        "ideal_buy": round(price, digits), "stop": stop, "ideal_sell": target,
        "stop_gap": stop_gap
    }

# ---------- Session State Initialization ----------
if "paper_trades" not in st.session_state:
    st.session_state.paper_trades = []
if "ai_weights" not in st.session_state:
    st.session_state.ai_weights = {k: 0.45 for k in AI_FEATURE_NAMES}
    st.session_state.ai_bias = -0.15

# ---------- Sidebar Controls ----------
with st.sidebar:
    st.markdown("### ⚡ Terminal Controls")
    search_query = st.text_input("🔎 Search Ticker / Crypto", placeholder="e.g. NVDA, SPY, BTC-USD")
    search_matches = search_stock_symbols(search_query) if search_query else []

    quick_list = list(ASSET_NAMES.keys())
    if search_matches:
        options = [f"{m['symbol']} — {m['name']} ({m['type']})" for m in search_matches]
        selected_label = st.selectbox("Search Results", options)
        symbol = selected_label.split(" — ")[0].strip()
    else:
        symbol = st.selectbox("Active Watchlist", quick_list, index=quick_list.index("NVDA"))

    col_tf1, col_tf2 = st.columns(2)
    with col_tf1:
        interval = st.selectbox("Timeframe", ["1m", "5m", "15m", "30m", "1h"], index=1)
    with col_tf2:
        period = st.selectbox("Lookback", ["1d", "5d", "1mo"], index=1)

    st.divider()
    st.markdown("### 🛡️ Risk Parameters")
    account_size = st.number_input("Paper Account ($)", min_value=100.0, value=25000.0, step=500.0)
    risk_pct = st.slider("Risk per Trade (%)", min_value=0.25, max_value=5.0, value=1.0, step=0.25)
    rr_ratio = st.slider("Target R:R Ratio", min_value=1.0, max_value=5.0, value=2.0, step=0.25)

    st.divider()
    st.link_button("↗ Open Asset on Robinhood", robinhood_asset_url(symbol), use_container_width=True)

# ---------- Main Terminal Header ----------
now_est = datetime.now(ZoneInfo("America/New_York")).strftime("%I:%M:%S %p EST")
asset_title = ASSET_NAMES.get(symbol, symbol)
st.markdown(f"""
<div class="terminal-hero">
  <div class="terminal-kicker">⚡ INTRADAY EXECUTION & AI CONFLUENCE TERMINAL • {now_est}</div>
  <h1>{html.escape(symbol)} — {html.escape(asset_title)}</h1>
  <p>Real-time VWAP/EMA confluence, automated directional trade levels, and adaptive perceptron confidence scoring.</p>
</div>
""", unsafe_allow_html=True)

# ---------- Fetch & Analyze Data ----------
df = fetch_intraday_data(symbol, period=period, interval=interval)

if df.empty:
    st.error(f"Unable to fetch intraday bars for **{symbol}**. Verify the ticker or try a different timeframe.")
    st.stop()

sig = analyze_signal(df, rr_ratio=rr_ratio)
digits = price_decimals(sig["price"])
price_delta_pct = (sig["price"] - sig["prev_close"]) / sig["prev_close"] * 100.0

# ---------- Action Signal Banner ----------
if sig["side"] == "LONG":
    st.markdown(f'<div class="action-banner buy">🟢 BULLISH CONFLUENCE ({sig["long_score"]}/5) — LONG SETUP ACTIVE</div>', unsafe_allow_html=True)
elif sig["side"] == "SHORT":
    st.markdown(f'<div class="action-banner short">🔴 BEARISH CONFLUENCE ({sig["short_score"]}/5) — SHORT SETUP ACTIVE</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="action-banner watch">🔵 NEUTRAL / CHOP ({max(sig["long_score"], sig["short_score"])}/5) — WAIT FOR BREAKOUT</div>', unsafe_allow_html=True)

# ---------- Top KPI Strip ----------
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Last Price", f"${sig['price']:,.{digits}f}", f"{price_delta_pct:+.2f}%")
m2.metric("Session VWAP", f"${sig['vwap']:,.{digits}f}", f"{sig['vwap_gap_pct']:+.2f}% vs VWAP")
m3.metric("EMA 9 / 21 Spread", f"{sig['ema_spread_pct']:+.2f}%", "Bullish" if sig["ema9"] > sig["ema21"] else "Bearish")
m4.metric("RSI (14)", f"{sig['rsi']:.1f}", "Overbought" if sig["rsi"] > 70 else ("Oversold" if sig["rsi"] < 30 else "Neutral"))
m5.metric("Relative Volume", f"{sig['volume_ratio']:.2f}x", "High Activity" if sig["volume_ratio"] >= 1.2 else "Normal")

# ---------- Interactive Price & Volume Chart ----------
info_heading("Price Action, VWAP & EMA Ribbon", "Candlesticks overlaid with Session VWAP (amber), 9 EMA (cyan), and 21 EMA (purple).")

plot_df = df.tail(90)
fig = make_subplots(
    rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04,
    row_heights=[0.76, 0.24]
)

fig.add_trace(go.Candlestick(
    x=plot_df.index, open=plot_df["Open"], high=plot_df["High"],
    low=plot_df["Low"], close=plot_df["Close"], name="Price",
    increasing_line_color="#089981", decreasing_line_color="#f23645"
), row=1, col=1)

fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["VWAP"], name="VWAP", line=dict(color="#f5b041", width=1.8)), row=1, col=1)
fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["EMA9"], name="EMA 9", line=dict(color="#38bdf8", width=1.4)), row=1, col=1)
fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["EMA21"], name="EMA 21", line=dict(color="#c084fc", width=1.4)), row=1, col=1)

# Horizontal levels for Entry, Stop, Target
fig.add_hline(y=sig["ideal_buy"], line_dash="dot", line_color="#83a7ff", annotation_text="Entry", row=1, col=1)
fig.add_hline(y=sig["stop"], line_dash="dash", line_color="#f23645", annotation_text="Stop", row=1, col=1)
fig.add_hline(y=sig["ideal_sell"], line_dash="dash", line_color="#089981", annotation_text="Target", row=1, col=1)

vol_colors = ["#089981" if c >= o else "#f23645" for c, o in zip(plot_df["Close"], plot_df["Open"])]
fig.add_trace(go.Bar(x=plot_df.index, y=plot_df["Volume"], name="Volume", marker_color=vol_colors, opacity=0.7), row=2, col=1)

fig.update_layout(
    height=520, margin=dict(l=10, r=10, t=20, b=10),
    paper_bgcolor="#131722", plot_bgcolor="#191d28",
    font=dict(color="#d1d4dc"), xaxis_rangeslider_visible=False,
    legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1)
)
fig.update_xaxes(gridcolor="#252a36", showgrid=True)
fig.update_yaxes(gridcolor="#252a36", showgrid=True)
st.plotly_chart(fig, use_container_width=True)

# ---------- Lower Workspace: Position Sizer & AI Perceptron ----------
col_left, col_right = st.columns([1.15, 1.0], gap="large")

with col_left:
    info_heading("🎯 Automated Trade Plan & Risk Calculator", "Sizes your position dynamically based on your sidebar risk budget and stop distance.")
    is_crypto = symbol.endswith("-USD")
    plan_side = "SHORT" if sig["side"] == "SHORT" else "LONG"

    c1, c2, c3 = st.columns(3)
    entry_in = c1.number_input("Entry Price ($)", value=float(sig["ideal_buy"]), format=f"%.{digits}f")
    stop_in = c2.number_input("Stop Loss ($)", value=float(sig["stop"]), format=f"%.{digits}f")
    target_in = c3.number_input("Profit Target ($)", value=float(sig["ideal_sell"]), format=f"%.{digits}f")

    sizing = calculate_position_size(account_size, risk_pct / 100.0, entry_in, stop_in, target_in, is_crypto=is_crypto)

    if sizing["valid"]:
        s1, s2, s3 = st.columns(3)
        s1.metric("Position Size", f"{sizing['quantity']:,.4f} {sizing['unit']}" if is_crypto else f"{int(sizing['quantity'])} {sizing['unit']}", f"${sizing['position_value']:,.2f} Notional")
        s2.metric("Planned Risk", f"${sizing['planned_risk']:,.2f}", f"{sizing['risk_pct_used']:.2f}% of Account")
        s3.metric("Potential Reward", f"${sizing['potential_reward']:,.2f}", f"{sizing['reward_to_risk']:.2f}R Ratio")

        if st.button("📝 Log Simulated Paper Trade", type="primary", use_container_width=True):
            st.session_state.paper_trades.append({
                "Time": now_est,
                "Symbol": symbol,
                "Side": sizing["side"],
                "Qty": sizing["quantity"],
                "Entry": entry_in,
                "Stop": stop_in,
                "Target": target_in,
                "Risk ($)": round(sizing["planned_risk"], 2)
            })
            st.toast(f"Logged {sizing['side']} paper trade for {symbol}!")
    else:
        st.warning(sizing["reason"])

with col_right:
    info_heading("🧠 AI Perceptron Setup Confidence", "Evaluates normalized VWAP, EMA, RSI, and Volume alignment using adaptive weights.")
    eval_side = "SHORT" if sig["side"] == "SHORT" else "LONG"
    features = directional_learning_features(sig, eval_side)
    prob, activation = evaluate_perceptron_trade(features, st.session_state.ai_weights, st.session_state.ai_bias)

    p1, p2 = st.columns(2)
    p1.metric(f"{eval_side} Win Probability", f"{prob * 100:.1f}%", f"Logit: {activation:+.2f}")
    p2.metric("Confluence Score", f"{sig['long_score'] if eval_side == 'LONG' else sig['short_score']} / 5", "Technical Alignment")

    feat_df = pd.DataFrame({
        "Feature": [k.replace("_", " ").title() for k in features.keys()],
        "Signal (-1 to +1)": [round(v, 2) for v in features.values()]
    })
    st.dataframe(feat_df, use_container_width=True, hide_index=True)
    render_terminal_notice("AI confidence weights update dynamically as simulated paper trades are closed and reviewed.", kind="learning")

# ---------- Paper Trade Blotter ----------
if st.session_state.paper_trades:
    st.divider()
    info_heading("📒 Active Paper Trade Blotter", "Session-stored simulated positions.")
    st.dataframe(pd.DataFrame(st.session_state.paper_trades), use_container_width=True, hide_index=True)

# ---------- Footer Disclaimer ----------
st.markdown("""
<div class="educational-disclaimer">
  <div class="disclaimer-heading">⚠️ Educational & Paper-Trading Disclaimer</div>
  <p>This terminal is designed strictly for <strong>technical analysis education and paper-trading simulation</strong>. Intraday market data from Yahoo Finance may be delayed and does not constitute financial or investment advice.</p>
</div>
""", unsafe_allow_html=True)
