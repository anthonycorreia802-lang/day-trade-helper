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

# Modern Cyber-Terminal Dark Theme CSS
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #07090e 0%, #0b0e14 100%); color: #e2e8f0; }
    
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
    st.markdown("### 🔍 Stock Watchlist")
    new_sym = st.text_input("Add Symbol", placeholder="e.g. META, AMD").upper().strip()
    if st.button("➕ Add to Watchlist") and new_sym and new_sym not in st.session_state.watchlist:
        st.session_state.watchlist.append(new_sym)

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

    interval = st.selectbox(
        "Timeframe / Speed",
        ["1m", "5m", "15m"],
        index=0
    )

    include_247 = st.checkbox(
        "Include Pre/Post-Market",
        value=True,
        help="Pulls 4:00 AM – 8:00 PM EST extended session data."
    )

    st.session_state.account_size = st.number_input(
        "Account Size ($)",
        min_value=1000.0,
        value=st.session_state.account_size,
        step=1000.0
    )

    risk_pct = st.slider(
        "Risk Per Trade (%)",
        0.25, 1.0, 0.5, 0.25
    ) / 100

    rr_ratio = st.slider(
        "Reward-to-Risk Target",
        1.2, 3.0, 1.8, 0.1
    )

    st.session_state.daily_loss_limit = st.number_input(
        "Max Daily Loss ($)",
        min_value=50.0,
        value=st.session_state.daily_loss_limit,
        step=50.0
    )

    refresh_sec = st.slider("Auto-Refresh Rate (sec)", 8, 60, 8)
    auto = st.checkbox("Enable Live Auto-Refresh", value=True)

    st.markdown("---")
    st.caption("Powered by Yahoo Finance extended feed.")

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
    period = "2d" if interval == "1m" else "5d"
    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        prepost=prepost,
        progress=False,
        auto_adjust=True
    )
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

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
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else latest

    price = live_price if live_price else float(latest["Close"])
    vwap = float(latest["VWAP"])
    ema9 = float(latest["EMA9"])
    ema20 = float(latest["EMA20"])
    rsi = float(latest["RSI"])
    atr = float(latest["ATR"])
    vol = float(latest["Volume"])
    vol_ma = float(latest["Vol_MA"]) if pd.notna(latest["Vol_MA"]) and latest["Vol_MA"] > 0 else max(vol, 1.0)

    recent = df.tail(45)
    swing_high = float(recent["High"].max())
    swing_low = float(recent["Low"].min())

    above_vwap = price > vwap
    below_vwap = price < vwap
    ema_up = ema9 > ema20
    ema_down = ema9 < ema20
    reclaim_up = float(prev["Close"]) <= float(prev["VWAP"]) and price > vwap
    reclaim_down = float(prev["Close"]) >= float(prev["VWAP"]) and price < vwap
    vol_ok = vol >= vol_ma * 0.85
    rsi_ok = 35 < rsi < 72

    long_score = sum([above_vwap, ema_up, reclaim_up or (price > ema9), vol_ok, rsi_ok])
    short_score = sum([below_vwap, ema_down, reclaim_down or (price < ema9), vol_ok, rsi_ok])

    stop_dist = max(atr * 1.25, price * 0.0025)

    if above_vwap and ema_up:
        support_anchor = max(vwap, min(ema9, price))
        ideal_buy = round(min(price, support_anchor + atr * 0.15), 2)
        stop = round(ideal_buy - stop_dist, 2)
        ideal_sell = round(max(ideal_buy + stop_dist * rr_ratio, swing_high), 2)
    elif below_vwap and ema_down:
        ideal_buy = round(max(swing_low, price - atr * 1.5), 2)
        stop = round(ideal_buy - stop_dist, 2)
        ideal_sell = round(min(vwap, ema20), 2)
    else:
        ideal_buy = round(min(price, vwap - atr * 0.25), 2)
        stop = round(ideal_buy - stop_dist, 2)
        ideal_sell = round(max(price + stop_dist * rr_ratio, vwap + atr * 1.5), 2)

    mins_per_bar = {"1m": 1, "5m": 5, "15m": 15}.get(interval, 1)
    bars_in_hour = 60 / mins_per_bar
    hourly_expected_move = atr * np.sqrt(bars_in_hour) * 0.55

    bias_mult = 1.0 if (above_vwap and ema_up) else (-1.0 if (below_vwap and ema_down) else 0.35)
    hourly_target = round(price + (hourly_expected_move * bias_mult), 2)

    if daily_stats:
        d_atr = daily_stats["daily_atr"]
        anchor = daily_stats["today_open"]
        if bias_mult >= 0:
            daily_target = round(max(price + d_atr * 0.35, anchor + d_atr * 0.75), 2)
        else:
            daily_target = round(min(price - d_atr * 0.35, anchor - d_atr * 0.75), 2)
        daily_range = (round(anchor - d_atr * 0.75, 2), round(anchor + d_atr * 0.75, 2))
    else:
        daily_target = round(price + (hourly_expected_move * 2.5 * bias_mult), 2)
        daily_range = (round(swing_low, 2), round(swing_high, 2))

    if long_score == 5 and price <= ideal_buy + atr * 0.35:
        action = "🚀 BUY NOW (STRONG SETUP)"
        reasons = [
            f"Price (${price:.2f}) is right inside your ideal buy zone (${ideal_buy:.2f})",
            "Trading above VWAP with bullish EMA 9 > EMA 20 alignment",
            f"Targeting ${ideal_sell:.2f} with stop at ${stop:.2f}"
        ]
        side = "LONG"
        score = long_score
    elif short_score == 5:
        action = "🔻 SHORT / SELL NOW"
        reasons = [
            "Price broke below VWAP with bearish EMA alignment",
            "Downward momentum confirmed",
            f"Downside target ${ideal_buy:.2f}"
        ]
        side = "SHORT"
        score = short_score
    elif price >= ideal_sell * 0.999 or rsi > 74:
        action = "💎 TAKE PROFIT / SELL"
        reasons = [
            f"Price reached/exceeded Ideal Sell target (${ideal_sell:.2f}) or RSI is overheated ({rsi:.0f})",
            "Lock in gains rather than chasing"
        ]
        side = "None"
        score = max(long_score, short_score)
    elif above_vwap and ema_up:
        action = f"⏳ WAIT FOR PULLBACK TO ${ideal_buy:.2f}"
        reasons = [
            "Trend is bullish, but current price is slightly above ideal entry",
            f"Place limit buy near ${ideal_buy:.2f} (VWAP / EMA9 support)"
        ]
        side = "LONG"
        score = long_score
    else:
        action = "🛡️ WAIT (NO CLEAR SETUP)"
        reasons = [
            "Price is below VWAP or consolidating without clear momentum",
            f"Watch for a reclaim above VWAP (${vwap:.2f}) or bounce near ${ideal_buy:.2f}"
        ]
        side = "None"
        score = max(long_score, short_score)

    return {
        "action": action,
        "reasons": reasons,
        "side": side,
        "score": score,
        "price": price,
        "vwap": vwap,
        "rsi": rsi,
        "ideal_buy": ideal_buy,
        "ideal_sell": ideal_sell,
        "stop": stop,
        "stop_dist": abs(ideal_buy - stop),
        "hourly_target": hourly_target,
        "daily_target": daily_target,
        "daily_range": daily_range,
    }

