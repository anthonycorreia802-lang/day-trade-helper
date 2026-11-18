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
import html
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

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
/* TradingView-inspired terminal: quiet charcoal surfaces, restrained color, clear hierarchy. */
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
[data-testid="stAppViewContainer"] > .main { background: var(--tv-bg) !important; }
h1, h2, h3, h4, h5, h6 {
  color: var(--tv-strong) !important;
  letter-spacing: -.015em;
  font-weight: 650 !important;
}
h1 { font-size: clamp(1.55rem, 2.5vw, 2rem) !important; }
h2 { font-size: 1.35rem !important; }
h3 { font-size: 1.12rem !important; }
p, li, label, legend, [data-testid="stMarkdownContainer"] { color: var(--tv-text); }
[data-testid="stCaptionContainer"], .stCaption, small {
  color: var(--tv-muted) !important;
}
hr { border-color: var(--tv-border) !important; margin: 1rem 0 !important; }

/* Sidebar and common panels */
section[data-testid="stSidebar"] {
  background: var(--tv-panel) !important;
  border-right: 1px solid var(--tv-border);
}
section[data-testid="stSidebar"] > div { padding-top: 1rem; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: var(--tv-strong) !important; }
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span { color: var(--tv-text) !important; }

/* Inputs and select controls: dark surfaces even when focused or opened. */
.stTextInput input, .stNumberInput input, .stTextArea textarea,
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea,
[data-baseweb="select"] > div, [data-baseweb="select"] input {
  background: #111622 !important;
  color: var(--tv-strong) !important;
  -webkit-text-fill-color: var(--tv-strong) !important;
  border: 1px solid #3a4050 !important;
  border-radius: 6px !important;
}
input::placeholder, textarea::placeholder {
  color: #858c99 !important;
  -webkit-text-fill-color: #858c99 !important;
  opacity: 1 !important;
}
[data-baseweb="select"] > div:focus-within,
[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within,
.stTextInput input:focus, .stNumberInput input:focus,
.stTextArea textarea:focus {
  border-color: var(--tv-blue) !important;
  box-shadow: 0 0 0 1px var(--tv-blue) !important;
  background: #151c2b !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}
[data-baseweb="popover"], [data-baseweb="menu"],
[data-baseweb="popover"] *, [data-baseweb="menu"] *,
[role="listbox"], [role="option"] {
  background: #1e222d !important;
  color: var(--tv-text) !important;
}
[role="option"]:hover, [role="option"][aria-selected="true"] {
  background: #2a3142 !important;
  color: #ffffff !important;
}

/* Buttons: subdued default, blue primary, stable readable state after click. */
.stButton > button, .stDownloadButton > button,
[data-testid="stFormSubmitButton"] > button,
[data-testid^="stBaseButton-"] {
  min-height: 2.45rem;
  border-radius: 6px !important;
  border: 1px solid #3a4050 !important;
  background: #252a36 !important;
  color: var(--tv-text) !important;
  -webkit-text-fill-color: var(--tv-text) !important;
  font-weight: 600 !important;
  box-shadow: none !important;
  opacity: 1 !important;
  transition: background .12s ease, border-color .12s ease !important;
}
.stButton > button:hover, .stDownloadButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover,
[data-testid^="stBaseButton-"]:hover {
  background: #303747 !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  border-color: #65718a !important;
}
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible,
[data-testid="stFormSubmitButton"] > button:focus-visible,
[data-testid^="stBaseButton-"]:focus-visible {
  outline: 2px solid #6b94ff !important;
  outline-offset: 2px !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}
.stButton > button:active, .stDownloadButton > button:active,
[data-testid="stFormSubmitButton"] > button:active,
[data-testid^="stBaseButton-"]:active,
.stButton > button[aria-pressed="true"] {
  background: #35415b !important;
  border-color: #7895e8 !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}
.stButton > button:disabled, .stDownloadButton > button:disabled,
[data-testid="stFormSubmitButton"] > button:disabled,
[data-testid^="stBaseButton-"]:disabled {
  background: #202532 !important;
  border-color: #343a49 !important;
  color: #858c99 !important;
  -webkit-text-fill-color: #858c99 !important;
  cursor: not-allowed !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primary"],
[data-testid="stFormSubmitButton"] > button[kind="primary"] {
  background: var(--tv-blue) !important;
  border-color: var(--tv-blue) !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}
.stButton > button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover {
  background: #1f53e5 !important;
  border-color: #1f53e5 !important;
}
.stButton > button[kind="primary"]:active,
.stButton > button[kind="primary"]:focus,
[data-testid="stBaseButton-primary"]:active,
[data-testid="stBaseButton-primary"]:focus {
  background: #1947c7 !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}
section[data-testid="stSidebar"] .stButton > button {
  background: #252a36 !important;
  color: var(--tv-text) !important;
  -webkit-text-fill-color: var(--tv-text) !important;
}

/* Compact metric cards and data surfaces */
[data-testid="stMetric"] {
  background: var(--tv-panel) !important;
  border: 1px solid var(--tv-border) !important;
  border-radius: 7px !important;
  padding: 11px 13px !important;
  box-shadow: none !important;
  min-width: 0;
}
[data-testid="stMetric"] label,
[data-testid="stMetric"] [data-testid="stMetricLabel"] {
  color: var(--tv-muted) !important;
  font-size: .8rem !important;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
  color: var(--tv-strong) !important;
  font-size: clamp(1.05rem, 1.5vw, 1.4rem) !important;
  font-weight: 650 !important;
}
[data-testid="stMetric"] [data-testid="stMetricDelta"] { color: var(--tv-text) !important; }
[data-testid="stDataFrame"], [data-testid="stDataEditor"],
div[data-testid="stPlotlyChart"] {
  width: 100%; max-width: 100%;
}
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
  border: 1px solid var(--tv-border) !important;
  border-radius: 7px !important;
  overflow: hidden;
}

/* Expanders, tabs and selection controls remain charcoal when opened/selected. */
[data-testid="stExpander"] {
  background: var(--tv-panel) !important;
  border: 1px solid var(--tv-border) !important;
  border-radius: 7px !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary:hover,
[data-testid="stExpander"] summary:focus,
[data-testid="stExpander"] summary:active,
[data-testid="stExpander"] details[open] > summary {
  background: var(--tv-panel) !important;
  color: var(--tv-strong) !important;
  -webkit-text-fill-color: var(--tv-strong) !important;
}
[data-testid="stExpander"] details[open] > div,
[data-testid="stExpander"] .streamlit-expanderContent,
.streamlit-expanderContent {
  background: var(--tv-panel) !important;
  color: var(--tv-text) !important;
  border-top: 1px solid var(--tv-border) !important;
}
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] li,
[data-testid="stExpander"] [data-testid="stCaptionContainer"],
[data-testid="stExpander"] label,
[data-testid="stExpander"] h1,
[data-testid="stExpander"] h2,
[data-testid="stExpander"] h3,
[data-testid="stExpander"] h4 {
  color: var(--tv-text) !important;
  -webkit-text-fill-color: var(--tv-text) !important;
}
[data-testid="stTabs"] [role="tab"],
[data-testid="stTabs"] [role="tab"] *,
[data-baseweb="tab"], [data-baseweb="tab"] * {
  color: var(--tv-text) !important;
  -webkit-text-fill-color: var(--tv-text) !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"],
[data-baseweb="tab"][aria-selected="true"] {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  background: #252d3d !important;
  border-bottom-color: var(--tv-blue) !important;
}
[data-testid="stRadio"] label, [data-testid="stCheckbox"] label,
[data-testid="stToggle"] label, [role="radiogroup"] label {
  color: var(--tv-text) !important;
}

/* Alerts, tooltips and custom information icons */
[data-testid="stAlert"], [data-testid="stNotification"],
[data-testid="stToast"], [data-testid="stDialog"], [role="dialog"] {
  border-radius: 7px !important;
}
[data-testid="stDialog"], [role="dialog"],
[data-testid="stPopoverBody"], [data-testid="stTooltipContent"], [role="tooltip"] {
  background: var(--tv-panel) !important;
  color: var(--tv-text) !important;
  border-color: var(--tv-border) !important;
}
.info-tip {
  display:inline-flex; align-items:center; justify-content:center;
  width:16px; height:16px; margin-left:5px;
  border:1px solid #59657a; border-radius:50%;
  color:#aab6ca; font-size:10px; font-weight:700;
  cursor:help; vertical-align:middle; position:relative;
}
.info-tip:hover { background:#273247; border-color:#8294b4; color:#ffffff; }
.info-tip[title]:hover::after {
  content:attr(title); position:absolute; z-index:99999;
  left:50%; top:calc(100% + 7px); transform:translateX(-50%);
  width:230px; white-space:normal; padding:9px 11px;
  border:1px solid #46536a; border-radius:6px;
  background:#1e222d; color:#d1d4dc; font-size:12px;
  line-height:1.4; font-weight:400; box-shadow:0 5px 16px rgba(0,0,0,.35);
  pointer-events:none;
}
.terminal-kicker { color:#8b9bb8; text-transform:uppercase; letter-spacing:.12em; font-size:.7rem; font-weight:700; }
.educational-disclaimer {
  margin: 1rem 0 1.5rem;
  padding: 1rem 1.1rem;
  border: 1px solid #3a4050;
  border-left: 3px solid #d6a84f;
  border-radius: 8px;
  background: #1e222d;
  color: #d1d4dc !important;
  line-height: 1.55;
  font-size: .9rem;
}
.educational-disclaimer .disclaimer-heading {
  color: #f0f3fa !important;
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: .45rem;
}
.educational-disclaimer,
.educational-disclaimer * {
  background-color: transparent;
  color: #d1d4dc !important;
  -webkit-text-fill-color: #d1d4dc !important;
}
.educational-disclaimer {
  background: #1e222d !important;
  border: 1px solid #3a4050 !important;
  border-left: 3px solid #d6a84f !important;
}
.educational-disclaimer .disclaimer-heading {
  background: transparent !important;
  color: #e5c879 !important;
  -webkit-text-fill-color: #e5c879 !important;
}
.educational-disclaimer p { margin: .3rem 0; }
.educational-disclaimer strong {
  color: #f0f3fa !important;
  -webkit-text-fill-color: #f0f3fa !important;
}

/* Streamlit metric deltas carry the small percentage / return text. Keep them
   on a dark pill with an explicit foreground so theme defaults cannot wash them out. */
[data-testid="stMetric"] [data-testid="stMetricDelta"] {
  display: inline-flex !important;
  align-items: center !important;
  gap: .25rem !important;
  padding: 2px 7px !important;
  margin-top: 3px !important;
  border: 1px solid #3b4658 !important;
  border-radius: 5px !important;
  background: #252c39 !important;
  color: #dce5f2 !important;
  -webkit-text-fill-color: #dce5f2 !important;
  opacity: 1 !important;
  font-weight: 600 !important;
}
[data-testid="stMetric"] [data-testid="stMetricDelta"] *,
[data-testid="stMetric"] [data-testid="stMetricDelta"] svg {
  color: #dce5f2 !important;
  fill: #dce5f2 !important;
  -webkit-text-fill-color: #dce5f2 !important;
  opacity: 1 !important;
}

/* Reusable, explicit dark notices for paper-trading and model-learning states. */
.terminal-notice {
  display: block;
  width: 100%;
  box-sizing: border-box;
  margin: .55rem 0 .8rem;
  padding: .75rem .9rem;
  border: 1px solid #40506a;
  border-left: 3px solid #6f9df5;
  border-radius: 7px;
  background: #222b3a !important;
  color: #dce5f2 !important;
  -webkit-text-fill-color: #dce5f2 !important;
  line-height: 1.5;
  font-size: .9rem;
}
.terminal-notice * {
  background: transparent !important;
  color: #dce5f2 !important;
  -webkit-text-fill-color: #dce5f2 !important;
}
.terminal-notice-learning { border-left-color: #d6a84f; background: #302b20 !important; }
.terminal-notice-learning, .terminal-notice-learning * { color: #f0dfb4 !important; -webkit-text-fill-color: #f0dfb4 !important; }
.terminal-notice-position { border-left-color: #6f9df5; }

/* Keep Streamlit's native info boxes readable in the same dark interface. */
[data-testid="stAlert"] {
  background: #222b3a !important;
  border: 1px solid #40506a !important;
  color: #dce5f2 !important;
}
[data-testid="stAlert"] *,
[data-testid="stAlert"] [data-testid="stMarkdownContainer"] *,
[data-testid="stAlert"] svg {
  color: #dce5f2 !important;
  fill: #dce5f2 !important;
  -webkit-text-fill-color: #dce5f2 !important;
  opacity: 1 !important;
}

.terminal-hero {
  padding: .9rem 1.1rem; margin:.15rem 0 .9rem;
  border:1px solid var(--tv-border); border-radius:8px;
  background:var(--tv-panel); box-shadow:none;
}
.terminal-hero h1 { margin:.15rem 0 .25rem; font-size:clamp(1.45rem,2.4vw,1.9rem); }
.terminal-hero p { margin:0; color:var(--tv-muted) !important; }
.action-banner {
  font-size:clamp(1.05rem,1.8vw,1.4rem); font-weight:750;
  text-align:center; padding:10px 14px; border-radius:7px;
  margin:10px 0 14px; letter-spacing:.02em; box-shadow:none;
}
.buy { background:rgba(8,153,129,.16); color:#35c9ac; border:1px solid rgba(8,153,129,.55); }
.short { background:rgba(242,54,69,.15); color:#ff6b78; border:1px solid rgba(242,54,69,.55); }
.watch { background:rgba(41,98,255,.13); color:#83a7ff; border:1px solid rgba(41,98,255,.5); }
@media (max-width: 1100px) {
  div[data-testid="stHorizontalBlock"] { flex-wrap:wrap; gap:.7rem; }
  div[data-testid="column"] { min-width:min(100%,220px) !important; }
}
@media (max-width: 700px) {
  .block-container { padding-left:.65rem; padding-right:.65rem; }
  .terminal-hero { padding:.75rem; }
  [data-testid="stMetric"] { padding:9px !important; }
}
</style>
""", unsafe_allow_html=True)


def info_heading(label, explanation, level=3):
    """Render a compact heading with a hover-only explanation icon."""
    safe_label = str(label).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    safe_tip = str(explanation).replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    st.markdown(f'<h{level} style="margin:.35rem 0 .55rem">{safe_label}<span class="info-tip" title="{safe_tip}" aria-label="More information">i</span></h{level}>', unsafe_allow_html=True)


def render_terminal_notice(message, kind="info"):
    """Render a high-contrast notice with a deliberately dark surface."""
    safe_message = html.escape(str(message))
    safe_kind = kind if kind in {"info", "learning", "position"} else "info"
    st.markdown(
        f'<div class="terminal-notice terminal-notice-{safe_kind}" role="status">{safe_message}</div>',
        unsafe_allow_html=True,
    )

# ---------- Yahoo Finance symbol search / recommendations ----------
@st.cache_data(ttl=900, show_spinner=False)
def search_stock_symbols(query):
    """Search Yahoo Finance for equities, ETFs, and cryptocurrency pairs."""
    query = str(query or "").strip()
    if len(query) < 1:
        return []
    try:
        result = yf.Search(query, max_results=50)
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
    "LINK-USD": "Chainlink", "LTC-USD": "Litecoin", "BCH-USD": "Bitcoin Cash", "DOT-USD": "Polkadot",
    "TRX-USD": "TRON", "SHIB-USD": "Shiba Inu", "TON-USD": "Toncoin", "XLM-USD": "Stellar",
    "HBAR-USD": "Hedera", "SUI-USD": "Sui", "NEAR-USD": "NEAR Protocol", "UNI-USD": "Uniswap",
    "ICP-USD": "Internet Computer", "ETC-USD": "Ethereum Classic", "ATOM-USD": "Cosmos",
    "FIL-USD": "Filecoin", "APT-USD": "Aptos", "ARB-USD": "Arbitrum", "OP-USD": "Optimism",
    "INJ-USD": "Injective", "IMX-USD": "Immutable", "STX-USD": "Stacks", "SEI-USD": "Sei",
    "PEPE-USD": "Pepe", "RENDER-USD": "Render", "ALGO-USD": "Algorand", "XTZ-USD": "Tezos",
    "EOS-USD": "EOS", "MKR-USD": "Maker", "AAVE-USD": "Aave", "GRT-USD": "The Graph",
    "VET-USD": "VeChain", "MANA-USD": "Decentraland", "SAND-USD": "The Sandbox", "THETA-USD": "Theta Network",
    "FET-USD": "Artificial Superintelligence Alliance", "RUNE-USD": "THORChain", "CRV-USD": "Curve DAO",
    "LDO-USD": "Lido DAO", "JUP-USD": "Jupiter", "BONK-USD": "Bonk", "WIF-USD": "dogwifhat"
}
STOCK_RECOMMENDATION_UNIVERSE = [
    "SPY", "QQQ", "IWM", "DIA", "AAPL", "MSFT", "NVDA", "AMD", "AMZN", "META",
    "GOOGL", "TSLA", "AVGO", "NFLX", "JPM", "XOM", "LLY", "COST", "PLTR", "ORCL"
]
CRYPTO_RECOMMENDATION_UNIVERSE = [
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "BNB-USD", "DOGE-USD", "ADA-USD", "AVAX-USD",
    "LINK-USD", "LTC-USD", "BCH-USD", "DOT-USD", "TRX-USD", "SHIB-USD", "TON-USD", "XLM-USD",
    "HBAR-USD", "SUI-USD", "NEAR-USD", "UNI-USD", "ICP-USD", "ETC-USD", "ATOM-USD", "FIL-USD",
    "APT-USD", "ARB-USD", "OP-USD", "INJ-USD", "IMX-USD", "STX-USD", "SEI-USD", "PEPE-USD",
    "RENDER-USD", "ALGO-USD", "XTZ-USD", "EOS-USD", "MKR-USD", "AAVE-USD", "GRT-USD", "VET-USD",
    "MANA-USD", "SAND-USD", "THETA-USD", "FET-USD", "RUNE-USD", "CRV-USD", "LDO-USD", "JUP-USD",
    "BONK-USD", "WIF-USD"
]
RECOMMENDATION_UNIVERSE = STOCK_RECOMMENDATION_UNIVERSE + CRYPTO_RECOMMENDATION_UNIVERSE

MARKET_STOCK_SCREENERS = (
    "most_actives", "day_gainers", "day_losers", "small_cap_gainers",
    "growth_technology_stocks", "most_shorted_stocks"
)


@st.cache_data(ttl=1800, show_spinner=False)
def discover_market_universe():
    """Discover a broad rotating universe of Yahoo-listed equities, ETFs and crypto pairs."""
    discovered = {}

    def add_quote(item, forced_type=None):
        if not isinstance(item, dict):
            return
        symbol = str(item.get("symbol") or "").upper().strip()
        qtype = str(item.get("quoteType") or forced_type or "").upper()
        if not symbol or qtype not in {"EQUITY", "ETF", "CRYPTO", "CRYPTOCURRENCY"}:
            return
        asset_type = "CRYPTO" if qtype in {"CRYPTO", "CRYPTOCURRENCY"} else qtype
        discovered[symbol] = {
            "symbol": symbol,
            "name": item.get("shortName") or item.get("shortname") or item.get("longName") or item.get("longname") or ASSET_NAMES.get(symbol, symbol),
            "type": asset_type,
        }

    for symbol in RECOMMENDATION_UNIVERSE:
        discovered[symbol] = {
            "symbol": symbol,
            "name": ASSET_NAMES.get(symbol, symbol),
            "type": "CRYPTO" if symbol.endswith("-USD") else "EQUITY",
        }

    if callable(getattr(yf, "screen", None)):
        for screen_name in MARKET_STOCK_SCREENERS:
            try:
                response = yf.screen(screen_name, count=100)
                quotes = response.get("quotes", []) if isinstance(response, dict) else []
                for item in quotes:
                    add_quote(item)
            except Exception:
                continue

    for search_term in ("USD cryptocurrency", "crypto USD", "altcoins USD"):
        try:
            result = yf.Search(search_term, max_results=50)
            for item in (getattr(result, "quotes", []) or []):
                add_quote(item, forced_type="CRYPTOCURRENCY")
        except Exception:
            continue

    return list(discovered.values())


def display_asset_name(symbol):
    return ASSET_NAMES.get(str(symbol).upper(), str(symbol).upper())


def price_decimals(price):
    try:
        return 2 if abs(float(price)) >= 1 else 6
    except (TypeError, ValueError):
        return 2


def directional_price_move_pct(start_price, end_price, side="LONG"):
    start_price = float(start_price)
    end_price = float(end_price)
    side = str(side).upper()
    if not np.isfinite(start_price) or not np.isfinite(end_price) or start_price <= 0:
        return 0.0
    if side == "SHORT":
        return (start_price - end_price) / start_price * 100.0
    return (end_price - start_price) / start_price * 100.0


def calculate_directional_percentages(current_price, entry, stop, target, side):
    try:
        current_price, entry, stop, target = map(float, (current_price, entry, stop, target))
        side = str(side).upper()
    except (TypeError, ValueError):
        return {"valid": False, "reason": "Prices and side must be valid values."}
    if (not all(np.isfinite(v) for v in (current_price, entry, stop, target))
            or min(current_price, entry, stop, target) <= 0):
        return {"valid": False, "reason": "All prices must be finite and above zero."}
    if side == "LONG":
        levels_valid = stop < entry < target
        reward_pct = (target - entry) / entry * 100.0
        risk_pct = (entry - stop) / entry * 100.0
    elif side == "SHORT":
        levels_valid = target < entry < stop
        reward_pct = (entry - target) / entry * 100.0
        risk_pct = (stop - entry) / entry * 100.0
    else:
        return {"valid": False, "reason": "Side must be LONG or SHORT."}
    if not levels_valid:
        return {"valid": False, "reason": "Price levels do not match the selected trade direction."}
    return {
        "valid": True,
        "side": side,
        "entry_vs_current_pct": (entry - current_price) / current_price * 100.0,
        "target_vs_current_pct": (target - current_price) / current_price * 100.0,
        "stop_vs_current_pct": (stop - current_price) / current_price * 100.0,
        "reward_pct": reward_pct,
        "risk_pct": risk_pct,
        "reward_to_risk": reward_pct / risk_pct if risk_pct > 0 else 0.0,
    }


def paper_trade_return_pct(pnl, entry_price, quantity):
    try:
        pnl, entry_price, quantity = float(pnl), float(entry_price), float(quantity)
    except (TypeError, ValueError):
        return None
    notional = entry_price * quantity
    if not all(np.isfinite(v) for v in (pnl, entry_price, quantity)) or notional <= 0:
        return None
    return pnl / notional * 100.0


def robinhood_asset_url(symbol):
    symbol = str(symbol or "").strip().upper()
    if not symbol:
        return "https://robinhood.com/"
    if symbol.endswith("-USD"):
        asset_code = symbol[:-4]
        return f"https://robinhood.com/us/en/crypto/{quote(asset_code.lower(), safe='')}/"
    return f"https://robinhood.com/us/en/stocks/{quote(symbol.lower(), safe='')}/"


def calculate_position_size(account_size, risk_fraction, entry, stop, target, is_crypto=False):
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
        entry = price
        if side == "LONG":
            stop = round(max(0.000001, entry - stop_gap), digits)
            target = round(entry + stop_gap * rr_ratio, digits)
        else:
            stop = round(entry + stop_gap, digits)
            target = round(max(0.000001, entry - stop_gap * rr_ratio), digits)

    return {"entry": float(entry), "stop": float(stop), "target": float(target), "side": side}


AI_FEATURE_NAMES = (
    "setup_strength", "vwap_alignment", "ema_alignment",
    "momentum_alignment", "volume_confirmation"
)


def directional_learning_features(signal, side):
    side = str(side).upper()
    if side not in {"LONG", "SHORT"}:
        raise ValueError("side must be LONG or SHORT")
    direction = 1.0 if side == "LONG" else -1.0
    score = float(signal.get("long_score" if side == "LONG" else "short_score", 0.0))
    rsi = float(signal.get("rsi", 50.0))
    vwap_gap = float(signal.get("vwap_gap_pct", 0.0))
    ema_spread = float(signal.get("ema_spread_pct", 0.0))
    volume_ratio = float(signal.get("volume_ratio", 1.0))
    clip = lambda value: float(np.clip(value, -1.0, 1.0))
    return {
        "setup_strength": clip((score / 5.0) * 2.0 - 1.0),
        "vwap_alignment": clip(direction * vwap_gap / 0.50),
        "ema_alignment": clip(direction * ema_spread / 0.30),
        "momentum_alignment": clip(direction * (rsi - 50.0) / 25.0),
        "volume_confirmation": clip((volume_ratio - 1.0) / 1.50)
    }


def evaluate_perceptron_trade(features_dict, weights_dict, bias):
    activation = float(bias)
    for name in AI_FEATURE_NAMES:
        activation += float(weights_dict.get(name, 0.0)) * float(features_dict.get(name, 0.0))
    probability = 1.0 / (1.0 + np.exp(-np.clip(activation, -30.0, 30.0)))
    return probability, activation
