import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date
import time
import uuid
import io

# ---------- Page Setup ----------
st.set_page_config(
    page_title="Simple Day Trade Helper",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme CSS
st.markdown("""
<style>
    .stApp { background-color: #131722; color: #d1d4dc; }
    section[data-testid="stSidebar"] {
        background-color: #1e222d;
        border-right: 1px solid #2a2e39;
    }
    h1, h2, h3, h4 { color: #d1d4dc !important; }
    .action-banner {
        font-size: 1.9rem;
        font-weight: 700;
        text-align: center;
        padding: 14px;
        border-radius: 8px;
        margin: 8px 0 14px 0;
    }
    .buy   { background: #089981; color: white; }
    .short { background: #f23645; color: white; }
    .watch { background: #2962ff; color: white; }
    div[data-testid="stMetric"] {
        background-color: #1e222d;
        border: 1px solid #2a2e39;
        border-radius: 6px;
        padding: 10px;
    }
    div[data-testid="stMetric"] label { color: #787b86 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #d1d4dc !important;
        font-size: 1.25rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Remember settings ----------
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["SPY", "QQQ", "AAPL", "TSLA", "NVDA"]
if "active_ticker" not in st.session_state:
    st.session_state.active_ticker = "SPY"
if "paper_trades" not in st.session_state:
    st.session_state.paper_trades = []
if "account_size" not in st.session_state:
    st.session_state.account_size = 25000.0
if "daily_loss_limit" not in st.session_state:
    st.session_state.daily_loss_limit = 300.0

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("### 1. Choose a Stock")
    new_sym = st.text_input("Add a stock symbol", placeholder="Example: META").upper().strip()
    if st.button("Add to list") and new_sym and new_sym not in st.session_state.watchlist:
        st.session_state.watchlist.append(new_sym)

    st.write("Click a stock below:")
    for sym in st.session_state.watchlist:
        if st.button(sym, key=f"btn_{sym}", use_container_width=True):
            st.session_state.active_ticker = sym

    st.markdown("---")
    st.markdown("### 2. Your Settings")

    interval = st.selectbox(
        "Chart speed",
        ["1m", "5m", "15m"],
        index=1,
        help="1m = updates faster (but still delayed). 5m is usually the best balance."
    )

    st.session_state.account_size = st.number_input(
        "How much money is in your account? ($)",
        min_value=1000.0,
        value=st.session_state.account_size,
        step=1000.0,
        help="This is only used to suggest how many shares to buy in practice mode."
    )

    risk_pct = st.slider(
        "How much are you willing to risk on one trade? (%)",
        0.25, 1.0, 0.5, 0.25,
        help="Most beginners should stay at 0.5% or less. This protects you from big losses."
    ) / 100

    rr_ratio = st.slider(
        "How much profit do you want vs risk?",
        1.2, 3.0, 1.8, 0.1,
        help="1.8 means: for every $1 you risk, you aim to make $1.80."
    )

    st.session_state.daily_loss_limit = st.number_input(
        "Max loss you allow today ($)",
        min_value=50.0,
        value=st.session_state.daily_loss_limit,
        step=50.0,
        help="If your practice losses reach this number, stop trading for the day."
    )

    refresh_sec = st.slider("Auto-refresh every (seconds)", 8, 60, 12)
    auto = st.checkbox("Turn on auto-refresh", value=True)

    st.markdown("---")
    st.caption("This uses free delayed data. It is NOT live. For learning only.")

# ---------- Data functions ----------
@st.cache_data(ttl=20, show_spinner=False)
def get_data(ticker, interval):
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

def get_signal(df):
    if len(df) < 20:
        return "WAIT", ["Not enough data yet"], None, None, None, 0, "None"

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    price = float(latest["Close"])
    vwap = float(latest["VWAP"])
    ema9 = float(latest["EMA9"])
    ema20 = float(latest["EMA20"])
    rsi = float(latest["RSI"])
    vol = float(latest["Volume"])
    vol_ma = float(latest["Vol_MA"]) if pd.notna(latest["Vol_MA"]) else vol

    # Conditions
    above_vwap = price > vwap
    below_vwap = price < vwap
    ema_up = ema9 > ema20
    ema_down = ema9 < ema20
    reclaim_up = float(prev["Close"]) <= float(prev["VWAP"]) and price > vwap
    reclaim_down = float(prev["Close"]) >= float(prev["VWAP"]) and price < vwap
    vol_ok = vol > vol_ma * 0.9
    rsi_ok = 38 < rsi < 72

    long_score = sum([above_vwap, ema_up, reclaim_up, vol_ok, rsi_ok])
    short_score = sum([below_vwap, ema_down, reclaim_down, vol_ok, rsi_ok])

    # Decision
    if long_score == 5:
        action = "BUY"
        reasons = [
            "Price just moved back above the average price (VWAP)",
            "Short-term trend is going up",
            "Volume looks healthy"
        ]
        side = "LONG"
        score = long_score
    elif short_score == 5:
        action = "SHORT"
        reasons = [
            "Price just moved back below the average price (VWAP)",
            "Short-term trend is going down",
            "Volume looks healthy"
        ]
        side = "SHORT"
        score = short_score
    elif rsi > 74 and above_vwap:
        action = "TAKE PROFIT"
        reasons = ["The stock has risen a lot recently (RSI is high)", "Consider selling some or moving your stop closer"]
        side = "None"
        score = 0
    elif below_vwap and ema_down:
        action = "AVOID BUYING"
        reasons = ["Price is below average and trend is down", "Better to wait"]
        side = "None"
        score = 0
    else:
        action = "WAIT"
        reasons = ["No clear setup right now", "Patience is part of trading"]
        side = "None"
        score = max(long_score, short_score)

    # Stop & Target
    atr = float(latest["ATR"]) if pd.notna(latest["ATR"]) else price * 0.004
    stop_dist = max(atr * 1.15, price * 0.0028)

    if side == "LONG":
        stop = price - stop_dist
        target = price + stop_dist * rr_ratio
    elif side == "SHORT":
        stop = price + stop_dist
        target = price - stop_dist * rr_ratio
    else:
        stop = target = stop_dist = None

    return action, reasons, stop, target, stop_dist, score, side

def get_higher_tf_bias(ticker):
    """Simple 15-minute bias"""
    try:
        df = get_data(ticker, "15m")
        if len(df) < 25:
            return "Not enough data"
        df = add_indicators(df)
        latest = df.iloc[-1]
        if float(latest["EMA9"]) > float(latest["EMA20"]):
            return "Upward (bullish)"
        else:
            return "Downward (bearish)"
    except:
        return "Unavailable"

# ---------- MAIN SCREEN ----------
ticker = st.session_state.active_ticker

try:
    df_raw = get_data(ticker, interval)
    if df_raw.empty:
        st.error("Could not load data. Check the stock symbol.")
        st.stop()

    df = add_indicators(df_raw)
    action, reasons, stop, target, stop_dist, score, side = get_signal(df)

    latest = df.iloc[-1]
    price = float(latest["Close"])
    last_time = df.index[-1]

    try:
        age_min = int((datetime.now(last_time.tzinfo) - last_time).total_seconds() // 60)
    except:
        age_min = "?"

    # Daily paper P&L
    today = date.today().isoformat()
    today_pnl = sum(
        t["pnl"] for t in st.session_state.paper_trades
        if t.get("pnl") is not None and t.get("time", "").startswith(today)
    )
    limit_hit = today_pnl <= -st.session_state.daily_loss_limit

    # Header
    st.markdown(f"## {ticker}")
    st.caption(f"Chart: {interval}  •  Data is delayed (about {age_min} min old)")

    # Big action
    css = "buy" if action == "BUY" else ("short" if action == "SHORT" else "watch")
    st.markdown(f'<div class="action-banner {css}">{action}</div>', unsafe_allow_html=True)

    if limit_hit:
        st.error(f"Daily loss limit reached (${st.session_state.daily_loss_limit:.0f}). Stop trading for today.")

    # Key numbers
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Current Price", f"${price:.2f}", help="The latest price we have (it is delayed).")
    c2.metric("VWAP", f"${float(latest['VWAP']):.2f}",
              help="VWAP = average price of the day. Think of it as the 'fair' price so far today. Above it is usually better for buying.")
    c3.metric("RSI", f"{float(latest['RSI']):.0f}",
              help="RSI shows if the stock moved too far too fast. Below 30 = maybe too low. Above 70 = maybe too high.")
    c4.metric("Signal Strength", f"{score}/5",
              help="How many of the 5 rules are currently true. 5/5 is the strongest setup.")
    c5.metric("15-min Bias", get_higher_tf_bias(ticker),
              help="A quick look at the bigger picture on the 15-minute chart.")

    # Why + Levels
    left, right = st.columns(2)

    with left:
        st.markdown("#### Why this signal?")
        for r in reasons:
            st.markdown(f"- {r}")

        with st.expander("What do these words mean?"):
            st.markdown("""
            - **VWAP**: The average price of all shares traded today.  
            - **EMA9 / EMA20**: Short-term average prices. When the faster one is above the slower one, the short-term trend is up.  
            - **RSI**: A number from 0–100 that shows if the stock is overheated or washed out.  
            - **Reclaim**: Price was below VWAP and just crossed back above it (or the opposite for shorting).  
            - **Stop**: The price where you admit the trade is wrong and get out to limit the loss.  
            - **Target**: The price where you plan to take profit.
            """)

    with right:
        if stop and target and stop_dist:
            st.markdown("#### Suggested Plan")
            st.markdown(f"**Entry zone**: around `${price:.2f}`")
            st.markdown(f"**Stop loss**: `${stop:.2f}`")
            st.markdown(f"**Target**: `${target:.2f}`")

            risk_dollars = st.session_state.account_size * risk_pct
            shares = int(risk_dollars / stop_dist) if stop_dist > 0 else 0
            st.markdown(f"**Suggested shares**: `{shares}`")
            st.caption(f"(Risking ${risk_dollars:.0f} which is {risk_pct*100:.1f}% of your account)")

            if not limit_hit and side in ["LONG", "SHORT"]:
                if st.button(f"Practice this {side} trade", type="primary", use_container_width=True):
                    trade = {
                        "id": str(uuid.uuid4())[:8],
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "ticker": ticker,
                        "side": side,
                        "entry": round(price, 2),
                        "stop": round(stop, 2),
                        "target": round(target, 2),
                        "shares": shares,
                        "status": "OPEN",
                        "exit": None,
                        "pnl": None,
                        "notes": "From signal"
                    }
                    st.session_state.paper_trades.append(trade)
                    st.success("Added to your practice log")

    # Chart
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.78, 0.22], vertical_spacing=0.02)

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="Price",
        increasing_line_color="#089981", decreasing_line_color="#f23645",
        increasing_fillcolor="#089981", decreasing_fillcolor="#f23645"
    ), row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["VWAP"], name="VWAP", line=dict(color="#2962ff", width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA9"], name="EMA 9", line=dict(color="#ff9800", width=1.4)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA20"], name="EMA 20", line=dict(color="#ab47bc", width=1.4)), row=1, col=1)

    colors = ["#089981" if c >= o else "#f23645" for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color=colors, opacity=0.5), row=2, col=1)

    fig.update_layout(
        height=500,
        paper_bgcolor="#131722",
        plot_bgcolor="#131722",
        font=dict(color="#d1d4dc"),
        margin=dict(l=0, r=10, t=10, b=0),
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(orientation="h", y=1.02, x=0, bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="#2a2e39"),
        yaxis=dict(gridcolor="#2a2e39", side="right"),
        yaxis2=dict(gridcolor="#2a2e39", side="right"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ---------- PAPER TRADE LOG ----------
    st.markdown("---")
    st.markdown("### Practice Trade Log")

    # Today's P&L summary
    st.info(f"Today's practice P&L: **${today_pnl:+.2f}**  •  Daily limit: ${st.session_state.daily_loss_limit:.0f}")

    open_trades = [t for t in st.session_state.paper_trades if t["status"] == "OPEN"]
    closed_trades = [t for t in st.session_state.paper_trades if t["status"] == "CLOSED"]

    if open_trades:
        st.markdown("#### Open Practice Trades")
        for t in open_trades:
            cols = st.columns([1.3, 0.8, 0.8, 0.8, 1.2, 1])
            cols[0].write(f"**{t['ticker']}** {t['side']}")
            cols[1].write(f"In at ${t['entry']}")
            cols[2].write(f"Stop ${t['stop']}")
            cols[3].write(f"{t['shares']} shares")
            exit_px = cols[4].number_input("Exit price", value=float(price), key=f"ex_{t['id']}", format="%.2f")
            if cols[5].button("Close trade", key=f"cl_{t['id']}"):
                if t["side"] == "LONG":
                    pnl = (exit_px - t["entry"]) * t["shares"]
                else:
                    pnl = (t["entry"] - exit_px) * t["shares"]
                t["exit"] = exit_px
                t["pnl"] = round(pnl, 2)
                t["status"] = "CLOSED"
                st.rerun()

    if closed_trades:
        st.markdown("#### Closed Practice Trades")
        cdf = pd.DataFrame(closed_trades)
        st.dataframe(cdf[["time", "ticker", "side", "entry", "exit", "shares", "pnl", "notes"]],
                     use_container_width=True, hide_index=True)

        total_pnl = sum(t["pnl"] for t in closed_trades if t["pnl"] is not None)
        wins = len([t for t in closed_trades if t["pnl"] and t["pnl"] > 0])
        st.write(f"Total practice P&L: **${total_pnl:+.2f}**  •  Wins: {wins}/{len(closed_trades)}")

        # Export button
        csv_buffer = io.StringIO()
        cdf.to_csv(csv_buffer, index=False)
        st.download_button(
            "Download trades as CSV",
            csv_buffer.getvalue(),
            file_name=f"paper_trades_{date.today()}.csv",
            mime="text/csv"
        )

    if st.button("Clear all practice trades"):
        st.session_state.paper_trades = []
        st.rerun()

    if auto:
        time.sleep(refresh_sec)
        st.rerun()

except Exception as e:
    st.error(f"Something went wrong: {e}")

st.markdown("---")
st.warning("""
**Please read this**  
This tool uses free delayed data and is only for learning and practice.  
It is **not** real-time and it does **not** guarantee profits.  
Most people who day trade lose money.  
Always use a stop loss and never risk money you cannot afford to lose.
""")
