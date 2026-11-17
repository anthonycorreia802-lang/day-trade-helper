import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time

# ---------- Page setup ----------
st.set_page_config(
    page_title="Day Trade Helper",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for cleaner look
st.markdown("""
<style>
    .big-action {
        font-size: 2.4rem !important;
        font-weight: 800 !important;
        text-align: center;
        padding: 18px;
        border-radius: 14px;
        margin-bottom: 12px;
    }
    .buy { background: #0e7a3d; color: white; }
    .sell { background: #9b1c1c; color: white; }
    .watch { background: #1e3a5f; color: white; }
    .metric-label { font-size: 0.85rem; color: #888; }
    .stMetric { background: #0e1117; padding: 12px; border-radius: 10px; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; }
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar (minimal) ----------
with st.sidebar:
    st.header("Settings")
    ticker = st.text_input("Ticker", value="SPY").upper().strip()
    interval = st.selectbox("Speed", ["1m (fastest free)", "5m", "15m"], index=0)
    interval = interval.split()[0]          # clean value
    risk_pct = st.slider("Risk %", 0.25, 1.0, 0.5, 0.25) / 100
    rr_ratio = st.slider("Target R:R", 1.2, 3.0, 1.8, 0.1)
    auto = st.checkbox("Auto-refresh (45s)", value=True)
    st.caption("Free data is delayed. This is not true live data.")

# ---------- Data functions ----------
@st.cache_data(ttl=30, show_spinner=False)
def load_data(ticker, interval):
    period = "1d" if interval == "1m" else "5d"
    df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def add_indicators(df):
    df = df.copy()
    typical = (df["High"] + df["Low"] + df["Close"]) / 3
    df["TP_Vol"] = typical * df["Volume"]
    df["Date"] = df.index.date
    df["Cum_Vol"] = df.groupby("Date")["Volume"].cumsum()
    df["Cum_TP_Vol"] = df.groupby("Date")["TP_Vol"].cumsum()
    df["VWAP"] = df["Cum_TP_Vol"] / df["Cum_Vol"]
    df["EMA9"] = df["Close"].ewm(span=9, adjust=False).mean()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    df["Vol_MA"] = df["Volume"].rolling(8).mean()
    df["ATR"] = (df["High"] - df["Low"]).rolling(14).mean()
    return df

def decide_action(df):
    if len(df) < 20:
        return "WATCH", ["Waiting for more data…"], None, None, None

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    price = float(latest["Close"])
    vwap = float(latest["VWAP"])
    ema9 = float(latest["EMA9"])
    ema20 = float(latest["EMA20"])
    rsi = float(latest["RSI"])
    vol = float(latest["Volume"])
    vol_ma = float(latest["Vol_MA"]) if pd.notna(latest["Vol_MA"]) else vol

    reasons = []
    action = "WATCH"

    above_vwap = price > vwap
    ema_bull = ema9 > ema20
    reclaim = float(prev["Close"]) <= float(prev["VWAP"]) and price > vwap
    vol_ok = vol > vol_ma * 0.95
    rsi_ok = 38 < rsi < 72

    long_setup = above_vwap and ema_bull and reclaim and vol_ok and rsi_ok
    momentum_fail = price < vwap and ema9 < ema20
    overbought = rsi > 74 and above_vwap

    if long_setup:
        action = "BUY"
        reasons = [
            "Price just reclaimed VWAP",
            "Short momentum (EMA9 > EMA20) is up",
            f"Volume supportive • RSI {rsi:.0f}"
        ]
    elif momentum_fail:
        action = "SELL / AVOID"
        reasons = ["Price lost VWAP", "Short EMAs turned down"]
    elif overbought:
        action = "TAKE PROFIT"
        reasons = [f"RSI is high ({rsi:.0f})", "Consider scaling out or tightening stop"]
    elif price < vwap:
        action = "AVOID LONG"
        reasons = ["Price is below VWAP – no long bias"]
    else:
        action = "WATCH"
        reasons = ["No clean setup right now"]

    atr = float(latest["ATR"]) if pd.notna(latest["ATR"]) else price * 0.004
    stop_dist = max(atr * 1.15, price * 0.0028)
    stop = price - stop_dist
    target = price + stop_dist * rr_ratio

    return action, reasons, stop, target, stop_dist

# ---------- Main UI ----------
try:
    with st.spinner("Loading…"):
        raw = load_data(ticker, interval)

    if raw.empty:
        st.error("No data. Check the ticker.")
        st.stop()

    df = add_indicators(raw)
    action, reasons, stop, target, stop_dist = decide_action(df)

    latest = df.iloc[-1]
    price = float(latest["Close"])
    last_time = df.index[-1]
    data_age = datetime.now(last_time.tzinfo) - last_time if last_time.tzinfo else None

    # ===== BIG ACTION BANNER =====
    css_class = "buy" if action == "BUY" else ("sell" if "SELL" in action or "AVOID" in action else "watch")
    st.markdown(f'<div class="big-action {css_class}">{action}</div>', unsafe_allow_html=True)

    # ===== KEY NUMBERS =====
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Price", f"${price:.2f}")
    c2.metric("VWAP", f"${float(latest['VWAP']):.2f}")
    c3.metric("RSI", f"{float(latest['RSI']):.0f}")
    c4.metric("EMA9", f"${float(latest['EMA9']):.2f}")
    c5.metric("Data age", f"{int(data_age.total_seconds()//60)} min" if data_age else "—")

    # ===== REASONS + LEVELS =====
    left, right = st.columns([1.1, 1])

    with left:
        st.markdown("#### Why?")
        for r in reasons:
            st.markdown(f"- {r}")

    with right:
        if stop and target:
            st.markdown("#### Suggested levels")
            st.markdown(f"**Stop** → `${stop:.2f}`")
            st.markdown(f"**Target ({rr_ratio:.1f}R)** → `${target:.2f}`")
            st.markdown(f"**Risk per share** → `${stop_dist:.2f}`")
            st.caption(f"Size = (Account × {risk_pct*100:.1f}%) ÷ ${stop_dist:.2f}")

    # ===== CHECKLIST =====
    with st.expander("Setup checklist", expanded=False):
        prev = df.iloc[-2]
        checks = {
            "Price > VWAP": price > float(latest["VWAP"]),
            "EMA9 > EMA20": float(latest["EMA9"]) > float(latest["EMA20"]),
            "Just reclaimed VWAP": float(prev["Close"]) <= float(prev["VWAP"]) and price > float(latest["VWAP"]),
            "Volume OK": float(latest["Volume"]) > float(latest["Vol_MA"]) * 0.95,
            "RSI 38–72": 38 < float(latest["RSI"]) < 72,
        }
        cols = st.columns(5)
        for i, (name, ok) in enumerate(checks.items()):
            cols[i].markdown(f"{'✅' if ok else '❌'}  \n{name}")

    # ===== CHART =====
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.75, 0.25], vertical_spacing=0.02)

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="Price",
        increasing_line_color="#26a69a", decreasing_line_color="#ef5350"
    ), row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["VWAP"], name="VWAP",
                             line=dict(color="#42a5f5", width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA9"], name="EMA9",
                             line=dict(color="#ffca28", width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA20"], name="EMA20",
                             line=dict(color="#ab47bc", width=1.5)), row=1, col=1)

    colors = ["#26a69a" if c >= o else "#ef5350" for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Vol",
                         marker_color=colors, opacity=0.5), row=2, col=1)

    fig.update_layout(
        height=520,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(orientation="h", y=1.08),
        template="plotly_dark"
    )
    fig.update_yaxes(title_text="", row=1, col=1)
    fig.update_yaxes(title_text="", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Footer
    st.caption(f"Last bar: {last_time}  •  Free data is delayed  •  Educational use only")

    # Auto refresh
    if auto:
        time.sleep(45)
        st.rerun()

except Exception as e:
    st.error(f"Something went wrong: {e}")

st.markdown("---")
st.warning("This is **not** true real-time data and **not** financial advice. Most day traders lose money. Always use hard stops and never risk money you can’t afford to lose.")
