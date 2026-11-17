"""
Beginner-friendly Day Trading Dashboard
Run locally: streamlit run app.py
Deploy: upload this file as app.py to Streamlit Community Cloud and add requirements.txt.
Educational/paper-trading only. Yahoo Finance data may be delayed or unavailable.
"""
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date
from zoneinfo import ZoneInfo
import sqlite3
import os
import math

st.set_page_config(page_title="Simple Trading Dashboard", page_icon="📈", layout="wide")

# ---------- Beginner-friendly styling ----------
st.markdown("""
<style>
.stApp {background:#0b1220;color:#e5e7eb}
section[data-testid="stSidebar"] {background:#111827}
div[data-testid="stMetric"] {background:#172235;border:1px solid #29364b;padding:12px;border-radius:10px}
.tip {background:#172235;border-left:4px solid #38bdf8;padding:12px;border-radius:6px}
.signal {padding:14px;border-radius:10px;text-align:center;font-size:24px;font-weight:800}
</style>
""", unsafe_allow_html=True)

DB_PATH = os.environ.get("TRADING_DB_PATH", "trading_journal.db")
TIMEFRAMES = {
    "1 minute": "1m", "2 minutes": "2m", "5 minutes": "5m",
    "15 minutes": "15m", "30 minutes": "30m", "1 hour": "60m"
}
PERIODS = {"1m": "2d", "2m": "60d", "5m": "60d", "15m": "60d", "30m": "60d", "60m": "730d"}
SCAN_UNIVERSE = [
    "SPY","QQQ","IWM","DIA","AAPL","MSFT","NVDA","AMZN","META","GOOGL",
    "TSLA","AMD","NFLX","JPM","XOM","COST","AVGO","PLTR","UBER","DIS"
]

