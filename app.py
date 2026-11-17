import time
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Day Trade Helper – Buy/Sell Guide",
    page_icon="📈",
    layout="wide",
)

st.title("Day Trading Buy / Sell Helper")
st.caption("Educational tool only • Delayed free data • Not real-time • Not financial advice")


# ---------- Sidebar ----------
st.sidebar.header("Settings")
ticker = st.sidebar.text_input("Ticker", value="SPY").upper().strip()
interval = st.sidebar.selectbox("Interval", ["1m", "5m", "15m"], index=1)
lookback = st.sidebar.selectbox("Lookback", ["1d", "5d", "10d"], index=1)
account_size = st.sidebar.number_input(
    "Account size ($)", min_value=100.0, value=10_000.0, step=500.0
)
risk_pct = st.sidebar.slider("Risk per trade (%)", 0.25, 1.0, 0.5, 0.25) / 100
rr_ratio = st.sidebar.slider("Target reward:risk", 1.2, 3.0, 1.8, 0.1)
auto_refresh = st.sidebar.checkbox("Auto-refresh every 60 seconds", value=False)


# ---------- Data helpers ----------
@st.cache_data(ttl=60)
def load_data(symbol: str, period: str, interval: str) -> pd.DataFrame:
    """Download and normalize Yahoo Finance intraday data."""
    effective_period = period
    if interval == "1m" and period == "10d":
        effective_period = "7d"

    df = yf.download(
        symbol,
        period=effective_period,
        interval=interval,
        progress=False,
        auto_adjust=True,
        threads=False,
    )

    if df is None or df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(df.columns):
        return pd.DataFrame()

    df = df[list(required)].copy()
    df = df.apply(pd.to_numeric, errors="coerce")
    return df.dropna()


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    typical = (df["High"] + df["Low"] + df["Close"]) / 3
    df["TP_Vol"] = typical * df["Volume"]
    df["Date"] = df.index.date
    df["Cum_Vol"] = df.groupby("Date")["Volume"].cumsum()
    df["Cum_TP_Vol"] = df.groupby("Date")["TP_Vol"].cumsum()
    df["VWAP"] = df["Cum_TP_Vol"] / df["Cum_Vol"].replace(0, np.nan)

    df["EMA9"] = df["Close"].ewm(span=9, adjust=False).mean()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))
    df["RSI"] = df["RSI"].replace([np.inf, -np.inf], np.nan)

    df["Vol_MA"] = df["Volume"].rolling(10).mean()
    df["Range"] = df["High"] - df["Low"]
    df["ATR"] = df["Range"].rolling(14).mean()
    return df


def get_action(df: pd.DataFrame):
    """Return the current mechanical setup and suggested long levels."""
    if len(df) < 25:
        return "WAIT", ["Not enough data yet"], None, None, None

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    price = float(latest["Close"])
    vwap = float(latest["VWAP"])
    ema9 = float(latest["EMA9"])
    ema20 = float(latest["EMA20"])
    rsi = float(latest["RSI"])
    vol = float(latest["Volume"])
    vol_ma = float(latest["Vol_MA"])

    if not np.isfinite(rsi):
        rsi = np.nan

    reasons = []

    above_vwap = price > vwap
    ema_bull = ema9 > ema20
    reclaim = prev["Close"] <= prev["VWAP"] and price > vwap
    vol_ok = vol > vol_ma
    rsi_ok = np.isfinite(rsi) and 40 < rsi < 70

    long_setup = above_vwap and ema_bull and reclaim and vol_ok and rsi_ok

    below_vwap = price < vwap
    ema_bear = ema9 < ema20
    rsi_overbought = np.isfinite(rsi) and rsi > 72
    momentum_fail = below_vwap and ema_bear

    if long_setup:
        action = "BUY"
        reasons.append("Price reclaimed VWAP with rising short-term momentum (EMA9 > EMA20)")
        reasons.append("Volume is above its recent 10-bar average")
        reasons.append(f"RSI is in a healthy range ({rsi:.1f})")
    elif momentum_fail:
        action = "SELL / AVOID LONG"
        reasons.append("Price lost VWAP and the short-term EMAs turned bearish")
    elif rsi_overbought and above_vwap:
        action = "TAKE PROFIT / TIGHTEN STOP"
        reasons.append(f"RSI is elevated ({rsi:.1f}); consider scaling out or trailing")
    elif below_vwap:
        action = "AVOID LONG / WAIT"
        reasons.append("Price is below VWAP, so the current bias is not bullish")
    else:
        action = "WATCH"
        reasons.append("No clean pullback-reclaim setup is present")

    atr = float(latest["ATR"])
    if not np.isfinite(atr):
        atr = price * 0.005

    stop_dist = max(atr * 1.2, price * 0.003)
    stop = price - stop_dist
    target = price + stop_dist * rr_ratio
    return action, reasons, stop, target, stop_dist