def get_higher_tf_bias(ticker, prepost):
    try:
        df = get_intraday_data(ticker, "15m", prepost=prepost)
        if len(df) < 25:
            return "Not enough data"
        df = add_indicators(df)
        latest = df.iloc[-1]
        return "🟢 Bullish (Up)" if float(latest["EMA9"]) > float(latest["EMA20"]) else "🔴 Bearish (Down)"
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

        today = date.today().isoformat()
        today_pnl = sum(
            t["pnl"] for t in st.session_state.paper_trades
            if t.get("pnl") is not None and t.get("time", "").startswith(today)
        )
        limit_hit = today_pnl <= -st.session_state.daily_loss_limit

        st.markdown(f"## ⚡ {ticker} — ${price:.2f}")
        st.caption(
            f"Session: **{session_label}**  •  EST Time: {now_est.strftime('%I:%M:%S %p')}  •  "
            f"Last Candle: {age_str}  •  Refresh: {refresh_sec}s"
        )

        css = "buy" if "BUY" in sig["action"] else ("short" if "SHORT" in sig["action"] or "SELL" in sig["action"] else "watch")
        st.markdown(f'<div class="action-banner {css}">{sig["action"]}</div>', unsafe_allow_html=True)

        if limit_hit:
            st.error(f"⚠️ Daily loss limit reached (${st.session_state.daily_loss_limit:.0f}). Stop trading for today.")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Current Price", f"${price:.2f}")
        c2.metric("VWAP (Fair Value)", f"${sig['vwap']:.2f}")
        c3.metric("RSI (Momentum)", f"{sig['rsi']:.0f}")
        c4.metric("Setup Score", f"{sig['score']}/5")
        c5.metric("15-min Trend", get_higher_tf_bias(ticker, include_247))

        if dash_mode == "Advanced (Pro)":
            st.markdown("##### 🔬 Advanced Pro Telemetry")
            ac1, ac2, ac3, ac4 = st.columns(4)
            ac1.metric("ATR (Volatility)", f"${df.iloc[-1]['ATR']:.2f}")
            ac2.metric("Volume vs MA", f"{df.iloc[-1]['Volume'] / max(df.iloc[-1]['Volume_MA'], 1):.2f}x")
            ac3.metric("EMA 9 / EMA 20 Spread", f"${df.iloc[-1]['EMA9'] - df.iloc[-1]['EMA20']:+.2f}")
            ac4.metric("Session High / Low", f"${df.tail(45)['High'].max():.2f} / ${df.tail(45)['Low'].min():.2f}")

        st.markdown("#### 🎯 Live Price Targets & Trade Zones")
        t1, t2, t3, t4 = st.columns(4)
        buy_delta = ((sig["ideal_buy"] - price) / price) * 100
        sell_delta = ((sig["ideal_sell"] - price) / price) * 100
        hr_delta = ((sig["hourly_target"] - price) / price) * 100
        day_delta = ((sig["daily_target"] - price) / price) * 100

        t1.metric("Ideal Buy Price", f"${sig['ideal_buy']:.2f}", f"{buy_delta:+.2f}% from now")
        t2.metric("Ideal Sell Price", f"${sig['ideal_sell']:.2f}", f"{sell_delta:+.2f}% from now")
        t3.metric("Hourly Target (1H)", f"${sig['hourly_target']:.2f}", f"{hr_delta:+.2f}% projected")
        t4.metric(
            "Daily Target (EOD)",
            f"${sig['daily_target']:.2f}",
            f"{day_delta:+.2f}% (Range: ${sig['daily_range'][0]}–${sig['daily_range'][1]})"
        )

        left, right = st.columns(2)
        with left:
            st.markdown("#### 💡 Why this setup?")
            for r in sig["reasons"]:
                st.markdown(f"- {r}")

            with st.expander("📖 How are Ideal Buy, Sell & Targets calculated?"):
                st.markdown("""
- **Ideal Buy Price**: Anchored to VWAP / EMA 9 pullback support in an uptrend, or lower volatility support in a downtrend.
- **Ideal Sell Price**: Anchored to your Reward-to-Risk ratio above the Ideal Buy.
- **Hourly Target**: Projects a 1-hour volatility envelope weighted by current trend direction.
- **Daily Target**: Uses the 14-day Daily ATR anchored to today's open.
                """)

        with right:
            st.markdown("#### ⚡ Quick Trade Execution")
            st.markdown(f"**Ideal Entry**: `${sig['ideal_buy']:.2f}`  |  **Stop Loss**: `${sig['stop']:.2f}`  |  **Take Profit**: `${sig['ideal_sell']:.2f}`")

            risk_dollars = st.session_state.account_size * risk_pct
            stop_dist = max(sig["stop_dist"], 0.01)
            shares = int(risk_dollars / stop_dist)
            st.markdown(f"**Position Size**: `{shares}` shares (Risking `${risk_dollars:.0f}` = `{risk_pct*100:.2f}%`)")

            already_open = any(
                t["ticker"] == ticker and t["status"] == "OPEN"
                for t in st.session_state.paper_trades
            )

            if not limit_hit and shares > 0:
                b1, b2 = st.columns(2)
                if already_open:
                    st.info(f"You already have an open paper trade on {ticker}.")
                else:
                    if b1.button(f"🚀 Paper BUY @ ${price:.2f}", type="primary", use_container_width=True):
                        st.session_state.paper_trades.append({
                            "id": str(uuid.uuid4())[:8],
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
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

                    if b2.button(f"🔻 Paper SHORT @ ${price:.2f}", use_container_width=True):
                        short_stop = round(price + stop_dist, 2)
                        short_target = round(price - stop_dist * rr_ratio, 2)
                        st.session_state.paper_trades.append({
                            "id": str(uuid.uuid4())[:8],
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
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
            height=520,
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
                    st.session_state.paper_trades.append({
                        "id": str(uuid.uuid4())[:8],
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
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

st.markdown("---")
st.warning("""
**⚠️ Educational Disclaimer**  
This tool uses free Yahoo Finance data and is intended solely for paper trading, journaling practice, and educational learning.  
It does not guarantee financial success. Always protect your capital with stop losses.
""")