def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT, ticker TEXT, side TEXT,
        entry REAL, exit REAL, stop REAL, target REAL, shares INTEGER,
        status TEXT, pnl REAL, notes TEXT)""")
    conn.commit()
    return conn

def add_trade(ticker, side, entry, stop, target, shares, notes="Paper trade"):
    with db_connect() as c:
        c.execute("INSERT INTO trades(created,ticker,side,entry,stop,target,shares,status,notes) VALUES(?,?,?,?,?,?,?,'OPEN',?)",
                  (datetime.now().isoformat(timespec="minutes"),ticker,side,entry,stop,target,shares,notes))

def close_trade(trade_id, exit_price):
    with db_connect() as c:
        row = c.execute("SELECT side,entry,shares FROM trades WHERE id=? AND status='OPEN'",(trade_id,)).fetchone()
        if not row: return
        side, entry, shares = row
        pnl = (exit_price-entry)*shares if side=="LONG" else (entry-exit_price)*shares
        c.execute("UPDATE trades SET exit=?,pnl=?,status='CLOSED' WHERE id=?",(exit_price,round(pnl,2),trade_id))

def get_trades(status=None):
    with db_connect() as c:
        q = "SELECT * FROM trades"
        params = ()
        if status:
            q += " WHERE status=?"; params=(status,)
        q += " ORDER BY id DESC"
        return pd.read_sql_query(q,c,params=params)

@st.cache_data(ttl=30, show_spinner=False)
def get_bars(symbol, interval):
    period = PERIODS[interval]
    df = yf.download(symbol, period=period, interval=interval, auto_adjust=True,
                     prepost=False, progress=False, threads=False)
    if df is None or df.empty: return pd.DataFrame()
    if isinstance(df.columns,pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    required = ["Open","High","Low","Close","Volume"]
    if not set(required).issubset(df.columns): return pd.DataFrame()
    return df[required].dropna()

@st.cache_data(ttl=60, show_spinner=False)
def search_symbols(query):
    if len(query.strip()) < 1: return []
    try:
        results = yf.Search(query.strip(), max_results=12, news_count=0).quotes
        out=[]
        for item in results:
            symbol=item.get("symbol")
            if symbol and item.get("quoteType") in ("EQUITY","ETF","MUTUALFUND","INDEX"):
                out.append({"symbol":symbol,"name":item.get("shortname") or item.get("longname") or symbol,
                            "type":item.get("quoteType","")})
        return out
    except Exception:
        return []

def indicators(df):
    d=df.copy()
    typical=(d.High+d.Low+d.Close)/3
    d["VWAP"]=(typical*d.Volume).groupby(d.index.date).cumsum()/d.Volume.groupby(d.index.date).cumsum().replace(0,np.nan)
    d["VWAP"]=d["VWAP"].fillna(d.Close)
    d["EMA9"]=d.Close.ewm(span=9,adjust=False).mean()
    d["EMA20"]=d.Close.ewm(span=20,adjust=False).mean()
    delta=d.Close.diff()
    gain=delta.clip(lower=0).ewm(alpha=1/14,min_periods=5,adjust=False).mean()
    loss=(-delta.clip(upper=0)).ewm(alpha=1/14,min_periods=5,adjust=False).mean()
    rs=gain/loss.replace(0,np.nan)
    d["RSI"]=(100-100/(1+rs)).fillna(50)
    tr=pd.concat([d.High-d.Low,(d.High-d.Close.shift()).abs(),(d.Low-d.Close.shift()).abs()],axis=1).max(axis=1)
    d["ATR"]=tr.ewm(alpha=1/14,min_periods=5,adjust=False).mean().fillna(d.Close*0.003)
    d["VOL_MA"]=d.Volume.rolling(8,min_periods=1).mean()
    return d

def analyze(d, risk_reward=2.0):
    x=d.iloc[-1]
    price=float(x.Close); atr=max(float(x.ATR),price*0.001)
    bull=price>float(x.VWAP) and x.EMA9>x.EMA20 and 40<float(x.RSI)<72
    bear=price<float(x.VWAP) and x.EMA9<x.EMA20 and 28<float(x.RSI)<60
    score=int(price>x.VWAP)+int(x.EMA9>x.EMA20)+int(x.RSI>50)+int(x.Volume>=x.VOL_MA)+int(price>x.EMA9)
    if bull: action="BULLISH SETUP"
    elif bear: action="BEARISH SETUP"
    else: action="WAIT — NO CLEAR SETUP"
    stop_dist=max(atr*1.25,price*0.002)
    long_stop=price-stop_dist; long_target=price+stop_dist*risk_reward
    short_stop=price+stop_dist; short_target=price-stop_dist*risk_reward
    return {"price":price,"action":action,"score":score,"vwap":float(x.VWAP),"rsi":float(x.RSI),
            "ema9":float(x.EMA9),"ema20":float(x.EMA20),"atr":atr,
            "long_stop":long_stop,"long_target":long_target,
            "short_stop":short_stop,"short_target":short_target}

@st.cache_data(ttl=180, show_spinner=False)
def scan_market(interval):
    rows=[]
    for symbol in SCAN_UNIVERSE:
        try:
            raw=get_bars(symbol,interval)
            if len(raw)<25: continue
            a=analyze(indicators(raw))
            direction="Bullish" if a["action"].startswith("BULLISH") else ("Bearish" if a["action"].startswith("BEARISH") else "Neutral")
            rows.append({"Ticker":symbol,"Direction":direction,"Score":a["score"],"Price":a["price"],
                         "RSI":a["rsi"],"VWAP":a["vwap"]})
        except Exception:
            continue
    if not rows: return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["Score","Ticker"],ascending=[False,True])

# ---------- Sidebar: keep the beginner path simple ----------
with st.sidebar:
    st.title("📈 Trading Dashboard")
    mode=st.radio("Experience",["Beginner","Advanced"],index=0,
                  help="Beginner shows only the essentials. Advanced adds indicator details.")
    st.caption("Start with Beginner. You can switch any time.")
    timeframe_label=st.selectbox("Chart timeframe",list(TIMEFRAMES),index=3)
    interval=TIMEFRAMES[timeframe_label]
    trend_label=st.selectbox("Trend confirmation timeframe",list(TIMEFRAMES),index=5)
    trend_interval=TIMEFRAMES[trend_label]
    st.caption("The chart and trend confirmation timeframes are independent.")
    risk_pct=st.slider("Risk per paper trade (%)",0.1,2.0,0.5,0.1)/100
    account=st.number_input("Paper account size ($)",min_value=100.0,value=10000.0,step=500.0)
    rr=st.slider("Reward / risk target",1.0,4.0,2.0,0.25)
    if st.button("🔄 Refresh market data",use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.title("📈 Simple Day-Trading Dashboard")
st.caption("Beginner-friendly market view · Educational use and paper trading only")

# Search: query-based symbol suggestions with selectable autofill
if "selected_symbol" not in st.session_state: st.session_state.selected_symbol="SPY"
if "watchlist" not in st.session_state: st.session_state.watchlist=["SPY","QQQ","AAPL","MSFT","NVDA"]
st.subheader("🔎 Find a stock")
search=st.text_input("Type a company name or ticker",placeholder="Try Apple or AAPL",label_visibility="collapsed")
suggestions=search_symbols(search) if search else []
if suggestions:
    options=[f'{x["symbol"]} — {x["name"]} ({x["type"]})' for x in suggestions]
    chosen=st.selectbox("Matching stocks and ETFs",options,key="search_autofill")
    c1,c2=st.columns([1,4])
    with c1:
        if st.button("Use this stock",type="primary"):
            st.session_state.selected_symbol=suggestions[options.index(chosen)]["symbol"]
            st.rerun()
    with c2:
        if st.button("Add selected to watchlist"):
            sym=suggestions[options.index(chosen)]["symbol"]
            if sym not in st.session_state.watchlist: st.session_state.watchlist.append(sym)
            st.success(f"{sym} added to your watchlist.")
elif search:
    st.info("No matching symbols found yet. Check spelling or try the ticker.")

# Watchlist kept separate from the scanner recommendations
with st.expander("⭐ My watchlist",expanded=True):
    w1,w2=st.columns([3,1])
    with w1:
        selected=st.selectbox("Choose from your watchlist",st.session_state.watchlist,
                              index=st.session_state.watchlist.index(st.session_state.selected_symbol)
                              if st.session_state.selected_symbol in st.session_state.watchlist else 0)
        st.session_state.selected_symbol=selected
    with w2:
        remove=st.selectbox("Remove",["—"]+st.session_state.watchlist)
        if st.button("Remove",disabled=remove=="—"):
            st.session_state.watchlist.remove(remove)
            if st.session_state.watchlist: st.session_state.selected_symbol=st.session_state.watchlist[0]
            st.rerun()

ticker=st.session_state.selected_symbol
left,right=st.columns([3,1])
with left: st.subheader(f"{ticker} · {timeframe_label} chart")
with right: st.caption(f"Updated: {datetime.now().strftime('%I:%M:%S %p')}")

try:
    raw=get_bars(ticker,interval)
    if raw.empty or len(raw)<20:
        st.error("Market data is unavailable or there are too few candles. Try another timeframe or ticker.")
        st.stop()
    df=indicators(raw)
    sig=analyze(df,rr)
    trend_raw=get_bars(ticker,trend_interval)
    trend="Not enough data"
    if len(trend_raw)>=20:
        td=indicators(trend_raw).iloc[-1]
        trend="Bullish" if td.EMA9>td.EMA20 else "Bearish"
    st.markdown(f'<div class="signal" style="background:{"#064e3b" if "BULLISH" in sig["action"] else "#7f1d1d" if "BEARISH" in sig["action"] else "#1e3a8a"}">{sig["action"]}</div>',unsafe_allow_html=True)
    m1,m2,m3,m4=st.columns(4)
    m1.metric("Latest price",f"${sig['price']:.2f}")
    m2.metric("Trend confirmation",trend,help=f"EMA 9 vs EMA 20 on {trend_label}")
    m3.metric("Setup score",f'{sig["score"]}/5')
    m4.metric("RSI momentum",f'{sig["rsi"]:.0f}')
    if mode=="Advanced":
        a1,a2,a3=st.columns(3)
        a1.metric("VWAP",f'${sig["vwap"]:.2f}')
        a2.metric("EMA 9 / EMA 20",f'${sig["ema9"]:.2f} / ${sig["ema20"]:.2f}')
        a3.metric("ATR",f'${sig["atr"]:.2f}')

    st.subheader("Price chart")
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,row_heights=[0.78,0.22],vertical_spacing=0.04)
    fig.add_trace(go.Candlestick(x=df.index,open=df.Open,high=df.High,low=df.Low,close=df.Close,name="Price"),row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df.VWAP,name="VWAP"),row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df.EMA9,name="EMA 9"),row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df.EMA20,name="EMA 20"),row=1,col=1)
    fig.add_trace(go.Bar(x=df.index,y=df.Volume,name="Volume"),row=2,col=1)
    fig.update_layout(height=560,template="plotly_dark",xaxis_rangeslider_visible=False,
                      margin=dict(l=10,r=10,t=25,b=10),legend=dict(orientation="h"))
    st.plotly_chart(fig,use_container_width=True)

    st.subheader("🎯 Example trade plan (paper trading)")
    st.caption("These are formula-based reference levels, not predictions or instructions to buy/sell.")
    if sig["action"].startswith("BEARISH"):
        side="SHORT"; entry=sig["price"]; stop=sig["short_stop"]; target=sig["short_target"]
    else:
        side="LONG"; entry=sig["price"]; stop=sig["long_stop"]; target=sig["long_target"]
    risk_cash=account*risk_pct
    per_share=abs(entry-stop)
    shares=max(0,math.floor(risk_cash/per_share)) if per_share>0 else 0
    shares=min(shares,math.floor(account/entry)) if entry>0 else 0
    p1,p2,p3,p4=st.columns(4)
    p1.metric("Example entry",f"${entry:.2f}")
    p2.metric("Stop-loss level",f"${stop:.2f}")
    p3.metric("Target level",f"${target:.2f}")
    p4.metric("Suggested paper shares",str(shares))
    st.caption(f"Approximate planned risk: ${shares*per_share:,.2f} · This sizing is capped by the paper account value.")

    with st.expander("What does this mean? (Beginner guide)",expanded=(mode=="Beginner")):
        st.markdown("""
        - **Bullish:** recent price/trend indicators point upward. It is not a guarantee.
        - **Bearish:** recent price/trend indicators point downward. It is not a guarantee.
        - **Wait:** indicators do not agree clearly; doing nothing is a valid decision.
        - **VWAP:** the session's volume-weighted average price; a reference line, not a prediction.
        - **RSI:** a momentum gauge from 0 to 100. It can stay high or low for a long time.
        - **EMA 9 / EMA 20:** faster and slower trend averages.
        - **Stop loss:** a planned exit level if the trade moves against you. A stop is not guaranteed to fill at that price.
        - **Reward/risk:** target distance compared with stop distance.
        """)

    st.subheader("🧪 Paper trade")
    st.caption("This records a simulated trade only. It does not send an order to a broker.")
    if st.button(f"Record {side} paper trade for {ticker}",type="primary",disabled=shares<1):
        add_trade(ticker,side,entry,stop,target,shares)
        st.success("Paper trade saved to your local journal.")
        st.rerun()
except Exception as exc:
    st.error(f"Could not load this ticker: {exc}")
    st.info("Check the ticker, internet connection, and selected timeframe.")

# ---------- Separate recommendation scanner ----------
st.markdown("---")
st.header("🌟 Market candidates (separate from your watchlist)")
st.write("A small, curated list of actively traded US stocks and ETFs ranked by the same simple technical rules.")
if st.button("Scan candidate list"):
    st.cache_data.clear()
    st.session_state.do_scan=True
if "do_scan" not in st.session_state: st.session_state.do_scan=False
if st.session_state.do_scan:
    with st.spinner("Checking candidate symbols..."):
        candidates=scan_market(interval)
    if candidates.empty:
        st.warning("No scanner results available. Yahoo Finance may be limiting requests; try again later.")
    else:
        bullish=candidates[candidates.Direction=="Bullish"].sort_values("Score",ascending=False)
        bearish=candidates[candidates.Direction=="Bearish"].sort_values("Score",ascending=False)
        st.markdown("**Potential bullish candidates**")
        st.dataframe(bullish.head(10),use_container_width=True,hide_index=True)
        st.markdown("**Potential bearish candidates**")
        st.dataframe(bearish.head(10),use_container_width=True,hide_index=True)
        st.caption("Candidates are algorithmic screens, not personalized investment recommendations. Check fundamentals, news, liquidity, spreads and your own risk limits.")
else:
    st.info("Select “Scan candidate list” to build a fresh candidate list. It is separate from My watchlist.")

# ---------- Persistent journal ----------
st.markdown("---")
st.header("📓 My paper-trading journal")
open_df=get_trades("OPEN")
closed_df=get_trades("CLOSED")
if not open_df.empty:
    st.markdown("**Open simulated trades**")
    for _,trade in open_df.iterrows():
        with st.container(border=True):
            c1,c2,c3,c4=st.columns([1,1,1,1])
            c1.write(f"**{trade.ticker} · {trade.side}**")
            c2.write(f"Entry ${trade.entry:.2f} · {int(trade.shares)} shares")
            c3.write(f"Stop ${trade.stop:.2f} · Target ${trade.target:.2f}")
            exit_price=c4.number_input("Exit price",min_value=0.01,value=float(trade.entry),key=f"exit_{int(trade.id)}")
            if st.button("Close simulated trade",key=f"close_{int(trade.id)}"):
                close_trade(int(trade.id),exit_price); st.rerun()
else:
    st.info("No open paper trades yet.")
if not closed_df.empty:
    total=float(closed_df.pnl.fillna(0).sum())
    wins=int((closed_df.pnl>0).sum())
    x1,x2,x3=st.columns(3)
    x1.metric("Closed-trade P&L",f"${total:+,.2f}")
    x2.metric("Win rate",f"{wins/len(closed_df)*100:.1f}%")
    x3.metric("Closed trades",len(closed_df))
    st.dataframe(closed_df[["created","ticker","side","entry","exit","shares","pnl","notes"]],use_container_width=True,hide_index=True)
    st.download_button("Download journal CSV",closed_df.to_csv(index=False),file_name="paper_trading_journal.csv",mime="text/csv")
else:
    st.caption("Closed-trade statistics appear here after you close a simulated trade.")

st.markdown("---")
st.warning("Educational tool only. Yahoo Finance data may be delayed, incomplete, rate-limited, or unavailable. No live brokerage orders are placed. Technical screens do not establish that a stock is suitable to invest in.")