# ---------- Main ----------
if not ticker:
    st.warning("Enter a ticker symbol in the sidebar.")
    st.stop()

try:
    with st.spinner("Loading delayed market data…"):
        raw = load_data(ticker, lookback, interval)

    if raw.empty:
        st.error("No data returned. Check the ticker or choose a longer lookback.")
        st.stop()

    df = add_indicators(raw)
    action, reasons, stop, target, stop_dist = get_action(df)

    latest = df.iloc[-1]
    price = float(latest["Close"])
    last_time = df.index[-1]

    if action == "BUY":
        st.success(f"### ACTION: {action}")
    elif "SELL" in action or "AVOID" in action:
        st.error(f"### ACTION: {action}")
    else:
        st.info(f"### ACTION: {action}")

    timestamp_label = last_time.strftime("%Y-%m-%d %H:%M") if hasattr(last_time, "strftime") else str(last_time)
    st.write(f"**Last bar time (delayed):** {timestamp_label}")
    st.write(f"**Latest close (delayed):** ${price:.2f}")

    st.subheader("Why this action?")
    for reason in reasons:
        st.write(f"- {reason}")

    if stop is not None and target is not None:
        risk_dollars = account_size * risk_pct
        shares = int(risk_dollars // stop_dist) if stop_dist > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Last price", f"${price:.2f}")
        col2.metric("Suggested stop", f"${stop:.2f}")
        col3.metric(f"Target ({rr_ratio:.1f}R)", f"${target:.2f}")
        col4.metric("Shares at risk", f"{shares:,}")

        st.caption(
            f"Position size: {shares:,} shares using ${risk_dollars:,.2f} "
            f"({risk_pct * 100:.2f}% of the account) and a ${stop_dist:.2f} stop distance."
        )

    with st.expander("Strategy checklist (long)"):
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        rsi_value = latest["RSI"]
        checks = {
            "Price > VWAP": latest["Close"] > latest["VWAP"],
            "EMA9 > EMA20": latest["EMA9"] > latest["EMA20"],
            "Just reclaimed VWAP": prev["Close"] <= prev["VWAP"] and latest["Close"] > latest["VWAP"],
            "Volume > 10-bar average": latest["Volume"] > latest["Vol_MA"],
            "RSI between 40–70": bool(pd.notna(rsi_value) and 40 < rsi_value < 70),
        }
        for name, ok in checks.items():
            st.write(("✅" if ok else "❌") + f"  {name}")

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.72, 0.28],
        vertical_spacing=0.03,
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(x=df.index, y=df["VWAP"], name="VWAP", line=dict(color="blue", width=1.5)),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df["EMA9"], name="EMA9", line=dict(width=1)),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df["EMA20"], name="EMA20", line=dict(width=1)),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker_color="rgba(100,100,100,0.4)",
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=650,
        title=f"{ticker} | {interval} | Last update: {timestamp_label}",
        margin=dict(l=10, r=10, t=40, b=10),
    )
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    st.plotly_chart(fig, use_container_width=True)

    if auto_refresh:
        st.caption("Auto-refreshing in 60 seconds…")
        time.sleep(60)
        st.rerun()

except Exception as exc:
    st.error(f"Error loading or processing data: {exc}")

st.markdown("---")
st.warning("""
**Critical warnings**
- Yahoo Finance data is delayed and may be unavailable or inaccurate.
- This is a mechanical educational strategy, not a recommendation or guarantee.
- Use a hard stop and never risk money you cannot afford to lose.
- Paper trade first. Many retail day traders lose money over time.
""")
