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
/* Percentage direction badges: arrows show actual movement; neutral is explicit. */
.pct-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 4px 0 1px;
  padding: 4px 9px;
  border: 1px solid transparent;
  border-radius: 5px;
  font-size: 13.5px !important;
  font-weight: 700;
  line-height: 1.35;
  white-space: normal;
}
.pct-indicator-icon { font-size: 15px; font-weight: 900; line-height: 1; }
.pct-up { color: #58d6a8 !important; background: rgba(8,153,129,.13) !important; border-color: rgba(8,153,129,.42) !important; }
.pct-down { color: #ff858e !important; background: rgba(242,54,69,.12) !important; border-color: rgba(242,54,69,.42) !important; }
.pct-neutral { color: #c1c8d4 !important; background: rgba(139,145,158,.13) !important; border-color: rgba(139,145,158,.35) !important; }
.pct-indicator.pct-up, .pct-indicator.pct-up * { color:#58d6a8 !important; -webkit-text-fill-color:#58d6a8 !important; }
.pct-indicator.pct-down, .pct-indicator.pct-down * { color:#ff858e !important; -webkit-text-fill-color:#ff858e !important; }
.pct-indicator.pct-neutral, .pct-indicator.pct-neutral * { color:#c1c8d4 !important; -webkit-text-fill-color:#c1c8d4 !important; }

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


/* Readability pass: larger body copy, captions, controls and chart labels. */
:root {
  --tv-muted: #aeb8c8;
  --tv-text: #e0e5ee;
}
html, body, .stApp, [data-testid="stAppViewContainer"] {
  font-size: 16px !important;
  line-height: 1.55 !important;
}
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] blockquote,
p, li {
  color: var(--tv-text) !important;
  font-size: 16px !important;
  line-height: 1.55 !important;
}
[data-testid="stCaptionContainer"],
.stCaption,
small,
[data-testid="stCaptionContainer"] *,
.stCaption * {
  color: var(--tv-muted) !important;
  font-size: 14px !important;
  line-height: 1.45 !important;
}
label, legend, [data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] *,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p {
  color: #e0e5ee !important;
  font-size: 15px !important;
  line-height: 1.45 !important;
}
.stTextInput input, .stNumberInput input, .stTextArea textarea,
[data-baseweb="select"] > div, [data-baseweb="select"] input,
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
  font-size: 15.5px !important;
  min-height: 42px !important;
}
.stButton > button, .stDownloadButton > button,
[data-testid="stFormSubmitButton"] > button,
[data-testid^="stBaseButton-"],
[data-testid="stLinkButton"] > a {
  font-size: 15px !important;
  line-height: 1.35 !important;
  min-height: 44px !important;
  padding: .55rem .85rem !important;
  opacity: 1 !important;
}
[data-testid="stMetric"] {
  padding: 13px 15px !important;
  min-height: 96px !important;
}
[data-testid="stMetric"] label,
[data-testid="stMetric"] [data-testid="stMetricLabel"] {
  color: var(--tv-muted) !important;
  font-size: 14px !important;
  line-height: 1.35 !important;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
  color: #f0f3fa !important;
  font-size: clamp(18px, 1.45vw, 23px) !important;
  line-height: 1.3 !important;
}
[data-testid="stMetric"] [data-testid="stMetricDelta"],
[data-testid="stMetric"] [data-testid="stMetricDelta"] * {
  font-size: 13.5px !important;
  line-height: 1.4 !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary * {
  color: #f0f3fa !important;
  font-size: 15.5px !important;
  line-height: 1.45 !important;
}
[data-testid="stTabs"] [role="tab"],
[data-baseweb="tab"],
[data-testid="stRadio"] label,
[data-testid="stCheckbox"] label,
[data-testid="stToggle"] label {
  font-size: 15px !important;
}
[data-baseweb="menu"] *, [role="option"], [role="listbox"] {
  font-size: 15px !important;
  line-height: 1.45 !important;
}
.info-tip { width: 18px; height: 18px; font-size: 12px !important; }
.info-tip[title]:hover::after { font-size: 13.5px !important; width: 250px; line-height: 1.5; }
.terminal-kicker {
  color: #aeb8c8 !important;
  font-size: 12.5px !important;
  line-height: 1.4 !important;
  letter-spacing: .08em !important;
}
.educational-disclaimer,
.educational-disclaimer p,
.educational-disclaimer li {
  color: #e0e5ee !important;
  font-size: 15px !important;
  line-height: 1.6 !important;
}
.educational-disclaimer .disclaimer-heading { font-size: 17px !important; }
.terminal-notice, .terminal-notice * {
  font-size: 15px !important;
  line-height: 1.55 !important;
}
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
  font-size: 14px !important;
}
[data-testid="stDataFrame"] canvas,
[data-testid="stDataEditor"] canvas {
  font-size: 14px !important;
}
.action-banner { font-size: clamp(17px, 1.7vw, 22px) !important; padding: 13px 16px !important; }
.terminal-hero p { font-size: 15.5px !important; line-height: 1.5 !important; }
@media (max-width: 900px) {
  html, body, .stApp, [data-testid="stAppViewContainer"] { font-size: 15.5px !important; }
  [data-testid="stMetric"] { min-height: 88px !important; }
}

/* Robinhood handoff: a real link button must be readable before hover or click. */
[data-testid="stLinkButton"] { width: 100% !important; }
[data-testid="stLinkButton"] > a,
[data-testid="stLinkButton"] a[role="button"],
.stLinkButton a {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  min-height: 48px !important;
  padding: .65rem 1rem !important;
  background: #2962ff !important;
  border: 1px solid #5d86ff !important;
  border-radius: 7px !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  font-size: 15px !important;
  font-weight: 700 !important;
  line-height: 1.35 !important;
  text-decoration: none !important;
  opacity: 1 !important;
  box-shadow: 0 2px 8px rgba(41,98,255,.18) !important;
}
[data-testid="stLinkButton"] > a *,
[data-testid="stLinkButton"] a[role="button"] *,
.stLinkButton a * {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  opacity: 1 !important;
}
[data-testid="stLinkButton"] > a:hover,
[data-testid="stLinkButton"] a[role="button"]:hover,
.stLinkButton a:hover {
  background: #1f53e5 !important;
  border-color: #86a5ff !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  transform: translateY(-1px);
}
[data-testid="stLinkButton"] > a:focus,
[data-testid="stLinkButton"] > a:focus-visible,
[data-testid="stLinkButton"] a[role="button"]:focus-visible,
.stLinkButton a:focus-visible {
  outline: 2px solid #a9c0ff !important;
  outline-offset: 3px !important;
  background: #1f53e5 !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}
[data-testid="stLinkButton"] > a:active,
[data-testid="stLinkButton"] a[role="button"]:active,
.stLinkButton a:active {
  background: #1947c7 !important;
  border-color: #a9c0ff !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  transform: none !important;
}

/* Paper desk empty state uses the same quiet bordered panel language as the dashboard. */
.paper-empty-state {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  width: 100%;
  box-sizing: border-box;
  margin: .7rem 0 1rem;
  padding: 18px 20px;
  background: #1e222d !important;
  border: 1px solid #3a4050 !important;
  border-left: 3px solid #6f9df5 !important;
  border-radius: 8px !important;
  color: #e0e5ee !important;
  -webkit-text-fill-color: #e0e5ee !important;
}
.paper-empty-state * {
  background: transparent !important;
  color: #e0e5ee !important;
  -webkit-text-fill-color: #e0e5ee !important;
}
.paper-empty-icon { font-size: 25px; line-height: 1.25; flex: 0 0 auto; }
.paper-empty-title { color: #f0f3fa !important; -webkit-text-fill-color: #f0f3fa !important; font-size: 17px; font-weight: 700; margin-bottom: 3px; }
.paper-empty-copy { color: #b8c2d1 !important; -webkit-text-fill-color: #b8c2d1 !important; font-size: 15px; line-height: 1.5; }

/* Real trading handoff panel: visually distinct from the simulated trading desk. */
[data-testid="stVerticalBlockBorderWrapper"]:has(.robinhood-panel-marker) {
  background: linear-gradient(145deg, #202a3b 0%, #1b2230 100%) !important;
  border: 1px solid #465875 !important;
  border-radius: 10px !important;
  padding: 12px !important;
  box-shadow: 0 5px 18px rgba(0,0,0,.16) !important;
}
.robinhood-panel-marker { display: none !important; }
.robinhood-handoff-kicker {
  display: inline-block;
  margin: 0 0 7px;
  padding: 4px 8px;
  border: 1px solid #52698e;
  border-radius: 4px;
  background: #273752 !important;
  color: #b9ccf4 !important;
  -webkit-text-fill-color: #b9ccf4 !important;
  font-size: 11px;
  font-weight: 750;
  letter-spacing: .08em;
}
.robinhood-handoff-copy {
  margin: 3px 0 9px;
  color: #bdc8d9 !important;
  -webkit-text-fill-color: #bdc8d9 !important;
  font-size: 14px;
  line-height: 1.5;
}
@media (max-width: 700px) {
  .paper-empty-state { padding: 14px; gap: 10px; }
  [data-testid="stVerticalBlockBorderWrapper"]:has(.robinhood-panel-marker) { padding: 9px !important; }
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


def render_paper_empty_state():
    """Show a readable, bordered empty state when the paper desk has no trades."""
    st.markdown(
        '<div class="paper-empty-state" role="status">'
        '<div class="paper-empty-icon" aria-hidden="true">▤</div>'
        '<div><div class="paper-empty-title">Your paper-trading desk is ready</div>'
        '<div class="paper-empty-copy">Add a simulated trade above to start tracking positions and performance.</div></div>'
        '</div>',
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

# Yahoo Finance screeners refresh the stock universe, so the scanner is not limited
# to the original hard-coded sample. Search remains available for other listed tickers.
MARKET_STOCK_SCREENERS = (
    "most_actives", "day_gainers", "day_losers", "small_cap_gainers",
    "growth_technology_stocks", "most_shorted_stocks"
)


@st.cache_data(ttl=1800, show_spinner=False)
def discover_market_universe():
    """Discover a broad rotating universe of Yahoo-listed equities, ETFs and crypto pairs.

    Yahoo limits each screener response; this is a broad active-market universe, not
    a claim that every security worldwide can be enumerated or scanned at once.
    """
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

    # Baseline coverage guarantees common tickers remain available if a screener fails.
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

    # Search additional crypto listings not present in the baseline dictionary.
    for search_term in ("USD cryptocurrency", "crypto USD", "altcoins USD"):
        try:
            result = yf.Search(search_term, max_results=50)
            for item in (getattr(result, "quotes", []) or []):
                add_quote(item, forced_type="CRYPTOCURRENCY")
        except Exception:
            continue

    return list(discovered.values())


def display_asset_name(symbol):
    """Readable asset name for known symbols; fall back to Yahoo Finance metadata."""
    return ASSET_NAMES.get(str(symbol).upper(), str(symbol).upper())


def price_decimals(price):
    """Use extra precision for low-priced crypto assets."""
    try:
        return 2 if abs(float(price)) >= 1 else 6
    except (TypeError, ValueError):
        return 2


def directional_price_move_pct(start_price, end_price, side="LONG"):
    """Return a favorable-positive move percentage for the selected position side."""
    start_price = float(start_price)
    end_price = float(end_price)
    side = str(side).upper()
    if not np.isfinite(start_price) or not np.isfinite(end_price) or start_price <= 0:
        return 0.0
    if side == "SHORT":
        return (start_price - end_price) / start_price * 100.0
    return (end_price - start_price) / start_price * 100.0


def calculate_directional_percentages(current_price, entry, stop, target, side):
    """Calculate entry gap, planned risk and target reward with LONG/SHORT signs handled correctly.

    Entry gap is a raw price difference from the current quote. Reward and risk are
    always positive magnitudes measured from entry, so a SHORT target below entry
    is correctly displayed as positive potential reward.
    """
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


def percentage_direction(value, neutral_threshold=0.05):
    """Return a simple up/down/neutral marker for a percentage movement."""
    try:
        movement = float(value)
    except (TypeError, ValueError):
        return {"icon": "→", "state": "neutral", "label": "Neutral"}
    if not np.isfinite(movement) or abs(movement) <= abs(float(neutral_threshold)):
        return {"icon": "→", "state": "neutral", "label": "Neutral"}
    if movement > 0:
        return {"icon": "↑", "state": "up", "label": "Moving up"}
    return {"icon": "↓", "state": "down", "label": "Moving down"}


def percentage_indicator_html(value, movement=None, label=None, neutral_threshold=0.05):
    """Create an accessible, colored up/down/neutral pill for percentage readouts.

    `value` is the percentage shown to the reader. `movement` may be supplied
    separately when the displayed value is a positive reward/risk magnitude but
    the underlying price direction is up or down (for example, a SHORT target).
    """
    try:
        shown_value = float(value)
    except (TypeError, ValueError):
        shown_value = 0.0
    direction = percentage_direction(shown_value if movement is None else movement, neutral_threshold)
    shown_label = str(label) if label is not None else f"{shown_value:+.2f}%"
    safe_label = html.escape(shown_label)
    safe_state = direction["state"]
    safe_icon = direction["icon"]
    aria = html.escape(direction["label"])
    return (
        f'<span class="pct-indicator pct-{safe_state}" role="status" aria-label="{aria}">'
        f'<span class="pct-indicator-icon" aria-hidden="true">{safe_icon}</span>'
        f'<span>{safe_label}</span></span>'
    )


def paper_trade_return_pct(pnl, entry_price, quantity):
    """Return P&L as a percentage of entry notional (entry price × shares/units)."""
    try:
        pnl, entry_price, quantity = float(pnl), float(entry_price), float(quantity)
    except (TypeError, ValueError):
        return None
    notional = entry_price * quantity
    if not all(np.isfinite(v) for v in (pnl, entry_price, quantity)) or notional <= 0:
        return None
    return pnl / notional * 100.0


def robinhood_asset_url(symbol):
    """Build the official Robinhood asset detail URL for stocks/ETFs or USD crypto pairs."""
    symbol = str(symbol or "").strip().upper()
    if not symbol:
        return "https://robinhood.com/"
    if symbol.endswith("-USD"):
        asset_code = symbol[:-4]
        return f"https://robinhood.com/us/en/crypto/{quote(asset_code.lower(), safe='')}/"
    return f"https://robinhood.com/us/en/stocks/{quote(symbol.lower(), safe='')}/"


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



AI_FEATURE_NAMES = (
    "setup_strength", "vwap_alignment", "ema_alignment",
    "momentum_alignment", "volume_confirmation"
)


def directional_learning_features(signal, side):
    """Create direction-normalized, bounded features from a signal snapshot."""
    side = str(side).upper()
    if side not in {"LONG", "SHORT"}:
        raise ValueError("side must be LONG or SHORT")
    direction = 1.0 if side == "LONG" else -1.0
    score = float(signal.get("long_score" if side == "LONG" else "short_score", 0.0))
    rsi = float(signal.get("rsi", 50.0))
    vwap_gap = float(signal.get("reference_gap_pct", signal.get("vwap_gap_pct", 0.0)))
    ema_spread = float(signal.get("trend_spread_pct", signal.get("ema_spread_pct", 0.0)))
    volume_ratio = float(signal.get("volume_ratio", 1.0))
    clip = lambda value: float(np.clip(value, -1.0, 1.0))
    return {
        "setup_strength": clip((score / 5.0) * 2.0 - 1.0),
        "vwap_alignment": clip(direction * vwap_gap / 0.50),
        "ema_alignment": clip(direction * ema_spread / 0.30),
        "momentum_alignment": clip(direction * (rsi - 50.0) / 25.0),
        "volume_confirmation": clip((volume_ratio - 1.0) / 1.5),
    }


def fit_adaptive_model(paper_trades, min_samples=20, trading_horizon=None):
    """Fit a small local model on closed practice trades from the matching holding horizon."""
    samples, outcomes = [], []
    for trade in paper_trades or []:
        if not isinstance(trade, dict) or str(trade.get("status", "")).upper() != "CLOSED":
            continue
        # Legacy trades predate the horizon selector and are treated as day trades.
        trade_horizon = trade.get("trading_horizon", "Day Trading")
        if trading_horizon is not None and trade_horizon != trading_horizon:
            continue
        features = trade.get("ai_features")
        pnl = trade.get("pnl")
        if not isinstance(features, dict) or pnl is None:
            continue
        try:
            vector = [float(features[name]) for name in AI_FEATURE_NAMES]
            outcome = 1.0 if float(pnl) > 0 else (0.0 if float(pnl) < 0 else None)
        except (KeyError, TypeError, ValueError):
            continue
        if outcome is None or not np.all(np.isfinite(vector)):
            continue
        samples.append(vector)
        outcomes.append(outcome)

    sample_count = len(samples)
    win_rate = float(np.mean(outcomes)) if outcomes else None
    if sample_count < int(min_samples) or len(set(outcomes)) < 2:
        return {
            "active": False, "sample_count": sample_count, "min_samples": int(min_samples),
            "win_rate": win_rate, "reason": "More varied closed paper trades are needed before fitting a model."
        }

    x = np.asarray(samples, dtype=float)
    y = np.asarray(outcomes, dtype=float)
    mean = x.mean(axis=0)
    scale = x.std(axis=0)
    scale[scale < 1e-6] = 1.0
    x_scaled = (x - mean) / scale
    x_design = np.column_stack([np.ones(len(x_scaled)), x_scaled])
    weights = np.zeros(x_design.shape[1], dtype=float)
    # Deterministic batch gradient descent; modest L2 penalty limits overfitting.
    for _ in range(700):
        logits = np.clip(x_design @ weights, -20, 20)
        probabilities = 1.0 / (1.0 + np.exp(-logits))
        gradient = (x_design.T @ (probabilities - y)) / len(y)
        gradient[1:] += 0.08 * weights[1:]
        weights -= 0.08 * gradient
    return {
        "active": True, "sample_count": sample_count, "min_samples": int(min_samples),
        "win_rate": win_rate, "weights": weights.tolist(),
        "mean": mean.tolist(), "scale": scale.tolist(),
        "feature_names": list(AI_FEATURE_NAMES),
    }


def predict_adaptive_model(model, features):
    """Return a paper-history pattern estimate, or None while the model is learning."""
    if not model or not model.get("active") or not isinstance(features, dict):
        return None
    try:
        x = np.asarray([float(features[name]) for name in AI_FEATURE_NAMES], dtype=float)
        mean = np.asarray(model["mean"], dtype=float)
        scale = np.asarray(model["scale"], dtype=float)
        weights = np.asarray(model["weights"], dtype=float)
        z = float(np.r_[1.0, (x - mean) / scale] @ weights)
        return float(1.0 / (1.0 + np.exp(-np.clip(z, -20, 20))))
    except (KeyError, TypeError, ValueError, FloatingPointError):
        return None

def build_reward_assessment(signal, adaptive_model=None, trend_bias="Unavailable", rr_ratio=1.8):
    """Explain the selected horizon's five technical checks without claiming win probability."""
    long_score = int(signal.get("long_score", 0))
    short_score = int(signal.get("short_score", 0))
    horizon = signal.get("horizon", "Day Trading")
    if long_score == short_score:
        return {
            "side": "MIXED", "score": max(long_score, short_score),
            "label": "No clear directional edge", "plan": None,
            "technical_alignment_pct": max(long_score, short_score) / 5.0 * 100.0,
            "checks_passed": max(long_score, short_score), "checks_total": 5,
            "potential_reward_pct": None, "risk_pct": None,
            "reward_to_risk": None, "pattern_estimate": None,
            "reasons": [
                f"Bullish and bearish {horizon.lower()} checks are tied, so the model does not favor either direction.",
                "Wait for price, trend and momentum to align before treating either target as a useful scenario.",
            ],
        }

    side = "LONG" if long_score > short_score else "SHORT"
    score = long_score if side == "LONG" else short_score
    is_long = side == "LONG"
    price = float(signal.get("price", 0.0))
    digits = price_decimals(price)
    stop_gap = max(float(signal.get("stop_dist", 0.0)), price * 0.0025, 0.000001)
    plan = build_quick_trade_plan(signal, price, stop_gap, rr_ratio, side, digits)

    volume_ratio = float(signal.get("volume_ratio", 1.0))
    rsi = float(signal.get("rsi", 50.0))
    trend_text = str(trend_bias or "Unavailable").lower()
    trend_matches = ("bullish" in trend_text or "up" in trend_text) if is_long else ("bearish" in trend_text or "down" in trend_text)
    if horizon == "Day Trading":
        above_vwap = bool(signal.get("above_vwap", float(signal.get("vwap_gap_pct", 0.0)) > 0))
        ema_bullish = bool(signal.get("ema_bullish", float(signal.get("ema_spread_pct", 0.0)) > 0))
        price_confirm = bool(signal.get("price_above_ema9", True))
        volume_ok = volume_ratio >= 0.85
        momentum_ok = (40 < rsi < 70) if is_long else (30 < rsi < 60)
        checks = [
            ("Price versus VWAP", above_vwap if is_long else not above_vwap,
             "Price is above VWAP, supporting buyers." if is_long else "Price is below VWAP, supporting sellers.",
             "Price is below VWAP, weakening the long case." if is_long else "Price is above VWAP, weakening the short case."),
            ("EMA 9 / EMA 20 trend", ema_bullish if is_long else not ema_bullish,
             "EMA 9 is above EMA 20, showing an upward short-term trend." if is_long else "EMA 9 is below EMA 20, showing a downward short-term trend.",
             "EMA 9 / EMA 20 are not aligned with this direction."),
            ("Price confirmation", price_confirm if is_long else not price_confirm,
             "Price is on the supportive side of EMA 9." if is_long else "Price is below EMA 9, supporting the short scenario.",
             "Price has not confirmed this direction around EMA 9."),
            ("Volume confirmation", volume_ok,
             f"Volume is {volume_ratio:.2f}× its recent average, meeting the activity check.",
             f"Volume is {volume_ratio:.2f}× its recent average, below the confirmation threshold."),
            ("RSI momentum", momentum_ok,
             f"RSI is {rsi:.1f}, inside the preferred momentum range for this side.",
             f"RSI is {rsi:.1f}, outside the preferred momentum range for this side."),
        ]
    else:
        reference_name = str(signal.get("reference_name", "trend average"))
        fast_name = str(signal.get("trend_fast_name", "faster average"))
        slow_name = str(signal.get("trend_slow_name", "slower average"))
        reference_gap = float(signal.get("reference_gap_pct", 0.0))
        trend_bullish = bool(signal.get("trend_bullish", False))
        slope_pct = float(signal.get("trend_slope_pct", 0.0))
        price_confirm = bool(signal.get("price_above_trend_fast", True))
        volume_threshold = 0.80 if horizon == "Swing Trading" else 0.75
        volume_ok = volume_ratio >= volume_threshold
        momentum_ok = (40 < rsi < 70) if horizon == "Swing Trading" else (42 < rsi < 72)
        checks = [
            (f"Price versus {reference_name}", reference_gap > 0 if is_long else reference_gap < 0,
             f"Price is above {reference_name}, supporting the upward case." if is_long else f"Price is below {reference_name}, supporting the downward case.",
             f"Price is below {reference_name}, weakening the long case." if is_long else f"Price is above {reference_name}, weakening the short case."),
            (f"{fast_name} / {slow_name} trend", trend_bullish if is_long else not trend_bullish,
             f"{fast_name} is above {slow_name}, supporting the longer trend." if is_long else f"{fast_name} is below {slow_name}, supporting the downward trend.",
             f"{fast_name} and {slow_name} are not aligned with this direction."),
            ("Trend slope / price position", (slope_pct > 0 and price_confirm) if is_long else (slope_pct < 0 and not price_confirm),
             f"The faster trend line is moving in the selected direction ({slope_pct:+.2f}% over its lookback).",
             f"The faster trend line or current price is not confirming this direction ({slope_pct:+.2f}% slope)."),
            ("Volume confirmation", volume_ok,
             f"Volume is {volume_ratio:.2f}× its recent average, meeting the activity check.",
             f"Volume is {volume_ratio:.2f}× its recent average, below the confirmation threshold."),
            ("RSI momentum", momentum_ok,
             f"RSI is {rsi:.1f}, inside the preferred momentum range for this horizon.",
             f"RSI is {rsi:.1f}, outside the preferred momentum range for this horizon."),
        ]

    reasons = [f"{'✓' if passed else '!'} {name}: {good if passed else caution}" for name, passed, good, caution in checks]
    if trend_bias and trend_bias not in {"Unavailable", "Not enough data"}:
        reasons.append(
            f"{'✓' if trend_matches else '!'} Higher timeframe: {trend_bias}; "
            + ("it agrees with this setup." if trend_matches else "it does not confirm this direction.")
        )
    label = "Strong technical confluence" if score >= 4 and trend_matches else (
        "Developing setup" if score >= 3 else "Weak / wait for confirmation"
    )
    percent_metrics = calculate_directional_percentages(
        price, float(plan["entry"]), float(plan["stop"]), float(plan["target"]), side
    )
    if not percent_metrics.get("valid"):
        potential_reward_pct = risk_pct = reward_to_risk = None
    else:
        potential_reward_pct = percent_metrics["reward_pct"]
        risk_pct = percent_metrics["risk_pct"]
        reward_to_risk = percent_metrics["reward_to_risk"]
    pattern_estimate = predict_adaptive_model(
        adaptive_model, directional_learning_features(signal, side)
    ) if adaptive_model else None
    return {
        "side": side, "score": score, "label": label, "plan": plan,
        "technical_alignment_pct": score / 5.0 * 100.0,
        "checks_passed": score, "checks_total": 5,
        "potential_reward_pct": potential_reward_pct, "risk_pct": risk_pct,
        "reward_to_risk": reward_to_risk,
        "pattern_estimate": pattern_estimate, "trend_matches": trend_matches,
        "reasons": reasons,
    }

def simulate_historical_practice(df, side="LONG", bars_back=20, horizon=10, rr_ratio=2.0, atr_multiple=1.0):
    """Replay one educational trade on historical candles; resolve same-candle ties conservatively."""
    side = str(side).upper()
    if side not in {"LONG", "SHORT"}:
        raise ValueError("side must be LONG or SHORT")
    if df is None or df.empty or not {"Open", "High", "Low", "Close", "ATR"}.issubset(df.columns):
        raise ValueError("Historical candles with OHLC and ATR data are required.")
    bars_back, horizon = int(bars_back), int(horizon)
    if horizon < 1 or bars_back < horizon or bars_back >= len(df):
        raise ValueError("Choose a historical starting candle with enough future candles to replay.")
    start_index = len(df) - 1 - bars_back
    start = df.iloc[start_index]
    future = df.iloc[start_index + 1:start_index + 1 + horizon]
    if len(future) < horizon:
        raise ValueError("Not enough future candles for the selected replay window.")
    entry = float(start["Close"])
    atr = float(start["ATR"])
    if not np.isfinite(entry) or entry <= 0 or not np.isfinite(atr) or atr <= 0:
        raise ValueError("The selected historical entry candle has invalid price or volatility data.")
    risk_distance = max(atr * float(atr_multiple), entry * 0.0025)
    if side == "LONG":
        stop, target = entry - risk_distance, entry + risk_distance * float(rr_ratio)
    else:
        stop, target = entry + risk_distance, max(0.000001, entry - risk_distance * float(rr_ratio))
    exit_price, outcome, exit_time, note = float(future["Close"].iloc[-1]), "TIME EXIT", future.index[-1], "Neither stop nor target was reached within the replay window."
    for timestamp, candle in future.iterrows():
        if side == "LONG":
            stop_hit, target_hit = float(candle["Low"]) <= stop, float(candle["High"]) >= target
        else:
            stop_hit, target_hit = float(candle["High"]) >= stop, float(candle["Low"]) <= target
        if stop_hit and target_hit:
            exit_price, outcome, exit_time = stop, "STOP LOSS", timestamp
            note = "Both levels appeared inside one candle; the replay assumes the stop was hit first (conservative assumption)."
            break
        if stop_hit:
            exit_price, outcome, exit_time, note = stop, "STOP LOSS", timestamp, "The stop level was touched before the target in the replay."
            break
        if target_hit:
            exit_price, outcome, exit_time, note = target, "TAKE PROFIT", timestamp, "The target level was reached inside the replay window."
            break
    pnl_per_unit = (exit_price - entry) if side == "LONG" else (entry - exit_price)
    return {
        "side": side, "entry": entry, "stop": stop, "target": target,
        "exit": float(exit_price), "outcome": outcome, "pnl_pct": pnl_per_unit / entry * 100,
        "r_multiple": pnl_per_unit / risk_distance, "start_time": str(start.name),
        "exit_time": str(exit_time), "bars_checked": len(future), "note": note,
    }


BEGINNER_TRADING_QUIZ = (
    {"question": "What does VWAP compare?", "options": ["Price weighted by trading volume", "The highest price of the day", "A company's yearly profit", "The number of shares available"], "answer": "Price weighted by trading volume", "why": "VWAP is the average traded price weighted by volume. Traders compare current price with it for session context."},
    {"question": "What is a stop loss for?", "options": ["To plan an exit if price moves against the trade", "To guarantee a profit", "To increase the position size", "To predict tomorrow's closing price"], "answer": "To plan an exit if price moves against the trade", "why": "A stop defines where the plan is considered invalid and the simulated position should be closed. Real fills can differ."},
    {"question": "What can RSI above 70 suggest?", "options": ["Strong or overextended upward momentum", "A guaranteed price drop", "The stock is undervalued", "Trading volume is zero"], "answer": "Strong or overextended upward momentum", "why": "RSI above 70 is commonly called overbought, but strong trends can remain elevated and it does not guarantee a reversal."},
    {"question": "When EMA 9 is above EMA 20, what does that usually indicate?", "options": ["Short-term upward trend pressure", "A guaranteed buy signal", "A lower trading volume", "A confirmed company dividend"], "answer": "Short-term upward trend pressure", "why": "The faster EMA is above the slower EMA, which can indicate upward momentum; it is not enough on its own to confirm a trade."},
    {"question": "A 2:1 reward-to-risk plan means what?", "options": ["The target is twice as far from entry as the stop", "The stop is twice as far as the target", "Two trades must be opened", "The trade has a 2% chance of loss"], "answer": "The target is twice as far from entry as the stop", "why": "A 2:1 plan targets two units of potential reward for each one unit of planned risk. It does not imply a 2-in-1 win probability."},
    {"question": "Why calculate position size before a trade?", "options": ["To keep the planned loss within a risk budget", "To guarantee the target is reached", "To remove market volatility", "To make every trade profitable"], "answer": "To keep the planned loss within a risk budget", "why": "Position size links quantity to the distance between entry and stop, helping keep the planned loss within the chosen risk amount."},
)


def render_beginner_quiz():
    """Render a short, objective trading-basics quiz with immediate explanations."""
    with st.expander("🧠 Beginner Knowledge Quiz", expanded=False):
        total = len(BEGINNER_TRADING_QUIZ)
        index = int(st.session_state.get("beginner_quiz_index", 0))
        results = st.session_state.setdefault("beginner_quiz_results", {})
        if index >= total:
            score = sum(bool(item.get("correct")) for item in results.values())
            st.success(f"Quiz complete: {score} / {total} correct.")
            st.caption("Review the explanations above in the Beginner's Guide, then try again to improve your score.")
            if st.button("Restart beginner quiz", key="beginner_quiz_restart"):
                st.session_state.beginner_quiz_index = 0
                st.session_state.beginner_quiz_results = {}
                st.rerun()
            return
        item = BEGINNER_TRADING_QUIZ[index]
        st.progress((index + 1) / total, text=f"Question {index + 1} of {total}")
        st.markdown(f"**{item['question']}**")
        chosen = st.radio("Choose one answer", item["options"], key=f"beginner_quiz_answer_{index}", label_visibility="collapsed")
        result = results.get(str(index))
        if result is None and st.button("Check answer", key=f"beginner_quiz_check_{index}", type="primary"):
            result = {"correct": chosen == item["answer"], "chosen": chosen}
            results[str(index)] = result
        if result is not None:
            if result["correct"]:
                st.success("That's right. " + item["why"])
            else:
                st.info(f"Good practice. Correct answer: **{item['answer']}**. {item['why']}")
            if st.button("Next question", key=f"beginner_quiz_next_{index}"):
                st.session_state.beginner_quiz_index = index + 1
                st.rerun()


def render_historical_practice_simulator(df, ticker, rr_ratio=1.8, trading_horizon="Day Trading"):
    """Offer a one-trade historical replay using only candles already loaded for the selected asset."""
    with st.expander("🎮 Practice Trade Simulator", expanded=False):
        st.caption(f"Practice candles follow the selected {trading_horizon.lower()} chart interval. A candle may represent minutes, a day, a week or a month.")
        max_back = min(120, len(df) - 2) if df is not None else 0
        if max_back < 6:
            st.info("Load more historical candles or choose a longer chart timeframe to use the simulator.")
            return
        horizon_options = [n for n in [5, 10, 15, 20] if n <= max_back]
        horizon = st.selectbox("How many future candles should the simulation replay?", horizon_options, index=min(1, len(horizon_options)-1), key=f"practice_horizon_{ticker}")
        max_back = min(120, len(df) - 2)
        default_back = min(max_back, max(horizon + 5, 20))
        bars_back = st.slider("Choose a past entry point (candles before latest)", min_value=horizon, max_value=max_back, value=default_back, key=f"practice_bars_back_{ticker}")
        side = st.radio("Practice direction", ["LONG", "SHORT"], horizontal=True, key=f"practice_side_{ticker}")
        rr = st.select_slider("Target reward-to-risk", options=[1.0, 1.5, 2.0, 2.5, 3.0], value=float(min([1.0, 1.5, 2.0, 2.5, 3.0], key=lambda v: abs(v - float(rr_ratio)))), key=f"practice_rr_{ticker}")
        if st.button("Run historical practice", key=f"practice_run_{ticker}", type="primary"):
            try:
                replay = simulate_historical_practice(df, side, bars_back, horizon, rr)
                st.session_state[f"practice_result_{ticker}"] = replay
            except Exception as exc:
                st.error(f"Could not run this practice scenario: {exc}")
        replay = st.session_state.get(f"practice_result_{ticker}")
        if replay:
            st.markdown(f"**{replay['side']} result: {replay['outcome']}**")
            r1, r2, r3 = st.columns(3)
            r1.metric("Entry", f"${replay['entry']:,.{price_decimals(replay['entry'])}f}")
            r2.metric("Exit", f"${replay['exit']:,.{price_decimals(replay['exit'])}f}")
            r3.metric("Hypothetical result", f"{replay['pnl_pct']:+.2f}%", f"{replay['r_multiple']:+.2f}R")
            r3.markdown(percentage_indicator_html(replay["pnl_pct"], label=f"{replay['pnl_pct']:+.2f}% practice return"), unsafe_allow_html=True)
            st.caption(f"{display_asset_name(ticker)} · {replay['bars_checked']} candles · {replay['start_time']} to {replay['exit_time']}. {replay['note']}")
        st.caption("Educational replay only: one historical setup, no fees/spread/slippage, and no claim that the next trade will behave the same way. If one candle touches both stop and target, the simulator assumes the stop happened first.")

def scan_recommendation_candidates(
    scan_interval="15m", prepost=False, rr_ratio=1.8, extra_symbols=None,
    learning_trades=None, scan_offset=0, batch_size=30, trading_horizon="Day Trading"
):
    """Scan a rotating basket from a broad live market universe plus pinned watchlist assets."""
    universe = discover_market_universe()
    names = {item["symbol"]: item.get("name", item["symbol"]) for item in universe}
    all_symbols = list(dict.fromkeys(item["symbol"] for item in universe))

    pinned = []
    for symbol in (extra_symbols or []):
        symbol = str(symbol).strip().upper()
        if symbol and symbol not in pinned:
            pinned.append(symbol)
            if symbol not in names:
                names[symbol] = ASSET_NAMES.get(symbol, symbol)
                all_symbols.insert(0, symbol)
    rotating = [symbol for symbol in all_symbols if symbol not in pinned]
    if rotating:
        start = int(scan_offset or 0) % len(rotating)
        batch = [rotating[(start + i) % len(rotating)] for i in range(min(int(batch_size), len(rotating)))]
        next_offset = (start + len(batch)) % len(rotating)
    else:
        batch, next_offset = [], 0
    symbols_to_scan = list(dict.fromkeys(pinned + batch))

    adaptive_model = fit_adaptive_model(learning_trades or [], trading_horizon=trading_horizon)
    rows = []
    scanned_ok = 0
    for symbol in symbols_to_scan:
        try:
            raw = get_intraday_data(symbol, scan_interval, prepost=prepost)
            if raw is None or raw.empty or len(raw) < 30:
                continue
            enriched = add_indicators(raw, trading_horizon)
            daily = get_daily_stats(symbol)
            live_quote = get_fast_quote(symbol)
            stats = compute_price_targets_and_signal(enriched, live_quote, daily, scan_interval, rr_ratio, trading_horizon)
            side = stats["side"]
            if side not in {"LONG", "SHORT"} or int(stats["score"]) < 3:
                continue
            scanned_ok += 1
            current_price = float(stats["price"])
            entry_price = float(stats["ideal_buy"])
            target_price = float(stats["ideal_sell"])
            target_pct = ((target_price / max(entry_price, 0.000001)) - 1) * 100
            if side == "SHORT":
                target_pct = ((entry_price / max(target_price, 0.000001)) - 1) * 100
            day_change_pct = float(daily.get("change_pct", 0.0)) if daily else 0.0
            digits = price_decimals(current_price)
            features = directional_learning_features(stats, side)
            ai_probability = predict_adaptive_model(adaptive_model, features)
            rows.append({
                "Asset Name": names.get(symbol, display_asset_name(symbol)),
                "Symbol": symbol,
                "Asset Type": "Crypto" if symbol.endswith("-USD") else ("ETF" if symbol in names and "ETF" in names.get(symbol, "") else "Stock / ETF"),
                "Price": round(current_price, digits),
                "Today %": round(day_change_pct, 2),
                "Bias": "Bullish" if side == "LONG" else "Bearish",
                "Score": f'{stats["score"]}/5',
                "Target Price": round(target_price, digits),
                "Potential %": round(target_pct, 2),
                "Entry": round(entry_price, digits),
                "Stop": round(stats["stop"], digits),
                "RSI": round(stats["rsi"], 1),
                "AI Model": "Active · secondary ranking" if ai_probability is not None else "Learning",
                "_score": int(stats["score"]),
                "_reward_pct": float(target_pct),
                "_ai_probability": ai_probability if ai_probability is not None else 0.5,
                "_side": side
            })
        except Exception:
            continue
    rows.sort(key=lambda row: (row["_score"], row["_ai_probability"], row["_reward_pct"]), reverse=True)
    return {
        "rows": rows,
        "pool_size": len(all_symbols),
        "batch_size": len(symbols_to_scan),
        "next_offset": next_offset,
        "scanned_count": scanned_ok,
        "ai_active": bool(adaptive_model.get("active")),
    }

# ---------- Session State ----------
defaults = {
    "watchlist": ["SPY", "QQQ", "AAPL", "TSLA", "NVDA", "BTC-USD", "ETH-USD"],
    "active_ticker": "SPY",
    "paper_trades": [],
    "account_size": 25000.0,
    "daily_loss_limit": 300.0,
    "last_alert_action": None,
    "market_scan_cursor": 0,
    "recommendation_pool_size": 0,
    "ai_min_learning_samples": 20
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
    """Load intraday or longer-horizon Yahoo Finance candles."""
    period_by_interval = {
        "1m": "2d", "2m": "60d", "5m": "60d", "15m": "60d",
        "30m": "60d", "60m": "60d", "1d": "5y", "1wk": "10y", "1mo": "max",
    }
    if interval not in period_by_interval:
        raise ValueError(f"Unsupported chart interval: {interval}")
    is_intraday = interval in {"1m", "2m", "5m", "15m", "30m", "60m"}
    df = yf.download(
        ticker,
        period=period_by_interval[interval],
        interval=interval,
        prepost=bool(prepost) if is_intraday else False,
        progress=False,
        auto_adjust=True,
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

def add_indicators(df, trading_horizon="Day Trading"):
    """Add shared indicators; select trend markers appropriate to the holding horizon."""
    df = df.copy()
    typical = (df["High"] + df["Low"] + df["Close"]) / 3
    vol_clean = df["Volume"].replace(0, np.nan).fillna(1)
    df["TP_Vol"] = typical * vol_clean
    df["Date"] = df.index.date
    df["Cum_Vol"] = df.groupby("Date")["Volume"].cumsum().replace(0, np.nan)
    df["Cum_TP_Vol"] = df.groupby("Date")["TP_Vol"].cumsum()
    df["VWAP"] = (df["Cum_TP_Vol"] / df["Cum_Vol"]).fillna(df["Close"])

    for period in (9, 20, 50, 100, 200):
        df[f"EMA{period}"] = df["Close"].ewm(span=period, adjust=False).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["RSI"] = (100 - (100 / (1 + rs))).fillna(50.0)
    volume_window = 8 if trading_horizon == "Day Trading" else 20
    df["Vol_MA"] = df["Volume"].rolling(volume_window, min_periods=max(3, volume_window // 2)).mean()

    prev_close = df["Close"].shift(1)
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - prev_close).abs(),
        (df["Low"] - prev_close).abs()
    ], axis=1).max(axis=1)
    df["ATR"] = tr.ewm(alpha=1/14, min_periods=14, adjust=False).mean().fillna(df["Close"] * 0.003)

    if trading_horizon == "Day Trading":
        reference = df["VWAP"]
        fast, slow = df["EMA9"], df["EMA20"]
        slope_bars = 3
    elif trading_horizon == "Swing Trading":
        reference = df["EMA50"]
        fast, slow = df["EMA20"], df["EMA50"]
        slope_bars = 5
    else:
        slow_period = 200 if len(df) >= 205 else (100 if len(df) >= 105 else 50)
        fast_period = 50 if slow_period > 50 else 20
        reference = df[f"EMA{slow_period}"]
        fast, slow = df[f"EMA{fast_period}"], reference
        slope_bars = 10

    trend_slope = fast - fast.shift(slope_bars)
    above_reference = df["Close"] > reference
    below_reference = df["Close"] < reference
    trend_up = fast > slow
    trend_down = fast < slow
    rising_slope = trend_slope > 0
    falling_slope = trend_slope < 0
    vol_ma = df["Vol_MA"].fillna(df["Volume"].replace(0, np.nan).median()).fillna(1.0)
    volume_ok = df["Volume"] >= vol_ma * (0.85 if trading_horizon == "Day Trading" else 0.80)
    if trading_horizon == "Day Trading":
        long_confirm = df["Close"] > df["EMA9"]
        short_confirm = df["Close"] < df["EMA9"]
    else:
        long_confirm = rising_slope
        short_confirm = falling_slope
    df["Signal"] = "HOLD"
    df.loc[above_reference & trend_up & long_confirm & volume_ok & (df["RSI"] < 75), "Signal"] = "BUY"
    df.loc[below_reference & trend_down & short_confirm & volume_ok & (df["RSI"] > 25), "Signal"] = "SELL"
    return df


def compute_price_targets_and_signal(df, live_price, daily_stats, interval, rr_ratio, trading_horizon="Day Trading"):
    """Build horizon-aware 0–5 technical scores and ATR-based illustrative trade levels."""
    if df is None or df.empty:
        raise ValueError("No price candles available.")

    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else latest
    price = float(live_price) if live_price is not None and np.isfinite(live_price) else float(latest["Close"])
    if not np.isfinite(price) or price <= 0:
        raise ValueError("Latest price is invalid.")

    vwap = float(latest["VWAP"])
    rsi = float(latest["RSI"])
    atr = float(latest["ATR"])
    vol = float(latest["Volume"])
    vol_ma = float(latest["Vol_MA"]) if pd.notna(latest["Vol_MA"]) and latest["Vol_MA"] > 0 else max(vol, 1.0)
    atr = max(atr if np.isfinite(atr) else price * 0.003, price * 0.001)
    digits = price_decimals(price)
    recent = df.tail(45)
    swing_high = float(recent["High"].max())
    swing_low = float(recent["Low"].min())

    if trading_horizon == "Day Trading":
        reference_name, fast_name, slow_name = "VWAP", "EMA 9", "EMA 20"
        reference = float(latest["VWAP"])
        fast, slow = float(latest["EMA9"]), float(latest["EMA20"])
        fast_series = df["EMA9"]
        slope_bars = 3
        stop_multiple = 1.25
        volume_threshold = 0.85
        long_rsi_ok, short_rsi_ok = 40 < rsi < 70, 30 < rsi < 60
        reference_up, reference_down = price > reference, price < reference
        trend_up, trend_down = fast > slow, fast < slow
        reclaim_up = float(prev["Close"]) <= float(prev["VWAP"]) and price > reference
        reclaim_down = float(prev["Close"]) >= float(prev["VWAP"]) and price < reference
        long_confirm = reclaim_up or price > fast
        short_confirm = reclaim_down or price < fast
        long_entry = min(price, max(reference, min(fast, price)))
        short_entry = max(price, min(reference, max(fast, price)))
        basis_description = "session VWAP, EMA 9/20 alignment, price confirmation, volume and RSI"
    elif trading_horizon == "Swing Trading":
        reference_name, fast_name, slow_name = "EMA 50", "EMA 20", "EMA 50"
        reference = float(latest["EMA50"])
        fast, slow = float(latest["EMA20"]), float(latest["EMA50"])
        fast_series = df["EMA20"]
        slope_bars = 5
        stop_multiple = 1.75
        volume_threshold = 0.80
        long_rsi_ok, short_rsi_ok = 40 < rsi < 70, 30 < rsi < 60
        reference_up, reference_down = price > reference, price < reference
        trend_up, trend_down = fast > slow, fast < slow
        long_confirm = len(df) > slope_bars and fast > float(df["EMA20"].iloc[-1 - slope_bars])
        short_confirm = len(df) > slope_bars and fast < float(df["EMA20"].iloc[-1 - slope_bars])
        long_entry = min(price, max(reference, min(fast, price)))
        short_entry = max(price, min(reference, max(fast, price)))
        basis_description = "price versus EMA 50, EMA 20/50 alignment, trend slope, volume and RSI"
    else:
        slow_period = 200 if len(df) >= 205 else (100 if len(df) >= 105 else 50)
        fast_period = 50 if slow_period > 50 else 20
        reference_name, fast_name, slow_name = f"EMA {slow_period}", f"EMA {fast_period}", f"EMA {slow_period}"
        reference = float(latest[f"EMA{slow_period}"])
        fast, slow = float(latest[f"EMA{fast_period}" ]), reference
        fast_series = df[f"EMA{fast_period}"]
        slope_bars = 10
        stop_multiple = 2.25
        volume_threshold = 0.75
        long_rsi_ok, short_rsi_ok = 42 < rsi < 72, 28 < rsi < 58
        reference_up, reference_down = price > reference, price < reference
        trend_up, trend_down = fast > slow, fast < slow
        long_confirm = len(df) > slope_bars and fast > float(fast_series.iloc[-1 - slope_bars])
        short_confirm = len(df) > slope_bars and fast < float(fast_series.iloc[-1 - slope_bars])
        long_entry = min(price, max(reference, min(fast, price)))
        short_entry = max(price, min(reference, max(fast, price)))
        basis_description = f"price versus {reference_name}, EMA {fast_period}/{slow_period} alignment, long trend slope, volume and RSI"

    vol_ratio = vol / max(vol_ma, 1.0)
    vol_ok = vol_ratio >= volume_threshold
    fast_prior = float(fast_series.iloc[-1 - slope_bars]) if len(fast_series) > slope_bars else fast
    trend_slope_pct = ((fast - fast_prior) / max(abs(fast_prior), 1e-9)) * 100.0
    slope_up = trend_slope_pct > 0
    slope_down = trend_slope_pct < 0

    long_score = int(reference_up) + int(trend_up) + int(long_confirm) + int(vol_ok) + int(long_rsi_ok)
    short_score = int(reference_down) + int(trend_down) + int(short_confirm) + int(vol_ok) + int(short_rsi_ok)

    stop_dist = max(atr * stop_multiple, price * (0.0025 if trading_horizon == "Day Trading" else 0.005))
    long_stop = round(max(0.000001, long_entry - stop_dist), digits)
    short_stop = round(short_entry + stop_dist, digits)
    long_target = round(long_entry + stop_dist * float(rr_ratio), digits)
    short_target = round(max(0.000001, short_entry - stop_dist * float(rr_ratio)), digits)

    if long_score >= 4 and long_score > short_score and (trading_horizon != "Day Trading" or price <= long_entry + atr * 0.35):
        if trading_horizon == "Day Trading":
            action = "🚀 BUY NOW (STRONG SETUP)"
        elif trading_horizon == "Swing Trading":
            action = "🟢 SWING BUY SETUP"
        else:
            action = "🟢 LONG-TERM BULLISH SETUP"
        reasons = [
            f"Long-side score is {long_score}/5 using {basis_description}.",
            f"{fast_name} is above {slow_name} and the trend slope is {'rising' if slope_up else 'not rising'}.",
            f"Illustrative long target ${long_target:,.{digits}f}; stop ${long_stop:,.{digits}f}."
        ]
        side, score = "LONG", long_score
        ideal_buy, stop, ideal_sell = round(long_entry, digits), long_stop, long_target
    elif short_score >= 4 and short_score > long_score:
        if trading_horizon == "Day Trading":
            action = "🔻 SHORT / SELL NOW"
        elif trading_horizon == "Swing Trading":
            action = "🔻 SWING SHORT SETUP"
        else:
            action = "🔻 LONG-TERM BEARISH SETUP"
        reasons = [
            f"Short-side score is {short_score}/5 using {basis_description}.",
            f"{fast_name} is below {slow_name} and the trend slope is {'falling' if slope_down else 'not falling'}.",
            f"Illustrative short target ${short_target:,.{digits}f}; stop ${short_stop:,.{digits}f}."
        ]
        side, score = "SHORT", short_score
        ideal_buy, stop, ideal_sell = round(short_entry, digits), short_stop, short_target
    elif long_score >= 3 and long_score > short_score:
        action = f"⏳ WAIT FOR LONG ENTRY NEAR ${long_entry:,.{digits}f}"
        reasons = [f"Bullish conditions are developing ({long_score}/5), but all confirmation checks are not aligned yet.", f"Watch the reference trend area near ${reference:,.{digits}f}."]
        side, score = "LONG", long_score
        ideal_buy, stop, ideal_sell = round(long_entry, digits), long_stop, long_target
    elif short_score >= 3 and short_score > long_score:
        action = f"⏳ WAIT FOR SHORT ENTRY NEAR ${short_entry:,.{digits}f}"
        reasons = [f"Bearish conditions are developing ({short_score}/5), but all confirmation checks are not aligned yet.", f"Watch the reference trend area near ${reference:,.{digits}f}."]
        side, score = "SHORT", short_score
        ideal_buy, stop, ideal_sell = round(short_entry, digits), short_stop, short_target
    else:
        action = "🛡️ WAIT (NO CLEAR SETUP)"
        reasons = [f"Trend, price position, volume and momentum are not sufficiently aligned for {trading_horizon.lower()}.", f"The selected reference is {reference_name} at ${reference:,.{digits}f}; wait for a clearer move."]
        side, score = "None", max(long_score, short_score)
        ideal_buy, stop, ideal_sell = round(price, digits), round(max(0.000001, price - stop_dist), digits), round(price + stop_dist * float(rr_ratio), digits)

    bias_mult = 1.0 if (reference_up and trend_up) else (-1.0 if (reference_down and trend_down) else 0.0)
    interval_minutes = {"1m": 1, "2m": 2, "5m": 5, "15m": 15, "30m": 30, "60m": 60, "1d": 390, "1wk": 1950, "1mo": 8190}.get(interval, 1)
    if trading_horizon == "Day Trading":
        projection_one_label, projection_two_label = "1H Projection", "Daily Projection"
        projection_one_minutes, projection_two_minutes = 60, 390
    elif trading_horizon == "Swing Trading":
        projection_one_label, projection_two_label = "1-Week Projection", "1-Month Projection"
        projection_one_minutes, projection_two_minutes = 1950, 8190
    else:
        projection_one_label, projection_two_label = "1-Month Projection", "3-Month Projection"
        projection_one_minutes, projection_two_minutes = 8190, 24570

    projection_one_move = atr * np.sqrt(max(1.0, projection_one_minutes / interval_minutes)) * 0.55
    projection_two_move = atr * np.sqrt(max(1.0, projection_two_minutes / interval_minutes)) * 0.55
    projection_one_target = round(price + projection_one_move * bias_mult, digits)
    projection_two_target = round(price + projection_two_move * bias_mult, digits)

    if daily_stats:
        d_atr = max(float(daily_stats["daily_atr"]), 0.0)
        anchor = float(daily_stats["today_open"])
        daily_range = (round(anchor - d_atr * 0.75, digits), round(anchor + d_atr * 0.75, digits))
    else:
        daily_range = (round(swing_low, digits), round(swing_high, digits))

    reference_gap_pct = ((price - reference) / max(abs(price), 1e-9)) * 100.0
    trend_spread_pct = ((fast - slow) / max(abs(price), 1e-9)) * 100.0
    ema9, ema20 = float(latest["EMA9"]), float(latest["EMA20"])
    return {
        "action": action, "reasons": reasons, "side": side, "score": score,
        "price": price, "vwap": vwap, "rsi": rsi,
        "ideal_buy": ideal_buy, "ideal_sell": ideal_sell, "stop": stop,
        "stop_dist": abs(ideal_buy - stop),
        "hourly_target": projection_one_target, "daily_target": projection_two_target,
        "projection_one_target": projection_one_target, "projection_two_target": projection_two_target,
        "projection_one_label": projection_one_label, "projection_two_label": projection_two_label,
        "daily_range": daily_range, "long_score": long_score, "short_score": short_score,
        "vwap_gap_pct": ((price - vwap) / max(abs(price), 1e-9)) * 100.0,
        "ema_spread_pct": ((ema9 - ema20) / max(abs(price), 1e-9)) * 100.0,
        "reference_gap_pct": reference_gap_pct, "trend_spread_pct": trend_spread_pct,
        "trend_slope_pct": trend_slope_pct, "trend_bullish": bool(trend_up),
        "trend_fast": fast, "trend_slow": slow,
        "trend_fast_name": fast_name, "trend_slow_name": slow_name,
        "reference_price": reference, "reference_name": reference_name,
        "horizon": trading_horizon, "volume_ratio": vol_ratio,
        "above_vwap": bool(price > vwap), "ema_bullish": bool(trend_up),
        "price_above_ema9": bool(price > ema9), "price_above_trend_fast": bool(price > fast),
    }

def get_higher_tf_bias(ticker, prepost, trend_interval="15m", trading_horizon="Day Trading"):
    """Compare trend averages on the separately selected confirmation interval."""
    try:
        df = get_intraday_data(ticker, trend_interval, prepost=prepost)
        if df is None or df.empty or len(df) < 25:
            return "Not enough data"
        df = add_indicators(df, trading_horizon)
        latest = df.iloc[-1]
        if trading_horizon == "Day Trading":
            fast, slow = float(latest["EMA9"]), float(latest["EMA20"])
        elif trading_horizon == "Swing Trading":
            fast, slow = float(latest["EMA20"]), float(latest["EMA50"])
        else:
            slow_period = 200 if len(df) >= 205 else (100 if len(df) >= 105 else 50)
            fast_period = 50 if slow_period > 50 else 20
            fast, slow = float(latest[f"EMA{fast_period}"]), float(latest[f"EMA{slow_period}"])
        if fast > slow:
            return "🟢 Bullish (Up)"
        if fast < slow:
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
        info_heading("⭐ Top Market Candidates", "Automatically refreshed ideas from a broad Yahoo Finance stock/ETF screener plus crypto discovery. It uses the selected trading horizon and rotates through symbols in batches; it cannot process every global listing simultaneously.", 3)
    else:
        info_heading("⭐ Top Market Candidates", "Automatically refreshed ideas from a broad Yahoo Finance stock/ETF screener plus crypto discovery. The scanner uses the selected trading horizon and rotates through symbols in batches; target distances are scenarios, not forecasts.", 2)

    if st.button("↻ Refresh candidates", key="top_candidate_refresh", use_container_width=True):
        st.session_state["recommendation_force_refresh"] = True

    scan_interval = {"Day Trading": "15m", "Swing Trading": "1d", "Long-Term Investing": "1wk"}.get(trading_horizon, "15m")
    if st.session_state.get("recommendation_horizon") != trading_horizon:
        st.session_state["recommendation_rows"] = []
        st.session_state["recommendation_future"] = None
        st.session_state["recommendation_requested_at"] = 0.0
        st.session_state["recommendation_horizon"] = trading_horizon

    future = st.session_state.get("recommendation_future")
    requested_at = st.session_state.get("recommendation_requested_at", 0.0)
    now_ts = datetime.now().timestamp()
    force_refresh = st.session_state.pop("recommendation_force_refresh", False)

    if force_refresh:
        # Do not discard the last completed list; it remains visible while the new scan runs.
        future = None

    if future is None or (future.done() and now_ts - requested_at >= 300):
        pinned_symbols = list(dict.fromkeys(
            list(st.session_state.get("watchlist", [])) + [st.session_state.get("active_ticker", "SPY")]
        ))
        learning_snapshot = [dict(t) for t in st.session_state.get("paper_trades", []) if isinstance(t, dict)]
        future = get_market_scan_executor().submit(
            scan_recommendation_candidates, scan_interval, False, 1.8,
            pinned_symbols, learning_snapshot,
            int(st.session_state.get("market_scan_cursor", 0)), 30, trading_horizon
        )
        st.session_state["recommendation_future"] = future
        st.session_state["recommendation_requested_at"] = now_ts

    if future.done():
        try:
            scan_result = future.result()
            if isinstance(scan_result, dict):
                rows = scan_result.get("rows", [])
                st.session_state["market_scan_cursor"] = scan_result.get("next_offset", 0)
                st.session_state["recommendation_pool_size"] = scan_result.get("pool_size", 0)
                st.session_state["recommendation_batch_size"] = scan_result.get("batch_size", 0)
                st.session_state["recommendation_scanned_count"] = scan_result.get("scanned_count", 0)
                st.session_state["recommendation_ai_active"] = scan_result.get("ai_active", False)
            else:
                rows = scan_result or []
            st.session_state["recommendation_rows"] = rows
            st.session_state["recommendation_scan_time"] = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %I:%M:%S %p ET")
            st.session_state["recommendation_last_error"] = None
        except Exception as exc:
            st.session_state["recommendation_last_error"] = str(exc)

    # Older session-state entries may predate the Asset Name / Asset Type fields.
    # Normalize at display time so deployments and browser sessions do not crash.
    candidates = [normalize_candidate_row(row) for row in st.session_state.get("recommendation_rows", [])]
    st.session_state["recommendation_rows"] = candidates
    # Preserve full names for assets discovered dynamically so later panels use them too.
    ASSET_NAMES.update({row["Symbol"]: row["Asset Name"] for row in candidates})
    scan_time = st.session_state.get("recommendation_scan_time")
    if scan_time:
        st.caption(f"Updated {scan_time}")
    pool_size = int(st.session_state.get("recommendation_pool_size", 0) or 0)
    if pool_size:
        st.caption(
            f"Market universe: {pool_size:,} discovered symbols · "
            f"{int(st.session_state.get('recommendation_batch_size', 0) or 0)} watched/scanned this pass · "
            "remaining symbols rotate into later scans."
        )
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
            today_pct_label = f"{float(row['Today %']):+.2f}% today"
            target_pct_label = f"{float(row['Potential %']):+.2f}% target move"
            target_move = float(row["Target Price"]) - float(row["Entry"])
            st.markdown(
                f'<div style="padding:8px 9px;margin:5px 0;border:1px solid #293b52;border-radius:8px;background:#111d2b">'
                f'<div style="font-weight:750;color:#f0f6ff;line-height:1.25">{tint} {row["Asset Name"]}</div>'
                f'<div style="display:flex;justify-content:space-between;gap:8px;margin-top:3px"><b style="color:#8ed8ff">{row["Symbol"]}</b><b>${row["Price"]:,.{digits}f}</b></div>'
                f'<div style="color:#aeb8c8;font-size:12px;margin-top:4px">{row["Asset Type"]} · {row["Bias"]} · Score {row["Score"]}</div>'
                f'{percentage_indicator_html(row["Today %"], label=today_pct_label)}'
                f'{percentage_indicator_html(row["Potential %"], movement=target_move, label=target_pct_label)}</div>',
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
        bullish_df = pd.DataFrame(bullish[:8]).drop(columns=["_score", "_reward_pct", "_ai_probability", "_side"], errors="ignore")
        for col in ["Price", "Target Price", "Entry", "Stop"]:
            bullish_df[col] = bullish_df[col].map(lambda value: f"${float(value):,.{price_decimals(value)}f}")
        bullish_df = bullish_df.rename(columns={"Price": "Current Price", "Today %": "Day Change %", "Target Price": "Target Price", "Potential %": "Target Distance %", "Entry": "Entry Area"})
        bullish_df["Day Change %"] = bullish_df["Day Change %"].map(lambda value: f"{percentage_direction(value)['icon']} {float(value):+.2f}%")
        bullish_df["Target Distance %"] = [
            f"{percentage_direction(float(row['Target Price'].replace('$', '').replace(',', '')) - float(row['Entry Area'].replace('$', '').replace(',', '')))['icon']} {float(value):+.2f}%"
            for (_, row), value in zip(bullish_df.iterrows(), bullish_df["Target Distance %"])
        ]
        st.dataframe(bullish_df, use_container_width=True, hide_index=True)
    else:
        st.info("No bullish candidates currently meet the scanner's minimum technical score.")
    if bearish:
        with st.expander("🔻 Bearish / short candidates", expanded=False):
            bearish_df = pd.DataFrame(bearish[:6]).drop(columns=["_score", "_reward_pct", "_ai_probability", "_side"], errors="ignore")
            for col in ["Price", "Target Price", "Entry", "Stop"]:
                bearish_df[col] = bearish_df[col].map(lambda value: f"${float(value):,.{price_decimals(value)}f}")
            bearish_df = bearish_df.rename(columns={"Price": "Current Price", "Today %": "Day Change %", "Target Price": "Target Price", "Potential %": "Target Distance %", "Entry": "Entry Area"})
            bearish_df["Day Change %"] = bearish_df["Day Change %"].map(lambda value: f"{percentage_direction(value)['icon']} {float(value):+.2f}%")
            bearish_df["Target Distance %"] = [
                f"{percentage_direction(float(row['Target Price'].replace('$', '').replace(',', '')) - float(row['Entry Area'].replace('$', '').replace(',', '')))['icon']} {float(value):+.2f}%"
                for (_, row), value in zip(bearish_df.iterrows(), bearish_df["Target Distance %"])
            ]
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
    trading_horizon = st.selectbox(
        "Trading Horizon",
        ["Day Trading", "Swing Trading", "Long-Term Investing"],
        index=0,
        key="trading_horizon",
        help="Day Trading is the default. Swing Trading looks at multi-day moves. Long-Term Investing checks weekly/monthly trends. The selected horizon changes chart intervals, indicators, stops, targets and candidate scanning."
    )
    horizon_explainer = {
        "Day Trading": "Day Trading · minutes to hours · 1m–1h charts",
        "Swing Trading": "Swing Trading · several days to a few weeks · 30m–1wk charts",
        "Long-Term Investing": "Long-Term Investing · weeks to months or longer · daily, weekly and monthly charts",
    }
    st.caption(horizon_explainer[trading_horizon])

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
    horizon_timeframes = {
        "Day Trading": {
            "chart": ["1m", "2m", "5m", "15m", "30m", "60m"], "chart_default": "1m",
            "confirm": ["5m", "15m", "30m", "60m", "1d"], "confirm_default": "15m",
        },
        "Swing Trading": {
            "chart": ["30m", "60m", "1d", "1wk"], "chart_default": "1d",
            "confirm": ["1d", "1wk", "1mo"], "confirm_default": "1wk",
        },
        "Long-Term Investing": {
            "chart": ["1d", "1wk", "1mo"], "chart_default": "1wk",
            "confirm": ["1wk", "1mo"], "confirm_default": "1mo",
        },
    }
    active_timeframes = horizon_timeframes[trading_horizon]
    timeframe_options = active_timeframes["chart"]
    trend_options = active_timeframes["confirm"]
    interval = st.selectbox(
        "Chart Timeframe", timeframe_options,
        index=timeframe_options.index(active_timeframes["chart_default"]),
        key=f"chart_timeframe_{trading_horizon.replace(' ', '_')}",
        format_func=lambda value: "1h (60m)" if value == "60m" else value,
        help="Each candle covers this amount of time. Day trading uses minute charts; swing and long-term modes add daily, weekly and monthly candles."
    )
    trend_interval = st.selectbox(
        "Trend Confirmation Timeframe", trend_options,
        index=trend_options.index(active_timeframes["confirm_default"]),
        key=f"trend_timeframe_{trading_horizon.replace(' ', '_')}",
        format_func=lambda value: "1h (60m)" if value == "60m" else value,
        help="A second, broader chart interval used to see whether the main trend agrees with the selected trading horizon."
    )
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

        df = add_indicators(df_raw, trading_horizon)
        fast_px = get_fast_quote(ticker)
        daily_stats = get_daily_stats(ticker)
        sig = compute_price_targets_and_signal(df, fast_px, daily_stats, interval, rr_ratio, trading_horizon)

        price = sig["price"]
        
        confirmed_horizon_signal = (
            sig.get("score", 0) >= 4
            and sig.get("side") in {"LONG", "SHORT"}
            and "WAIT" not in str(sig.get("action", "")).upper()
        )
        if confirmed_horizon_signal:
            alert_key = f"{trading_horizon}:{sig['action']}"
            if st.session_state.last_alert_action != alert_key:
                st.toast(f"🚨 {trading_horizon} alert: {sig['action']} on {ticker} @ ${price:,.{price_decimals(price)}f}!", icon="⚡")
                st.session_state.last_alert_action = alert_key

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
        st.caption(f"{trading_horizon}  •  Chart: {interval}  •  Trend confirmation: {'1h' if trend_interval == '60m' else trend_interval}")
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
        reference_help = "Volume-weighted average price for the current trading session." if trading_horizon == "Day Trading" else f"The {sig['reference_name']} is a smoothed price average used as the broader trend reference for this horizon."
        c2.metric(f"{sig['reference_name']} Reference", f"${sig['reference_price']:,.{ticker_digits}f}", help=reference_help)
        c3.metric("RSI (Momentum)", f"{sig['rsi']:.0f}", help="A speed gauge for recent price moves. It can stay high or low while a strong trend continues.")
        c4, c5 = st.columns(2)
        c4.metric("Setup Score", f"{sig['score']}/5", help="How many of the five technical checks are met. This is not a probability of success.")
        trend_bias = get_higher_tf_bias(ticker, include_247, trend_interval, trading_horizon)
        c5.metric(
            f"{'1h' if trend_interval == '60m' else trend_interval} Trend",
            trend_bias,
            help=f"{trading_horizon} trend-average confirmation on the selected {trend_interval} timeframe."
        )

        # The local model learns only from closed paper trades with an entry-time snapshot.
        adaptive_model = fit_adaptive_model(st.session_state.get("paper_trades", []), min_samples=20, trading_horizon=trading_horizon)
        reward_assessment = build_reward_assessment(sig, adaptive_model, trend_bias, rr_ratio)
        info_heading(
            f"🧠 AI Analysis — {asset_name} ({ticker})",
            "The technical-alignment percentage is the number of rule checks that agree, divided by five. It is not the chance of making money. Potential reward is the planned price move from entry to target, not a win probability.",
            3,
        )
        ai_c1, ai_c2, ai_c3 = st.columns(3)
        alignment_pct = float(reward_assessment.get("technical_alignment_pct", 0.0))
        checks_passed = int(reward_assessment.get("checks_passed", 0))
        if reward_assessment["side"] == "MIXED":
            ai_c1.metric(
                "Directional Assessment", "Mixed",
                f"Long {sig['long_score']}/5 · Short {sig['short_score']}/5",
                help="Bullish and bearish checks are tied, so the app does not favor a direction."
            )
            ai_c2.metric("Potential Reward to Target", "—", help="No single direction is favored, so no directional target reward is presented.")
            ai_c2.markdown(percentage_indicator_html(0, movement=0, label="→ Waiting for clearer direction"), unsafe_allow_html=True)
            ai_c3.metric(
                "Technical Alignment", f"{alignment_pct:.0f}%",
                f"{checks_passed} of 5 checks on each side",
                help="Share of the five technical checks that pass for each tied side. This is not a probability of profit."
            )
            ai_c3.markdown(percentage_indicator_html(alignment_pct, movement=0, label=f"→ {checks_passed}/5 checks · no directional edge"), unsafe_allow_html=True)
        else:
            side_label = "Bullish / Long" if reward_assessment["side"] == "LONG" else "Bearish / Short"
            ai_c1.metric("AI Technical Assessment", reward_assessment["label"], f"{side_label} · {checks_passed}/5 checks")
            ai_c2.metric(
                "Potential Reward to Target",
                f"+{reward_assessment['potential_reward_pct']:.2f}%" if reward_assessment.get("potential_reward_pct") is not None else "—",
                help="Favorable price distance from the planned entry to target. Positive for both LONG and SHORT plans. It is not the chance that the target will be reached.",
            )
            ai_move_sign = 1 if reward_assessment.get("side") == "LONG" else -1
            if reward_assessment.get("potential_reward_pct") is not None:
                ai_c2.markdown(
                    percentage_indicator_html(
                        reward_assessment["potential_reward_pct"],
                        movement=ai_move_sign * reward_assessment["potential_reward_pct"],
                        label=f"+{reward_assessment['potential_reward_pct']:.2f}% target reward · "
                              f"risk {reward_assessment['risk_pct']:.2f}% · {reward_assessment['reward_to_risk']:.2f}:1 reward/risk",
                    ),
                    unsafe_allow_html=True,
                )
            ai_c3.metric(
                "Technical Alignment", f"{alignment_pct:.0f}%",
                f"{checks_passed} of 5 checks support {side_label}",
                help="This is a simple count of the five technical checks that agree with the selected direction. It is not a win probability or forecast.",
            )
            ai_c3.markdown(
                percentage_indicator_html(
                    alignment_pct,
                    movement=ai_move_sign * alignment_pct,
                    label=f"{('↑' if ai_move_sign > 0 else '↓')} {alignment_pct:.0f}% technical checks aligned",
                ),
                unsafe_allow_html=True,
            )
        with st.expander("Why the AI assessment looks this way", expanded=True):
            if reward_assessment["side"] == "MIXED":
                st.info("Bullish and bearish technical checks are tied. Waiting for alignment is more informative than forcing a direction.")
            else:
                for reason in reward_assessment["reasons"]:
                    st.markdown(f"- {reason}")
            if not adaptive_model.get("active"):
                st.caption(
                    f"Paper-history model is learning: {adaptive_model['sample_count']}/{adaptive_model['min_samples']} "
                    "eligible closed paper trades. The technical-alignment percentage above is calculated from the five rule checks and does not depend on this model."
                )
            else:
                past_rate = adaptive_model.get("win_rate")
                rate_text = f" Historical paper win rate: {past_rate * 100:.1f}%." if past_rate is not None else ""
                st.caption(
                    f"Paper-history model has {adaptive_model['sample_count']} closed examples.{rate_text} "
                    "That win rate describes previous practice trades only; the model does not produce a calibrated probability for this setup."
                )

        adaptive_side = "LONG" if sig["long_score"] >= sig["short_score"] else "SHORT"
        with st.expander("🧠 Adaptive AI Strategy Assistant — model details", expanded=False):
            info_heading(
                "Learns from your paper-trading results",
                "A small local machine-learning model learns patterns from closed simulated trades you made in this session. It does not place orders, retrain on live market outcomes, or guarantee accuracy.",
                4,
            )
            ai_a, ai_b, ai_c = st.columns(3)
            ai_a.metric("Learning Trades", f"{adaptive_model['sample_count']}/{adaptive_model['min_samples']}")
            ai_b.metric("Your Recorded Win Rate", f"{adaptive_model['win_rate'] * 100:.1f}%" if adaptive_model.get("win_rate") is not None else "—")
            ai_c.metric("Model Status", "Learning" if not adaptive_model.get("active") else "Active")
            if not adaptive_model.get("active"):
                render_terminal_notice(
                    "The model is still learning. Close at least 20 paper trades with saved signal snapshots and include both wins and losses. "
                    "Until then, candidate ordering uses the visible technical score and target distance.",
                    kind="learning",
                )
            else:
                st.info(
                    "The paper-history model is active as a secondary candidate-ranking helper when technical scores tie. "
                    "Its raw model output is not shown as a percentage because it has not been independently calibrated as a win probability."
                )
                st.caption("The model updates on the next dashboard refresh after you close additional paper trades. It only adjusts candidate ordering when technical scores tie; the underlying signal rules remain visible and unchanged. Use it as extra research, not as an automatic trading instruction.")
            st.caption("Learning data stays in this Streamlit session. Restarting/clearing the session can remove the history; use the paper journal CSV export to keep a record.")

        if dash_mode == "Advanced (Pro)":
            info_heading("🔬 Advanced Pro Telemetry", "Additional technical readings: ATR measures volatility, volume versus average compares activity, and EMA spread shows trend separation.", 5)
            ac1, ac2, ac3, ac4 = st.columns(4)
            ac1.metric("ATR (Volatility)", f"${df.iloc[-1]['ATR']:,.{ticker_digits}f}", help="Average True Range measures how much the stock typically moves per candle.")
            ac2.metric("Volume vs MA", f"{df.iloc[-1]['Volume'] / max(df.iloc[-1]['Vol_MA'], 1):.2f}x", help="Current volume compared to its 8-period average. Higher means stronger interest.")
            ac3.metric(f"{sig['trend_fast_name']} / {sig['trend_slow_name']} Spread", f"${sig['trend_fast'] - sig['trend_slow']:+,.{ticker_digits}f}", help="Distance between the two trend averages used for the selected trading horizon.")
            ac4.metric("Recent High / Low", f"${df.tail(45)['High'].max():,.{ticker_digits}f} / ${df.tail(45)['Low'].min():,.{ticker_digits}f}", help="Highest and lowest prices in the most recent 45 candles on the selected timeframe.")

        info_heading("🎯 Live Price Targets & Trade Zones", "Entry gap is measured from the current quote. Target reward and stop risk are measured from the planned entry; reward stays positive for a valid SHORT target below entry.", 4)
        price_plan_side = sig["side"] if sig.get("side") in {"LONG", "SHORT"} else ("LONG" if sig["long_score"] >= sig["short_score"] else "SHORT")
        price_plan = build_quick_trade_plan(
            sig, price, max(float(sig["stop_dist"]), price * 0.0025, 0.000001),
            rr_ratio, price_plan_side, ticker_digits
        )
        price_pcts = calculate_directional_percentages(
            price, price_plan["entry"], price_plan["stop"], price_plan["target"], price_plan_side
        )
        t1, t2, t3 = st.columns(3)
        t1.metric(
            f"Planned Entry ({price_plan_side})",
            f"${price_plan['entry']:,.{ticker_digits}f}",
            help="The entry level for the stronger current technical side. The percentage compares this entry price with the latest quote; negative means below the quote and positive means above it."
        )
        t1.markdown(percentage_indicator_html(price_pcts["entry_vs_current_pct"], label=f"{price_pcts['entry_vs_current_pct']:+.2f}% vs current"), unsafe_allow_html=True)
        t2.metric(
            "Profit Target",
            f"${price_plan['target']:,.{ticker_digits}f}",
            help="Favorable percentage move from planned entry to target. It is positive for both LONG and SHORT plans and is not a probability of reaching the target."
        )
        t2.markdown(percentage_indicator_html(price_pcts["reward_pct"], movement=price_plan["target"] - price_plan["entry"], label=f"+{price_pcts['reward_pct']:.2f}% potential reward"), unsafe_allow_html=True)
        t3.metric(
            "Stop Loss",
            f"${price_plan['stop']:,.{ticker_digits}f}",
            help="Adverse percentage move from planned entry to stop. The estimated loss also depends on position size and can differ from real fills."
        )
        t3.markdown(percentage_indicator_html(-price_pcts["risk_pct"], movement=price_plan["stop"] - price_plan["entry"], label=f"-{price_pcts['risk_pct']:.2f}% planned risk"), unsafe_allow_html=True)
        h1, h2 = st.columns(2)
        projection_one = float(sig["projection_one_target"])
        projection_two = float(sig["projection_two_target"])
        projection_one_pct = directional_price_move_pct(price, projection_one, price_plan_side)
        projection_two_pct = directional_price_move_pct(price, projection_two, price_plan_side)
        projection_help = "Volatility-based scenario using the selected chart interval and recent ATR. It is a planning reference, not a price forecast."
        h1.metric(
            sig["projection_one_label"], f"${projection_one:,.{ticker_digits}f}",
            help=projection_help
        )
        h1.markdown(percentage_indicator_html(projection_one_pct, movement=projection_one - price, label=f"{projection_one_pct:+.2f}% favorable-side scenario"), unsafe_allow_html=True)
        h2.metric(
            sig["projection_two_label"], f"${projection_two:,.{ticker_digits}f}",
            help=f"Longer-range volatility scenario. Recent daily reference range: ${sig['daily_range'][0]:,.{ticker_digits}f} to ${sig['daily_range'][1]:,.{ticker_digits}f}. This is not a forecast."
        )
        h2.markdown(percentage_indicator_html(projection_two_pct, movement=projection_two - price, label=f"{projection_two_pct:+.2f}% favorable-side scenario"), unsafe_allow_html=True)
        st.caption("Arrow guide: ↑ price/return moving up · ↓ moving down · → nearly flat (within 0.05%). A ↓ arrow can still show a positive reward on a SHORT plan. Win-rate and AI percentages describe past patterns, not future certainty.")
        if sig.get("side") == "None":
            st.caption("No confirmed directional setup. The entry/stop/target values above are a reference plan based on the stronger score, not a trade signal.")

        info_heading("💡 Why this setup?", "A short explanation of which technical checks are supporting or weakening the current signal.", 4)
        for r in sig["reasons"]:
            st.markdown(f"- {r}")

        # The glossary changes with the experience-level switch, so terms gain depth in Pro mode.
        if dash_mode == "Beginner (Simple)":
            with st.expander("👶 Beginner's Guide: Plain-English definitions", expanded=False):
                st.markdown("""
- **Ticker / Symbol**: A short name for a stock or coin. AAPL means Apple; BTC-USD means Bitcoin priced in US dollars.
- **Current Price**: The latest price the app can find. It may be delayed, so it might not be the exact price you could trade at.
- **Candle**: One bar on the chart. It shows where price started, where it went, and where it finished during that time.
- **Timeframe**: How long each candle covers. A 5-minute chart makes one candle every five minutes; a weekly chart makes one candle for a week.
- **Day trading**: Buying and selling within the same day, usually using minute charts.
- **Swing trading**: Holding a trade for a few days or weeks while trying to catch a larger price move.
- **Long-term investing**: Holding a stock or coin for months or years, and focusing on the bigger trend instead of every small price change. Day Trading stays the default; you can switch horizons in the sidebar.
- **VWAP**: An average price for the session that gives more weight to times when more shares or coins traded. Price above it can mean buyers are stronger; below it can mean sellers are stronger.
- **RSI**: A speed gauge for price moves. A high reading means price has risen quickly; a low reading means it has fallen quickly. It does not tell you exactly when price will turn.
- **EMA 9 / EMA 20**: Two smooth lines on the chart. The 9 line reacts faster. If it is above the 20 line, the recent move is leaning upward.
- **ATR**: A guide to how much the price usually moves. A bigger ATR means bigger swings; it does not say whether price will rise or fall.
- **Volume**: How many shares or coins were traded. More volume means more trading activity.
- **Volume vs. Average**: Compares today's candle volume with its usual amount. Above 1.0x means more activity than average.
- **Setup Score (0–5)**: Counts how many of the app's five checks agree. A score of 4 does not mean an 80% chance of winning.
- **Trend Confirmation**: Checks a second chart timeframe to see whether it points in the same direction.
- **Trading Horizon**: Tells the app whether to focus on day trades, multi-day swing trades or longer-term positions. It changes the chart interval, moving averages, stop distance and target windows.
- **LONG / Paper BUY**: A practice trade that makes money if the price goes up, before costs.
- **SHORT / Paper SHORT**: A practice trade that makes money if the price goes down, before costs. Real short selling can have extra costs and risks.
- **Entry Price**: The price where the practice trade starts.
- **Stop Loss**: The price where you plan to exit if the trade goes against you. A real trade may fill at a different price.
- **Take Profit / Target**: The price where you plan to take the gain if the trade moves your way.
- **Entry % vs. Current**: How far the planned entry is from the price shown now. The arrow shows whether that entry is higher, lower or about the same.
- **Potential Reward %**: How far the target is from the entry, as a percentage. This shows the size of the possible move, not the chance it will happen.
- **Stop Risk %**: How far the stop is from the entry, as a percentage. Your dollar loss also depends on how many shares or coins you hold.
- **Reward-to-Risk (R/R)**: Compares the possible gain with the planned loss. 2:1 means the target is twice as far from entry as the stop is.
- **Position Size**: How many shares or coins the calculator suggests for the risk setting you chose.
- **Risk Per Trade**: The amount of your practice account you are willing to risk on one trade if the stop is reached.
- **Paper Trading**: Practice trading with pretend money. It does not send an order to a broker.
- **Paper Account Balance**: The pretend money you start with in the practice account.
- **Portfolio Equity**: Your paper balance after adding the results of closed trades and the current estimated results of open trades.
- **Realized P&L**: The profit or loss from practice trades you have closed.
- **Unrealized P&L**: The estimated profit or loss on trades that are still open. It can change as the price moves.
- **Win Rate**: The percentage of closed practice trades that made money. A break-even trade is still included in the total number of trades.
- **Trade Return %**: How big the gain or loss was compared with the amount used to open that practice trade.
- **Technical Alignment %**: How many of the five chart checks agree with the current direction. For example, 4 out of 5 checks is 80%. This is not an 80% chance of winning.
- **Paper-History Model**: A helper that looks for patterns in finished practice trades and can help sort similar candidates. It does not predict the chance that the next trade will win.
- **Crypto Pair**: A coin's price compared with another currency. BTC-USD is the Bitcoin price in US dollars. Crypto markets run all day and night.
- **BUY / SELL Marker**: A chart label showing where the app's rules first changed to a buy or sell signal. It is a signal from the rules, not a promise about what price will do next.
- **Up / Down / Neutral icon**: Up means the measured price or return is rising; down means it is falling; sideways means the move is very small (less than 0.05%).
                """)
        else:
            with st.expander("📘 Advanced Reference: Definitions & Methodology", expanded=False):
                st.markdown("""
- **VWAP**: Plain meaning: the average price traded during the current session, giving more weight to busy periods. Technical detail: cumulative typical price × volume ÷ cumulative volume; it is mainly used in day trading and is not intrinsic value.
- **RSI (14)**: Plain meaning: a gauge of how quickly price has been moving. Technical detail: smoothed average gains versus losses, scaled from 0–100; 70/30 are guideposts, not automatic reversal signals.
- **EMA 9 / EMA 20 / EMA 50 / EMA 100 / EMA 200**: Plain meaning: smooth price lines that show the recent and bigger trend. Shorter averages react faster; longer averages react more slowly. Technical detail: exponential moving averages weight recent prices more heavily; the active horizon selects which pair is used for trend checks.
- **ATR (14)**: Plain meaning: how much price has been swinging. Technical detail: a smoothed True Range using the largest of high–low, high–previous close, or low–previous close; it measures movement size, not direction.
- **Volume Ratio**: Plain meaning: whether this candle is busier than usual. Technical detail: current bar volume ÷ recent moving average; the scanner checks for at least 0.85×.
- **Setup Score**: Plain meaning: how many of five checks agree. Technical detail: the checks change with your horizon—VWAP and EMA 9/20 for day trading, EMA 20/50 for swing trading, and longer EMA pairs for long-term mode, plus volume and RSI. It is not a probability.
- **Trend Confirmation**: Plain meaning: check a second chart interval for agreement. Technical detail: compare the moving averages assigned to the active horizon on the separately selected timeframe; disagreement is a reason to be cautious.
- **ATR Stop Distance**: Plain meaning: give the stop some room for normal price swings. Technical detail: the calculator uses the larger of 1.25× ATR or 0.25% of price.
- **Position Sizing**: Plain meaning: decide how many shares or coins fit your risk limit. Technical detail: quantity is limited by risk budget ÷ entry-to-stop distance and account buying power; stocks use whole shares, crypto can be fractional.
- **Reward-to-Risk**: Plain meaning: compare the possible gain with the planned loss. Technical detail: entry-to-target distance ÷ entry-to-stop distance, before trading costs, slippage, borrow fees or taxes.
- **Entry Gap %**: Plain meaning: how far the planned entry is from the current quote. Technical detail: (planned entry ÷ current quote − 1) × 100; positive means above, negative means below.
- **Potential Reward %**: Plain meaning: the size of the planned favorable move. Technical detail: direction-adjusted entry-to-target distance ÷ entry × 100; it is not the chance of reaching the target.
- **Stop Risk %**: Plain meaning: how far away the protective stop is. Technical detail: direction-adjusted entry-to-stop distance ÷ entry × 100; this is not the percentage of the whole account at risk.
- **Paper Trade Return %**: Plain meaning: the gain or loss on one practice trade compared with its entry value. Technical detail: direction-adjusted P&L ÷ (entry × shares/units) × 100. Portfolio return instead compares total paper equity with the starting balance.
- **Technical Alignment %**: Plain meaning: how many of the five chart checks agree with the chosen direction. Technical detail: directional setup score ÷ 5 × 100; it measures rule agreement, not win probability.
- **Paper-History Model**: Plain meaning: looks for patterns in your finished practice trades. Technical detail: a small logistic model trained on saved entry snapshots; its raw output is used only for secondary candidate sorting because it is not independently calibrated as a win probability.
- **Historical Practice Replay**: One hypothetical entry on a historical candle, followed by a fixed number of candles. If a bar touches both stop and target, the simulator assumes the stop occurs first.
- **Data Limitations**: Plain meaning: prices or charts may be late or incomplete. Technical detail: Yahoo Finance intervals, screeners and quotes may be delayed, missing or rate-limited.
- **Percentage Direction Icons**: ↑ means up, ↓ means down, and → means nearly flat (within 0.05%). The arrow shows price/return direction, not whether a LONG or SHORT trade is profitable.
                """)

        if dash_mode == "Beginner (Simple)":
            st.markdown("---")
            info_heading("🎓 Beginner Learning Lab", "Learn the terms with a short factual quiz and practice one hypothetical LONG or SHORT on historical candles from the currently selected asset. The exercise does not use real money.", 3)
            render_beginner_quiz()
            render_historical_practice_simulator(df, ticker, rr_ratio, trading_horizon)

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
            render_terminal_notice(
                f"You already have an open paper position on {ticker}. The buttons stay visible, but close that position before opening another on the same asset.",
                kind="position",
            )
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
                "trading_horizon": trading_horizon,
                "side": "LONG",
                "entry": float(long_plan["entry"]),
                "stop": float(long_plan["stop"]),
                "target": float(long_plan["target"]),
                "shares": float(long_calc["quantity"]),
                "status": "OPEN",
                "exit": None,
                "pnl": None,
                "notes": f"Automatic Quick Execution LONG · risk budget ${long_calc['risk_budget']:.2f}",
                "ai_features": directional_learning_features(sig, "LONG"),
            })
            st.rerun()

        if short_col.button(
            f"🔻 Paper SHORT · {short_qty_text} {short_calc.get('unit', 'shares')}",
            key=f"quick_auto_short_{ticker}",
            type="primary",
            use_container_width=True,
            disabled=short_disabled,
            help="Opens the automatically sized simulated SHORT position. It has a stop above entry and target below entry. Paper practice only.",
        ):
            st.session_state.paper_trades.append({
                "id": str(uuid.uuid4())[:8],
                "time": datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M"),
                "ticker": ticker,
                "trading_horizon": trading_horizon,
                "side": "SHORT",
                "entry": float(short_plan["entry"]),
                "stop": float(short_plan["stop"]),
                "target": float(short_plan["target"]),
                "shares": float(short_calc["quantity"]),
                "status": "OPEN",
                "exit": None,
                "pnl": None,
                "notes": f"Automatic Quick Execution SHORT · risk budget ${short_calc['risk_budget']:.2f}",
                "ai_features": directional_learning_features(sig, "SHORT"),
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

        with st.container(border=True):
            st.markdown(
                '<div class="robinhood-panel-marker"></div>'
                '<div class="robinhood-handoff-kicker">REAL-MARKET ORDER HANDOFF</div>'
                '<div class="robinhood-handoff-copy">Continue to Robinhood to review the selected asset and complete any real order there. This area is separate from simulated paper trading.</div>',
                unsafe_allow_html=True,
            )
            info_heading(
                "↗ Real trade on Robinhood",
                "Opens the selected asset's official Robinhood detail page. Review the ticker, order type, amount and estimated execution price inside Robinhood before submitting. This terminal does not transmit real brokerage orders or collect Robinhood credentials.",
                4,
            )
            st.link_button(
                f"Review & Buy/Sell {display_asset_name(ticker)} ({ticker}) on Robinhood ↗",
                robinhood_asset_url(ticker),
                use_container_width=True,
            )
            st.caption(
                "This is a secure handoff to Robinhood, not an embedded order ticket. Asset availability, trading permissions and execution are determined by Robinhood. "
                "For agent-based order placement, Robinhood requires its separate Trading MCP onboarding and dedicated MCP/Agentic account."
            )
            st.markdown(
                "[Robinhood Trading MCP onboarding](https://robinhood.com/us/en/support/articles/onboarding-an-external-agent/) · "
                "[How to review and place a stock order](https://robinhood.com/us/en/support/articles/buying-a-stock/)",
                unsafe_allow_html=False,
            )

        # ---------- DYNAMIC CHART WITH ZOOM / TOOLBAR & MARKERS ----------
        chart_explanation = "Candles show open, high, low and close. VWAP and EMA 9/20 help with intraday context." if trading_horizon == "Day Trading" else ("Candles show open, high, low and close. EMA 20/50 show the swing trend." if trading_horizon == "Swing Trading" else f"Candles show open, high, low and close. {sig['trend_fast_name']} and {sig['trend_slow_name']} show the broader trend.")
        info_heading("📊 Price Chart", chart_explanation + " Green BUY and red SELL markers show where the selected horizon's rules first changed signal.", 4)
        plot_df = df.tail(90)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.78, 0.22], vertical_spacing=0.02)

        if chart_type == "Candlestick":
            fig.add_trace(go.Candlestick(
                x=plot_df.index, open=plot_df["Open"], high=plot_df["High"], low=plot_df["Low"], close=plot_df["Close"],
                name="Price",
                increasing_line_color="#089981", decreasing_line_color="#f23645",
                increasing_fillcolor="#089981", decreasing_fillcolor="#f23645"
            ), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(
                x=plot_df.index, y=plot_df["Close"],
                name="Close Price",
                line=dict(color="#4c8dff", width=2.2)
            ), row=1, col=1)

        if trading_horizon == "Day Trading":
            fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["VWAP"], name="VWAP", line=dict(color="#4da3ff", width=1.7)), row=1, col=1)
            fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["EMA9"], name="EMA 9", line=dict(color="#f0b90b", width=1.2)), row=1, col=1)
            fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["EMA20"], name="EMA 20", line=dict(color="#9b8cff", width=1.2)), row=1, col=1)
        elif trading_horizon == "Swing Trading":
            fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["EMA20"], name="EMA 20", line=dict(color="#f0b90b", width=1.4)), row=1, col=1)
            fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["EMA50"], name="EMA 50", line=dict(color="#9b8cff", width=1.5)), row=1, col=1)
        else:
            slow_chart_period = 200 if len(df) >= 205 else (100 if len(df) >= 105 else 50)
            fast_chart_period = 50 if slow_chart_period > 50 else 20
            fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df[f"EMA{fast_chart_period}"], name=f"EMA {fast_chart_period}", line=dict(color="#f0b90b", width=1.5)), row=1, col=1)
            fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df[f"EMA{slow_chart_period}"], name=f"EMA {slow_chart_period}", line=dict(color="#9b8cff", width=1.6)), row=1, col=1)

        # Draw a marker only when the signal changes into BUY or SELL. This keeps
        # the chart clean while making each new setup easy to spot.
        prior_signal = plot_df["Signal"].shift(1).fillna("HOLD")
        buy_signals = plot_df[(plot_df["Signal"] == "BUY") & (prior_signal != "BUY")]
        sell_signals = plot_df[(plot_df["Signal"] == "SELL") & (prior_signal != "SELL")]

        if not buy_signals.empty:
            buy_marker_y = buy_signals["Low"] - buy_signals["ATR"].fillna(0) * 0.18
            fig.add_trace(go.Scatter(
                x=buy_signals.index, y=buy_marker_y,
                mode="markers+text", text=["BUY"] * len(buy_signals),
                textposition="bottom center",
                textfont=dict(color="#35c9ac", size=12, family="Arial, sans-serif"),
                marker=dict(symbol="triangle-up", size=14, color="#089981", line=dict(width=1, color="#d1d4dc")),
                name="BUY signal", hovertemplate="BUY signal<br>%{x}<br>Level: %{y:.4f}<extra></extra>"
            ), row=1, col=1)

        if not sell_signals.empty:
            sell_marker_y = sell_signals["High"] + sell_signals["ATR"].fillna(0) * 0.18
            fig.add_trace(go.Scatter(
                x=sell_signals.index, y=sell_marker_y,
                mode="markers+text", text=["SELL"] * len(sell_signals),
                textposition="top center",
                textfont=dict(color="#ff6b78", size=12, family="Arial, sans-serif"),
                marker=dict(symbol="triangle-down", size=14, color="#f23645", line=dict(width=1, color="#d1d4dc")),
                name="SELL signal", hovertemplate="SELL signal<br>%{x}<br>Level: %{y:.4f}<extra></extra>"
            ), row=1, col=1)

        fig.add_hline(
            y=price_plan["entry"], line_dash="dot", line_color="#089981",
            annotation_text=f"{price_plan_side} Entry ${price_plan['entry']:,.{ticker_digits}f}", row=1, col=1
        )
        fig.add_hline(
            y=price_plan["target"], line_dash="dot", line_color="#089981",
            annotation_text=f"Profit Target ${price_plan['target']:,.{ticker_digits}f}", row=1, col=1
        )
        fig.add_hline(
            y=price_plan["stop"], line_dash="dash", line_color="#f23645",
            annotation_text=f"Stop Loss ${price_plan['stop']:,.{ticker_digits}f}", row=1, col=1
        )
        fig.add_hline(y=sig["projection_one_target"], line_dash="dash", line_color="#06b6d4", annotation_text=f"{sig['projection_one_label']} ${sig['projection_one_target']:,.{ticker_digits}f}", row=1, col=1)
        fig.add_hline(y=sig["projection_two_target"], line_dash="dot", line_color="#c792ea", annotation_text=f"{sig['projection_two_label']} ${sig['projection_two_target']:,.{ticker_digits}f}", row=1, col=1)

        bar_colors = ["#089981" if c >= o else "#f23645" for c, o in zip(plot_df["Close"], plot_df["Open"])]
        fig.add_trace(go.Bar(x=plot_df.index, y=plot_df["Volume"], name="Volume", marker_color=bar_colors, opacity=0.6), row=2, col=1)

        fig.update_layout(
            height=610,
            autosize=True,
            paper_bgcolor="#131722",
            plot_bgcolor="#131722",
            font=dict(color="#e0e5ee", family="Arial, sans-serif", size=13),
            margin=dict(l=8, r=12, t=22, b=8),
            xaxis_rangeslider_visible=False,
            showlegend=True,
            hovermode="x unified",
            legend=dict(orientation="h", y=1.04, x=0, bgcolor="rgba(19,23,34,0.75)", font=dict(color="#b8c2d1", size=12)),
            xaxis=dict(gridcolor="#252a36", linecolor="#363c4e", tickfont=dict(color="#aeb8c8", size=12), type="category", nticks=10, zeroline=False),
            yaxis=dict(gridcolor="#252a36", linecolor="#363c4e", tickfont=dict(color="#aeb8c8", size=12), side="right", zeroline=False),
            yaxis2=dict(gridcolor="#252a36", linecolor="#363c4e", tickfont=dict(color="#aeb8c8", size=12), side="right", zeroline=False),
            dragmode="pan",
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
        p1.metric("Paper Starting Balance", f"${st.session_state.account_size:,.2f}")
        p2.metric("Paper Portfolio Equity", f"${portfolio_equity:,.2f}")
        p2.markdown(percentage_indicator_html(total_return, label=f"{total_return:+.2f}% vs start"), unsafe_allow_html=True)
        p3.metric("Realized P&L", f"${realized_pnl:+,.2f}")
        p4.metric("Open P&L", f"${unrealized_pnl:+,.2f}")
        p5.metric("Open Positions", str(len(open_trades)))
        st.caption(
            "Paper portfolio return = (paper equity ÷ paper starting balance − 1). "
            "Each trade's return % below uses its own entry notional (entry price × shares/units). "
            "Quotes may be delayed or unavailable."
        )

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
                        "trading_horizon": trading_horizon,
                        "entry": float(manual_entry), "stop": float(manual_stop),
                        "target": float(manual_target), "shares": float(manual_qty),
                        "status": "OPEN", "exit": None, "pnl": None, "notes": manual_notes,
                        "ai_features": directional_learning_features(sig, manual_side) if manual_ticker == ticker else None
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
                    h1.markdown(f"**{display_asset_name(trade_ticker)}**  \n`{trade_ticker}` · {trade['side']} · {float(trade['shares']):,.6f} {unit} · {trade.get('trading_horizon', 'Older trade')}")
                    h2.metric("Entry / Mark", f"${float(trade['entry']):,.{digits}f}", f"Mark ${live_px:,.{digits}f}")
                    h3.metric("Stop / Target", f"${float(trade['stop']):,.{digits}f}", f"Target ${float(trade['target']):,.{digits}f}")
                    open_return_pct = paper_trade_return_pct(unrealized, trade["entry"], trade["shares"])
                    h4.metric(
                        "Unrealized P&L",
                        f"${unrealized:+,.2f}",
                        help="Estimated open profit/loss. Return % = unrealized P&L divided by entry price × shares/units; LONG and SHORT P&L are direction-adjusted."
                    )
                    if open_return_pct is not None:
                        h4.markdown(percentage_indicator_html(open_return_pct, label=f"{open_return_pct:+.2f}% on entry value"), unsafe_allow_html=True)
                    else:
                        h4.caption("Return % unavailable")
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
            breakeven_count = total_closed - len(wins) - len(losses)
            cdf["pnl"] = pd.to_numeric(cdf["pnl"], errors="coerce").fillna(0)
            cdf["return_pct"] = [
                paper_trade_return_pct(row.get("pnl", 0), row.get("entry", 0), row.get("shares", 0))
                for row in closed_sorted
            ]
            valid_trade_returns = [value for value in cdf["return_pct"].tolist() if value is not None and np.isfinite(value)]
            avg_trade_return = float(np.mean(valid_trade_returns)) if valid_trade_returns else 0.0
            a1, a2, a3, a4, a5 = st.columns(5)
            a1.metric("Net Realized P&L", f"${sum(pnl_values):+,.2f}")
            a2.metric("Win Rate", f"{win_rate:.1f}%", f"{len(wins)} wins · {len(losses)} losses · {breakeven_count} flat")
            a3.metric("Average Winner", f"${avg_win:+,.2f}")
            a4.metric("Average Loser", f"${avg_loss:+,.2f}")
            a5.metric("Average Trade Return", f"{avg_trade_return:+.2f}%", help="Arithmetic average of each closed trade's P&L divided by its entry notional. This is not portfolio return.")
            a5.markdown(percentage_indicator_html(avg_trade_return, label=f"{avg_trade_return:+.2f}% average"), unsafe_allow_html=True)
            cdf["cumulative_pnl"] = cdf["pnl"].cumsum()
            eq = px.line(cdf, x="closed_at" if "closed_at" in cdf else "time", y="cumulative_pnl", title="Cumulative Realized P&L", markers=True)
            eq.update_layout(paper_bgcolor="#131722", plot_bgcolor="#1e222d", font=dict(color="#e0e5ee", family="Arial, sans-serif", size=13), height=340, margin=dict(l=14, r=14, t=48, b=14), xaxis=dict(gridcolor="#2a2e39", tickfont=dict(color="#aeb8c8", size=12)), yaxis=dict(gridcolor="#2a2e39", tickfont=dict(color="#aeb8c8", size=12), title="P&L ($)"))
            eq.update_traces(line_color="#10b981" if sum(pnl_values) >= 0 else "#ef4444", line_width=3)
            st.plotly_chart(eq, use_container_width=True)
            display_cols = [c for c in ["time", "closed_at", "ticker", "side", "trading_horizon", "entry", "exit", "stop", "target", "shares", "pnl", "return_pct", "notes"] if c in cdf.columns]
            st.dataframe(cdf[display_cols], use_container_width=True, hide_index=True)
            csv_export = cdf.copy()
            if "ai_features" in csv_export.columns:
                import json
                csv_export["ai_features"] = csv_export["ai_features"].apply(
                    lambda value: json.dumps(value) if isinstance(value, dict) else ""
                )
            csv_buffer = io.StringIO()
            csv_export.to_csv(csv_buffer, index=False)
            st.download_button("📥 Export Paper Journal (CSV)", csv_buffer.getvalue(), file_name=f"paper_trading_journal_{date.today()}.csv", mime="text/csv", key="export_paper_journal")

        if not normalized_records:
            render_paper_empty_state()
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
  <div class="terminal-kicker">Market-wide discovery · adaptive learning · simulated execution</div>
  <h1>⚡ PRO DAY TRADE TERMINAL</h1>
  <p>A day-trading-first workspace with optional swing and long-term analysis, market discovery, adaptive paper-trade learning, risk planning and simulated execution.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
render_dashboard()

st.markdown("""
<div class="educational-disclaimer">
  <div class="disclaimer-heading">⚠️ Educational Disclaimer</div>
  <p><strong>Educational use only:</strong> This terminal is a learning and research tool, not a broker or a substitute for independent financial judgment.</p>
  <p><strong>Market data:</strong> Quotes and history come from Yahoo Finance and may be delayed, incomplete, adjusted, or unavailable.</p>
  <p><strong>Signals, AI assessments and percentages:</strong> These are technical scenarios and calculations, not personalized investment advice, calibrated win probabilities, or guarantees. A target percentage describes the distance between entry and target; it does not describe the likelihood of reaching it.</p>
  <p><strong>Paper Trading Desk:</strong> All paper positions and P&amp;L are simulated. Percent returns use entry notional for each trade; portfolio return uses the paper starting balance. Simulations do not include every real-world fee, spread, tax, borrow cost, or execution difference.</p>
  <p><strong>Robinhood:</strong> The link above opens the selected asset on Robinhood for you to review and place an order there. This terminal does not send real orders, access your Robinhood credentials, or guarantee that an asset is tradable in your account.</p>
  <p>Always check the current quote, order details, permissions and risks independently before making an investment decision.</p>
</div>
""", unsafe_allow_html=True)
