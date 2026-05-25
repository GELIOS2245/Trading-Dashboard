#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
  EQUITIES INTELLIGENCE TERMINAL  v3.0
  Multi-Source Quantitative & Fundamental Research Platform
═══════════════════════════════════════════════════════════════════════════════

requirements.txt contents (add this file to your GitHub repo):
    streamlit==1.40.2
    yfinance==0.2.51
    pandas
    numpy
    requests
    feedparser
    plotly
    beautifulsoup4
    lxml

RUN LOCALLY:
    streamlit run trading_dashboard_v3.py
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import html
import re
import time
import warnings
from datetime import datetime
from typing import Optional

import feedparser
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf
from bs4 import BeautifulSoup
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="EQ · Intelligence Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────────────────────────────────────
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700;800&display=swap');
html,body,[class*="css"],.stApp{font-family:'Outfit',sans-serif;background:#050a14;color:#b8cce0}
.main,.block-container{background:#050a14 !important;padding-top:1rem !important}
p,li{font-size:.88rem;line-height:1.75;color:#8aacc8}

.banner{background:linear-gradient(135deg,#071428 0%,#091a2e 60%,#071428 100%);border:1px solid #0f2540;border-radius:12px;padding:18px 26px;margin-bottom:18px;display:flex;align-items:center;justify-content:space-between}
.banner-title{font-family:'Outfit',sans-serif;font-weight:800;font-size:1.5rem;color:#e8f0ff;letter-spacing:-.02em}
.banner-sub{font-family:'IBM Plex Mono',monospace;font-size:.62rem;color:#3a5a80;letter-spacing:.06em;text-transform:uppercase;margin-top:3px}
.live-dot{width:7px;height:7px;background:#00d4aa;border-radius:50%;display:inline-block;margin-right:6px;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.4;transform:scale(1.3)}}
.live-text{font-family:'IBM Plex Mono',monospace;font-size:.67rem;color:#00d4aa;font-weight:600}

.stTabs [data-baseweb="tab-list"]{background:#071428;border-radius:10px;gap:2px;padding:4px;border:1px solid #0f2540}
.stTabs [data-baseweb="tab"]{color:#3a5a80;background:transparent;border-radius:8px;font-family:'IBM Plex Mono',monospace;font-size:.76rem;letter-spacing:.05em;padding:8px 16px}
.stTabs [aria-selected="true"]{background:#0d2040 !important;color:#60a5fa !important;border:1px solid #1e3d6a !important}

.card{background:linear-gradient(160deg,#071428 0%,#09192e 100%);border:1px solid #0f2540;border-radius:10px;padding:16px;margin:6px 0}
.card-sm{padding:10px 14px}

/* Sector grid buttons */
.sector-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:16px}
.sector-tile{background:#071428;border:1px solid #0f2540;border-radius:10px;padding:14px 10px;text-align:center;cursor:pointer;transition:all .15s ease}
.sector-tile:hover{border-color:#1e3d6a;background:#091428}
.sector-tile.selected{border:2px solid #3b82f6;background:#0d2040}
.sector-tile-icon{font-size:1.5rem;display:block;margin-bottom:6px}
.sector-tile-name{font-family:'IBM Plex Mono',monospace;font-size:.63rem;color:#7a9cc0;text-transform:uppercase;letter-spacing:.08em;line-height:1.4}
.sector-tile.selected .sector-tile-name{color:#60a5fa}
.sector-tile-etf{font-family:'IBM Plex Mono',monospace;font-size:.58rem;color:#2a4a6a;margin-top:3px}
.sector-tile.selected .sector-tile-etf{color:#3b82f6}

.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:12px 0}
.metric-tile{background:#071428;border:1px solid #0f2540;border-radius:8px;padding:12px 14px;text-align:center}
.m-label{font-family:'IBM Plex Mono',monospace;font-size:.62rem;color:#2a4a6a;text-transform:uppercase;letter-spacing:.12em;margin-bottom:4px}
.m-val{font-family:'IBM Plex Mono',monospace;font-size:1.1rem;font-weight:700}
.bull{color:#00d4aa}.bear{color:#ff4d6d}.neu{color:#c8deff}.amber{color:#f59e0b}

.sec-label{font-family:'IBM Plex Mono',monospace;font-size:.64rem;color:#3b82f6;text-transform:uppercase;letter-spacing:.18em;border-left:2px solid #3b82f6;padding-left:10px;margin:18px 0 10px 0}
.edu-box{background:#050e1c;border:1px dashed #1e3450;border-radius:6px;padding:10px 14px;font-size:.78rem;color:#4a7296;font-style:italic;margin-top:6px;line-height:1.6}
.edu-box::before{content:"💡 "}

.report-box{background:#060f1e;border:1px solid #0f2540;border-radius:10px;padding:18px;font-size:.85rem;line-height:1.8;color:#8aacc8}
.report-long{border-top:3px solid #00d4aa}
.report-short{border-top:3px solid #ff4d6d}
.report-blue{border-top:3px solid #3b82f6}
.report-amber{border-top:3px solid #f59e0b}
.report-box strong{color:#c8deff}

.chip-long{background:#00d4aa18;border:1px solid #00d4aa40;color:#00d4aa;padding:3px 10px;border-radius:5px;font-family:'IBM Plex Mono',monospace;font-size:.76rem;font-weight:700;display:inline-block;margin:2px}
.chip-short{background:#ff4d6d18;border:1px solid #ff4d6d40;color:#ff4d6d;padding:3px 10px;border-radius:5px;font-family:'IBM Plex Mono',monospace;font-size:.76rem;font-weight:700;display:inline-block;margin:2px}
.chip-blue{background:#3b82f618;border:1px solid #3b82f640;color:#60a5fa;padding:2px 8px;border-radius:4px;font-family:'IBM Plex Mono',monospace;font-size:.64rem;display:inline-block}

.score-bar-bg{background:#0d1e30;border-radius:4px;height:6px;margin:5px 0}
.score-bar-fill{height:6px;border-radius:4px}

.analyst-row{display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid #0c1e30}
.analyst-firm{font-family:'IBM Plex Mono',monospace;font-size:.74rem;color:#c8deff;font-weight:600}
.analyst-date{font-family:'IBM Plex Mono',monospace;font-size:.61rem;color:#2a4a6a}
.analyst-pt{font-family:'IBM Plex Mono',monospace;font-size:.71rem;color:#f59e0b}
.chip-upgrade{background:#00d4aa12;border:1px solid #00d4aa30;color:#00d4aa;padding:2px 7px;border-radius:4px;font-family:'IBM Plex Mono',monospace;font-size:.61rem;display:inline-block}
.chip-downgrade{background:#ff4d6d12;border:1px solid #ff4d6d30;color:#ff4d6d;padding:2px 7px;border-radius:4px;font-family:'IBM Plex Mono',monospace;font-size:.61rem;display:inline-block}
.chip-hold{background:#f59e0b12;border:1px solid #f59e0b30;color:#f59e0b;padding:2px 7px;border-radius:4px;font-family:'IBM Plex Mono',monospace;font-size:.61rem;display:inline-block}

.filing-row{padding:10px 0;border-bottom:1px solid #0c1e30;display:flex;align-items:flex-start;gap:12px}
.filing-badge{font-family:'IBM Plex Mono',monospace;font-size:.59rem;font-weight:700;padding:3px 7px;border-radius:4px;white-space:nowrap}
.badge-8k{background:#ff4d6d18;border:1px solid #ff4d6d40;color:#ff4d6d}
.badge-10k{background:#a78bfa18;border:1px solid #a78bfa40;color:#a78bfa}
.badge-10q{background:#60a5fa18;border:1px solid #60a5fa40;color:#60a5fa}
.badge-def{background:#f59e0b18;border:1px solid #f59e0b40;color:#f59e0b}
.badge-other{background:#2a4a6a18;border:1px solid #2a4a6a40;color:#4a7296}

.news-row{padding:10px 0;border-bottom:1px solid #0c1e30}
.news-title a{color:#7ab0d8;text-decoration:none;font-size:.84rem}
.news-meta{font-family:'IBM Plex Mono',monospace;font-size:.62rem;color:#2a4a6a;margin-top:3px}

.macro-tile{background:#071428;border:1px solid #0f2540;border-radius:8px;padding:14px;text-align:center}
.macro-val{font-family:'IBM Plex Mono',monospace;font-size:1.1rem;font-weight:700;color:#e8f0ff;margin:4px 0}
.macro-chg{font-family:'IBM Plex Mono',monospace;font-size:.76rem;margin-top:2px}

.err-box{background:#1a0a0a;border:1px solid #ff4d6d40;border-radius:8px;padding:14px;font-size:.82rem;color:#ff9090;margin:10px 0}
.warn-box{background:#1a1400;border:1px solid #f59e0b40;border-radius:8px;padding:14px;font-size:.82rem;color:#f0c060;margin:10px 0}

.stTextInput input{background:#071428 !important;border:1px solid #0f2540 !important;color:#c8deff !important;font-family:'IBM Plex Mono',monospace !important;border-radius:8px !important}
.stTextInput input:focus{border-color:#3b82f6 !important}
.stButton button{background:#0d2040;border:1px solid #1e3d6a;color:#60a5fa;border-radius:8px;font-family:'IBM Plex Mono',monospace;font-size:.8rem;letter-spacing:.05em}
.stButton button:hover{background:#132d54;border-color:#3b82f6;color:#93c5fd}
.stSelectbox>div>div{background:#071428 !important;border:1px solid #0f2540 !important;color:#c8deff !important;border-radius:8px !important}
div[data-testid="stExpander"]{background:#071428;border:1px solid #0f2540;border-radius:8px}
hr{border:none;border-top:1px solid #0c1e30;margin:16px 0}
::-webkit-scrollbar{width:5px}
::-webkit-scrollbar-track{background:#050a14}
::-webkit-scrollbar-thumb{background:#0f2540;border-radius:3px}
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  SECTOR UNIVERSE
# ─────────────────────────────────────────────────────────────────────────────
SECTORS: dict = {
    "Information Technology": {
        "icon": "💻", "etf": "XLK",
        "tickers": ["AAPL","MSFT","NVDA","AMD","AVGO","CRM","ORCL","ADBE","QCOM","TXN"],
        "sub": {"AAPL":"Consumer Electronics","MSFT":"Enterprise Cloud","NVDA":"AI / Data Center GPUs","AMD":"CPUs & GPUs","AVGO":"Networking Chips","CRM":"CRM / SaaS","ORCL":"Database / Cloud (OCI)","ADBE":"Creative SaaS","QCOM":"Mobile Semiconductors","TXN":"Analog Semiconductors"}},
    "Health Care": {
        "icon": "🏥", "etf": "XLV",
        "tickers": ["JNJ","UNH","ABBV","MRK","TMO","ABT","AMGN","GILD","PFE","ISRG"],
        "sub": {"JNJ":"Diversified Pharma & MedTech","UNH":"Managed Care","ABBV":"Biopharmaceuticals","MRK":"Large-Cap Pharma","TMO":"Life Sciences Tools","ABT":"Medical Devices","AMGN":"Biotechnology","GILD":"Antiviral Biotech","PFE":"Large-Cap Pharma","ISRG":"Robotic Surgery"}},
    "Financials": {
        "icon": "🏦", "etf": "XLF",
        "tickers": ["JPM","BAC","GS","MS","BLK","AXP","WFC","C","SCHW","ICE"],
        "sub": {"JPM":"Global Banking","BAC":"Retail & Investment Banking","GS":"Investment Banking","MS":"Wealth & Investment Banking","BLK":"Asset Management","AXP":"Charge Cards","WFC":"Retail Banking","C":"Global Consumer Banking","SCHW":"Discount Brokerage","ICE":"Financial Exchanges"}},
    "Consumer Discretionary": {
        "icon": "🛍️", "etf": "XLY",
        "tickers": ["AMZN","TSLA","HD","MCD","NKE","SBUX","TJX","LOW","BKNG","ABNB"],
        "sub": {"AMZN":"E-Commerce / Cloud","TSLA":"Electric Vehicles","HD":"Home Improvement","MCD":"Quick Service Restaurants","NKE":"Athletic Apparel","SBUX":"Specialty Coffee","TJX":"Off-Price Retail","LOW":"Home Improvement","BKNG":"Online Travel","ABNB":"Short-Term Rentals"}},
    "Communication Services": {
        "icon": "📡", "etf": "XLC",
        "tickers": ["META","GOOGL","NFLX","DIS","CMCSA","T","VZ","SNAP","PINS","TTD"],
        "sub": {"META":"Social Media / VR","GOOGL":"Search / Cloud / AI","NFLX":"Video Streaming","DIS":"Theme Parks / Streaming","CMCSA":"Cable / Broadband","T":"Telecom / Fiber","VZ":"Wireless Telecom","SNAP":"Social / AR Camera","PINS":"Visual Discovery","TTD":"Programmatic Advertising"}},
    "Industrials": {
        "icon": "⚙️", "etf": "XLI",
        "tickers": ["HON","CAT","GE","UPS","RTX","DE","LMT","NOC","FDX","ETN"],
        "sub": {"HON":"Diversified Industrials","CAT":"Construction Equipment","GE":"Aerospace Engines","UPS":"Package Delivery","RTX":"Defense / Aerospace","DE":"Agricultural Machinery","LMT":"Defense Contractor","NOC":"Defense / Cyber","FDX":"Global Freight","ETN":"Electrical Power"}},
    "Consumer Staples": {
        "icon": "🛒", "etf": "XLP",
        "tickers": ["PG","KO","PEP","WMT","COST","PM","MO","CL","GIS","MDLZ"],
        "sub": {"PG":"Household & Personal Care","KO":"Beverages","PEP":"Beverages & Snacks","WMT":"Discount Retail","COST":"Warehouse Retail","PM":"International Tobacco","MO":"U.S. Tobacco","CL":"Oral & Home Care","GIS":"Packaged Foods","MDLZ":"Snacks & Chocolate"}},
    "Energy": {
        "icon": "⛽", "etf": "XLE",
        "tickers": ["XOM","CVX","COP","SLB","EOG","MPC","PSX","VLO","OXY","DVN"],
        "sub": {"XOM":"Integrated Oil & Gas","CVX":"Integrated Oil & Gas","COP":"E&P Upstream","SLB":"Oilfield Services","EOG":"Permian Basin E&P","MPC":"Refining","PSX":"Refining / Midstream","VLO":"Independent Refining","OXY":"E&P / Carbon Capture","DVN":"Delaware Basin E&P"}},
    "Utilities": {
        "icon": "⚡", "etf": "XLU",
        "tickers": ["NEE","DUK","SO","D","AEP","EXC","SRE","ED","XEL","WEC"],
        "sub": {"NEE":"Renewable Energy","DUK":"Electric Utility","SO":"Electric & Gas Utility","D":"Electric & Gas","AEP":"Transmission Utility","EXC":"Nuclear Power","SRE":"California Gas / LNG","ED":"New York Utility","XEL":"Renewable Utility","WEC":"Midwest Utility"}},
    "Real Estate": {
        "icon": "🏢", "etf": "XLRE",
        "tickers": ["AMT","PLD","EQIX","CCI","PSA","WELL","O","SPG","DLR","VICI"],
        "sub": {"AMT":"Cell Tower REIT","PLD":"Industrial REIT","EQIX":"Data Center REIT","CCI":"Cell Tower / Fiber REIT","PSA":"Self-Storage REIT","WELL":"Healthcare REIT","O":"Net Lease REIT","SPG":"Premium Mall REIT","DLR":"Data Center REIT","VICI":"Gaming Real Estate"}},
    "Materials": {
        "icon": "⛏️", "etf": "XLB",
        "tickers": ["LIN","APD","SHW","FCX","NEM","NUE","ALB","ECL","MOS","CF"],
        "sub": {"LIN":"Industrial Gases","APD":"Industrial Gases","SHW":"Paints & Coatings","FCX":"Copper Mining","NEM":"Gold Mining","NUE":"Steel","ALB":"Lithium / Chemicals","ECL":"Water Treatment","MOS":"Fertilizers","CF":"Nitrogen Fertilizers"}},
}

# Macro symbols — kept small and reliable
MACRO_SYMBOLS: dict = {
    "S&P 500":       {"sym": "^GSPC",    "type": "index",  "fmt": ",.0f"},
    "NASDAQ":        {"sym": "^IXIC",    "type": "index",  "fmt": ",.0f"},
    "Dow Jones":     {"sym": "^DJI",     "type": "index",  "fmt": ",.0f"},
    "VIX":           {"sym": "^VIX",     "type": "index",  "fmt": ".2f"},
    "10Y Treasury":  {"sym": "^TNX",     "type": "rate",   "fmt": ".3f"},
    "2Y Treasury":   {"sym": "^IRX",     "type": "rate",   "fmt": ".3f"},
    "30Y Treasury":  {"sym": "^TYX",     "type": "rate",   "fmt": ".3f"},
    "Dollar Index":  {"sym": "DX-Y.NYB", "type": "fx",     "fmt": ".2f"},
    "EUR/USD":       {"sym": "EURUSD=X", "type": "fx",     "fmt": ".4f"},
    "Gold":          {"sym": "GC=F",     "type": "comm",   "fmt": ",.2f"},
    "WTI Crude":     {"sym": "CL=F",     "type": "comm",   "fmt": ".2f"},
    "Copper":        {"sym": "HG=F",     "type": "comm",   "fmt": ".3f"},
}

NEWS_SOURCES: dict = {
    "Yahoo Finance":  "https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US",
    "Google News":    "https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en",
    "Reuters":        "https://news.google.com/rss/search?q={ticker}+site:reuters.com&hl=en&gl=US&ceid=US:en",
    "CNBC":           "https://news.google.com/rss/search?q={ticker}+site:cnbc.com&hl=en&gl=US&ceid=US:en",
    "MarketWatch":    "https://news.google.com/rss/search?q={ticker}+site:marketwatch.com&hl=en&gl=US&ceid=US:en",
    "Seeking Alpha":  "https://news.google.com/rss/search?q={ticker}+site:seekingalpha.com&hl=en&gl=US&ceid=US:en",
    "Barron's":       "https://news.google.com/rss/search?q={ticker}+site:barrons.com&hl=en&gl=US&ceid=US:en",
    "Benzinga":       "https://news.google.com/rss/search?q={ticker}+site:benzinga.com&hl=en&gl=US&ceid=US:en",
}

NEWS_COLORS: dict = {
    "Yahoo Finance": "#7ab0d8", "Google News": "#94a3b8",
    "Reuters": "#f59e0b", "CNBC": "#60a5fa",
    "MarketWatch": "#00d4aa", "Seeking Alpha": "#a78bfa",
    "Barron's": "#e879f9", "Benzinga": "#fb923c",
}

FINVIZ_HEADERS: dict = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.5",
}

EDGAR_BASE = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type={form}&dateb=&owner=include&count=6&output=atom"


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _safe(val, default=None):
    try:
        if val is None:
            return default
        if isinstance(val, float) and (val != val or val == float("inf") or val == float("-inf")):
            return default
        return val
    except Exception:
        return default

def fmt_pct(val, none_str="N/A"):
    if val is None: return none_str
    try: return "{:+.1f}%".format(val * 100)
    except: return none_str

def fmt_large(val, none_str="N/A"):
    if val is None: return none_str
    try:
        v = float(val)
        if abs(v) >= 1e12: return "${:.2f}T".format(v/1e12)
        if abs(v) >= 1e9:  return "${:.2f}B".format(v/1e9)
        if abs(v) >= 1e6:  return "${:.2f}M".format(v/1e6)
        return "${:.0f}".format(v)
    except: return none_str

def fmt_val(val, fmt=".2f", suffix="", none_str="N/A"):
    if val is None: return none_str
    try: return "{:{}}{}".format(val, fmt, suffix)
    except: return none_str

def color_class(val, thresh=0, reverse=False):
    if val is None: return "neu"
    is_good = float(val) > thresh
    if reverse: is_good = not is_good
    return "bull" if is_good else "bear"

def score_bar_html(score, color="#3b82f6"):
    return (
        '<div class="score-bar-bg">'
        '<div class="score-bar-fill" style="width:{:.0f}%;background:{};"></div>'
        '</div>'
        '<span style="font-family:\'IBM Plex Mono\',monospace;font-size:.69rem;color:{};">'
        '{:.0f}/100</span>'
    ).format(score, color, color, score)

def metric_tiles_html(pairs):
    tiles = "".join(
        '<div class="metric-tile"><div class="m-label">{}</div>'
        '<div class="m-val {}">{}</div></div>'.format(lbl, cls, val)
        for lbl, val, cls in pairs
    )
    return '<div class="metric-grid">{}</div>'.format(tiles)

def section_label(text):
    st.markdown('<div class="sec-label">{}</div>'.format(text), unsafe_allow_html=True)

def edu_box(text):
    st.markdown('<div class="edu-box">{}</div>'.format(text), unsafe_allow_html=True)

def err_box(text):
    st.markdown('<div class="err-box">⚠️ {}</div>'.format(text), unsafe_allow_html=True)

def warn_box(text):
    st.markdown('<div class="warn-box">ℹ️ {}</div>'.format(text), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  DATA FETCHING — yfinance with retry
# ─────────────────────────────────────────────────────────────────────────────
def _make_session():
    """Create a requests session with browser-like headers to reduce yfinance rate-limiting."""
    import requests as _req
    s = _req.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    })
    return s


def _fetch_hist_download(ticker: str) -> pd.DataFrame:
    """
    Use yf.download() as a reliable fallback for price history.
    More robust than tk.history() on cloud IPs.
    """
    for period in ["1y", "6mo", "3mo"]:
        try:
            df = yf.download(
                ticker, period=period, interval="1d",
                auto_adjust=True, progress=False, threads=False,
            )
            if df is not None and not df.empty:
                # yf.download may return MultiIndex columns when single ticker
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                return df
        except Exception:
            time.sleep(0.5)
    return pd.DataFrame()


def _fetch_info_safe(ticker: str, retries: int = 4, delay: float = 2.0) -> dict:
    """
    Fetch yfinance info dict with retry + session headers.
    Returns dict (may be partial/empty) — never raises.
    """
    t_up = ticker.upper().strip()
    for attempt in range(retries):
        try:
            sess = _make_session()
            tk   = yf.Ticker(t_up, session=sess)
            info = tk.info
            if info and len(info) > 5:
                return info
        except Exception:
            pass
        # Also try without custom session
        try:
            tk   = yf.Ticker(t_up)
            info = tk.info
            if info and len(info) > 5:
                return info
        except Exception:
            pass
        if attempt < retries - 1:
            time.sleep(delay)
    return {}


@st.cache_data(ttl=900, show_spinner=False)
def get_raw(ticker: str):
    """
    Fetch full yfinance data bundle with multi-layer fallbacks.
    Returns dict (may have partial data) or None if completely unavailable.
    """
    t_up = ticker.upper().strip()
    try:
        # ── Layer 1: fetch info with retry + session headers ─────────────────
        info = _fetch_info_safe(t_up, retries=4, delay=2.0)

        # ── Layer 2: get price history — try tk.history first, yf.download fallback
        hist = pd.DataFrame()
        try:
            sess = _make_session()
            tk   = yf.Ticker(t_up, session=sess)
            for period in ["1y", "6mo", "3mo"]:
                try:
                    h = tk.history(period=period, interval="1d", auto_adjust=True)
                    if h is not None and not h.empty:
                        hist = h
                        break
                except Exception:
                    time.sleep(0.3)
        except Exception:
            pass

        # Fallback to yf.download if tk.history failed
        if hist.empty:
            hist = _fetch_hist_download(t_up)

        # ── Layer 3: inject price from hist into info if missing ─────────────
        if hist is not None and not hist.empty:
            last_close = float(hist["Close"].iloc[-1])
            if not info.get("currentPrice") and not info.get("regularMarketPrice"):
                info["currentPrice"] = last_close
            if not info.get("fiftyTwoWeekHigh"):
                info["fiftyTwoWeekHigh"] = float(hist["High"].max())
            if not info.get("fiftyTwoWeekLow"):
                info["fiftyTwoWeekLow"] = float(hist["Low"].min())

        # ── If we have neither info nor hist, give up ─────────────────────────
        if not info and (hist is None or hist.empty):
            return None

        # ── Layer 4: optional supplemental data (skip gracefully) ────────────
        cashflow = balance = income = pd.DataFrame()
        upgrades = holders = pd.DataFrame()
        try:
            tk2 = yf.Ticker(t_up)
            try: cashflow = tk2.cashflow
            except Exception: pass
            try: balance  = tk2.balance_sheet
            except Exception: pass
            try:
                upgrades = tk2.upgrades_downgrades
            except Exception:
                try: upgrades = tk2.upgrades
                except Exception: pass
            try: holders = tk2.institutional_holders
            except Exception: pass
        except Exception:
            pass

        return {
            "info": info, "hist": hist, "cashflow": cashflow,
            "balance": balance, "income": income,
            "upgrades": upgrades, "holders": holders,
            "ticker": t_up,
            "partial": len(info) < 10,  # flag partial data for UI
        }
    except Exception:
        return None


@st.cache_data(ttl=1800, show_spinner=False)
def get_macro_snapshot():
    """
    Fetch macro data one symbol at a time to avoid batch failures.
    Returns dict keyed by display name.
    """
    result = {}
    for label, meta in MACRO_SYMBOLS.items():
        sym = meta["sym"]
        for attempt in range(3):
            try:
                tk   = yf.Ticker(sym)
                hist = tk.history(period="5d", interval="1d", auto_adjust=True)
                if hist is not None and len(hist) >= 2:
                    last = float(hist["Close"].iloc[-1])
                    prev = float(hist["Close"].iloc[-2])
                    chg  = (last / prev - 1) if prev != 0 else 0.0
                    result[label] = {
                        "last": last, "chg": chg,
                        "fmt": meta["fmt"], "type": meta["type"],
                        "hist": hist["Close"].dropna(),
                    }
                    break
            except Exception:
                pass
            time.sleep(0.4)
    return result


@st.cache_data(ttl=1800, show_spinner=False)
def get_sector_etf_perf():
    """Fetch 1-day % change for all 11 sector ETFs individually."""
    result = {}
    for sname, sdata in SECTORS.items():
        etf = sdata["etf"]
        for attempt in range(3):
            try:
                tk   = yf.Ticker(etf)
                hist = tk.history(period="5d", interval="1d", auto_adjust=True)
                if hist is not None and len(hist) >= 2:
                    last = float(hist["Close"].iloc[-1])
                    prev = float(hist["Close"].iloc[-2])
                    chg  = (last / prev - 1) if prev != 0 else 0.0
                    result[sname] = {"etf": etf, "chg": chg, "last": last}
                    break
            except Exception:
                pass
            time.sleep(0.3)
    return result


# ─────────────────────────────────────────────────────────────────────────────
#  NEWS & FILINGS
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def fetch_multi_news(ticker: str, max_per: int = 3):
    """Aggregate news from 8 RSS sources with deduplication."""
    all_items = []
    seen = set()
    for src, url_tmpl in NEWS_SOURCES.items():
        url = url_tmpl.format(ticker=ticker.upper())
        try:
            feed  = feedparser.parse(url)
            count = 0
            for entry in feed.entries:
                title = html.unescape(entry.get("title", "")).strip()
                title = re.sub(r"\s*[-–]\s*[A-Z][A-Za-z\s.]+$", "", title).strip()
                if not title or len(title) < 10:
                    continue
                key = title[:55].lower()
                if key in seen:
                    continue
                seen.add(key)
                all_items.append({
                    "title":  title,
                    "link":   entry.get("link", ""),
                    "date":   entry.get("published", entry.get("updated", ""))[:16],
                    "source": src,
                })
                count += 1
                if count >= max_per:
                    break
        except Exception:
            continue
    all_items.sort(key=lambda x: x["date"], reverse=True)
    return all_items[:18]


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_sec_filings(ticker: str):
    """Pull recent EDGAR filings via public Atom RSS."""
    filings = []
    headers = {"User-Agent": "EQ-Terminal research@example.com", "Accept-Encoding": "gzip, deflate"}
    for form in ["8-K", "10-K", "10-Q", "DEF 14A"]:
        try:
            url  = EDGAR_BASE.format(ticker=ticker.upper(), form=form.replace(" ", "+"))
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                continue
            feed = feedparser.parse(resp.text)
            for entry in feed.entries[:2]:
                title   = html.unescape(entry.get("title", ""))
                summary = html.unescape(entry.get("summary", ""))
                if len(summary) > 150: summary = summary[:150] + "…"
                filings.append({
                    "form":    form,
                    "title":   title,
                    "link":    entry.get("link", ""),
                    "date":    entry.get("updated", entry.get("published", ""))[:10],
                    "summary": summary,
                })
        except Exception:
            continue
    filings.sort(key=lambda x: x["date"], reverse=True)
    return filings[:10]


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_finviz_ratings(ticker: str):
    """Scrape analyst ratings from finviz.com."""
    ratings = []
    try:
        url  = "https://finviz.com/quote.ashx?t={}&p=d".format(ticker.upper())
        resp = requests.get(url, headers=FINVIZ_HEADERS, timeout=12)
        if resp.status_code != 200:
            return ratings
        soup  = BeautifulSoup(resp.text, "lxml")
        table = soup.find("table", {"class": "js-table-ratings"})
        if table is None:
            for tbl in soup.find_all("table"):
                if any(w in tbl.get_text() for w in ["Upgrade","Downgrade","Initiated"]):
                    table = tbl; break
        if table is None:
            return ratings
        for row in table.find_all("tr")[1:9]:
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cells) >= 4:
                ratings.append({
                    "date": cells[0], "action": cells[1],
                    "firm": cells[2], "rating": cells[3],
                    "pt":   cells[4] if len(cells) > 4 else "",
                })
    except Exception:
        pass
    return ratings


# ─────────────────────────────────────────────────────────────────────────────
#  METRICS COMPUTATION
# ─────────────────────────────────────────────────────────────────────────────
def compute_metrics(raw):
    if raw is None:
        return None
    info     = raw.get("info") if raw.get("info") is not None else {}
    hist_raw = raw.get("hist")
    hist     = hist_raw if isinstance(hist_raw, pd.DataFrame) and not hist_raw.empty else pd.DataFrame()
    cf_raw   = raw.get("cashflow")
    cashflow = cf_raw if isinstance(cf_raw, pd.DataFrame) and not cf_raw.empty else pd.DataFrame()
    ticker   = raw.get("ticker", "")

    m = {"ticker": ticker}
    m["name"]     = _safe(info.get("longName"), ticker)
    m["sector"]   = _safe(info.get("sector"), "Unknown")
    m["industry"] = _safe(info.get("industry"), "Unknown")
    m["currency"] = _safe(info.get("currency"), "USD")
    m["exchange"] = _safe(info.get("exchange"), "")

    cp = _safe(info.get("currentPrice")) or _safe(info.get("regularMarketPrice"))
    if cp is None and not hist.empty:
        cp = float(hist["Close"].iloc[-1])
    m["price"] = cp
    if not cp:
        # Last resort: try to pull price from hist directly
        hist_raw2 = raw.get("hist")
        if isinstance(hist_raw2, pd.DataFrame) and not hist_raw2.empty:
            cp = float(hist_raw2["Close"].iloc[-1])
            m["price"] = cp
        if not cp:
            return None  # truly no price anywhere

    m["52w_high"] = _safe(info.get("fiftyTwoWeekHigh")) or (float(hist["High"].max()) if not hist.empty else None)
    m["52w_low"]  = _safe(info.get("fiftyTwoWeekLow"))  or (float(hist["Low"].min())  if not hist.empty else None)
    m["mktcap"]   = _safe(info.get("marketCap"))
    m["beta"]     = _safe(info.get("beta"), 1.0)

    m["pe"]       = _safe(info.get("trailingPE"))
    m["fwd_pe"]   = _safe(info.get("forwardPE"))
    m["peg"]      = _safe(info.get("pegRatio"))
    m["pb"]       = _safe(info.get("priceToBook"))
    m["ps"]       = _safe(info.get("priceToSalesTrailing12Months"))
    m["ev_ebit"]  = _safe(info.get("enterpriseToEbitda"))

    m["rev_growth"]    = _safe(info.get("revenueGrowth"))
    m["earn_growth"]   = _safe(info.get("earningsGrowth"))
    m["roe"]           = _safe(info.get("returnOnEquity"))
    m["roa"]           = _safe(info.get("returnOnAssets"))
    m["profit_margin"] = _safe(info.get("profitMargins"))
    m["gross_margin"]  = _safe(info.get("grossMargins"))
    m["op_margin"]     = _safe(info.get("operatingMargins"))
    m["de_ratio"]      = _safe(info.get("debtToEquity"))
    m["current_ratio"] = _safe(info.get("currentRatio"))

    m["fcf"] = _safe(info.get("freeCashflow"))
    if m["fcf"] is None and not cashflow.empty:
        try:
            ocf_rows = [r for r in cashflow.index if "operating" in str(r).lower()]
            cap_rows = [r for r in cashflow.index if "capital" in str(r).lower()]
            if ocf_rows:
                ocf  = float(cashflow.loc[ocf_rows[0]].iloc[0])
                capx = float(cashflow.loc[cap_rows[0]].iloc[0]) if cap_rows else 0.0
                m["fcf"] = ocf - abs(capx)
        except Exception:
            pass

    mc = m.get("mktcap"); fc = m.get("fcf")
    m["fcf_yield"] = (fc / mc) if (fc and mc and mc > 0) else None

    m["short_pct"]      = _safe(info.get("shortPercentOfFloat"))
    m["target_price"]   = _safe(info.get("targetMeanPrice"))
    m["analyst_rec"]    = _safe(info.get("recommendationMean"))
    m["analyst_cnt"]    = _safe(info.get("numberOfAnalystOpinions"))
    m["div_yield"]      = _safe(info.get("dividendYield"))
    tp = m.get("target_price")
    m["analyst_upside"] = (tp / cp - 1) if (tp and cp and cp > 0) else None

    # ── Technicals ─────────────────────────────────────────────────────────────
    if not hist.empty and len(hist) >= 20:
        close = hist["Close"].astype(float)
        high  = hist["High"].astype(float)
        low   = hist["Low"].astype(float)

        for period, key in [(20,"sma20"),(50,"sma50"),(200,"sma200")]:
            m[key] = float(close.rolling(period).mean().iloc[-1]) if len(hist) >= period else None

        for key, base in [("pct_sma20","sma20"),("pct_sma50","sma50"),("pct_sma200","sma200")]:
            bv = m.get(base)
            m[key] = (cp / bv - 1) if (bv and cp) else None

        delta = close.diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rs    = gain / loss.replace(0, float("nan"))
        rsi_v = (100.0 - 100.0 / (1.0 + rs)).iloc[-1]
        m["rsi"] = float(rsi_v) if rsi_v == rsi_v else None

        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd  = ema12 - ema26
        sig   = macd.ewm(span=9, adjust=False).mean()
        m["macd_hist"] = float((macd - sig).iloc[-1])

        bb_mid = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        m["bb_upper"] = float((bb_mid + 2*bb_std).iloc[-1])
        m["bb_lower"] = float((bb_mid - 2*bb_std).iloc[-1])
        bw = m["bb_upper"] - m["bb_lower"]
        m["bb_pct"] = float((close.iloc[-1] - m["bb_lower"]) / bw) if bw != 0 else 0.5

        tr_parts = pd.concat([high-low, (high-close.shift(1)).abs(), (low-close.shift(1)).abs()], axis=1)
        m["atr"] = float(tr_parts.max(axis=1).rolling(14).mean().iloc[-1])

        m["ret_1m"]  = float(close.iloc[-1]/close.iloc[-21]-1) if len(close)>=21 else None
        m["ret_3m"]  = float(close.iloc[-1]/close.iloc[-63]-1) if len(close)>=63 else None
        m["ret_1y"]  = float(close.iloc[-1]/close.iloc[0]-1)
        m["vol_ann"] = float(close.pct_change().dropna().std() * (252**0.5))
    else:
        for key in ["sma20","sma50","sma200","pct_sma20","pct_sma50","pct_sma200",
                    "rsi","macd_hist","bb_upper","bb_lower","bb_pct","atr",
                    "ret_1m","ret_3m","ret_1y","vol_ann"]:
            m[key] = None

    m["intrinsic"] = _dcf(m)
    iv = m.get("intrinsic")
    m["mos"] = (iv / cp - 1) if (iv and cp and cp > 0) else None
    m["long_score"]  = _score_long(m)
    m["short_score"] = _score_short(m)
    return m


def _dcf(m):
    fcf = m.get("fcf"); mc = m.get("mktcap"); price = m.get("price")
    g1  = min(max(m.get("rev_growth") or 0.06, -0.05), 0.22)
    g2  = 0.03; r = 0.10
    if fcf and mc and mc > 0 and price and price > 0 and fcf > 0:
        shares = mc / price; fcf_ps = fcf / shares; pv = 0.0; f = fcf_ps
        for t in range(1, 6):
            f *= (1 + g1); pv += f / ((1+r)**t)
        tv = f*(1+g2)/(r-g2); pv += tv/((1+r)**5)
        return round(pv, 2)
    pe = m.get("pe") or m.get("fwd_pe")
    if pe and pe > 0 and price and price > 0:
        eps = price/pe; g = min(g1, 0.12)
        if r > g: return round(eps*(1+g)/(r-g), 2)
    return None


def _score_long(m):
    s = 50.0
    fy=m.get("fcf_yield"); mos=m.get("mos"); roe=m.get("roe"); rg=m.get("rev_growth")
    p200=m.get("pct_sma200"); rsi=m.get("rsi"); au=m.get("analyst_upside")
    pe=m.get("pe"); de=m.get("de_ratio"); mh=m.get("macd_hist"); ar=m.get("analyst_rec")
    if fy is not None:
        if fy>0.08:s+=15
        elif fy>0.05:s+=10
        elif fy>0.02:s+=5
        elif fy<0:s-=15
    if mos is not None:
        if mos>0.30:s+=12
        elif mos>0.15:s+=7
        elif mos>0:s+=3
        elif mos<-0.25:s-=10
    if roe is not None:
        if roe>0.25:s+=8
        elif roe>0.15:s+=5
        elif roe>0.08:s+=2
        elif roe<0:s-=8
    if rg is not None:
        if rg>0.15:s+=8
        elif rg>0.05:s+=4
        elif rg>0:s+=1
        elif rg<-0.05:s-=8
    if p200 is not None:
        if p200>0.05:s+=5
        elif p200>0:s+=2
        else:s-=5
    if rsi is not None:
        if 38<=rsi<=60:s+=5
        elif rsi<35:s+=3
        elif rsi>75:s-=5
    if au is not None:
        if au>0.20:s+=7
        elif au>0.10:s+=3
        elif au<-0.05:s-=4
    if pe is not None and pe>0:
        if pe<15:s+=5
        elif pe<22:s+=2
        elif pe>60:s-=6
        elif pe>100:s-=12
    if de is not None:
        if de<50:s+=3
        elif de>300:s-=5
    if mh is not None:s+=2 if mh>0 else -2
    if ar is not None:
        if ar<=1.8:s+=5
        elif ar<=2.3:s+=2
        elif ar>=4:s-=5
    return round(min(max(s, 0), 100), 1)


def _score_short(m):
    s = 50.0
    fy=m.get("fcf_yield"); mos=m.get("mos"); pe=m.get("pe"); roe=m.get("roe")
    p200=m.get("pct_sma200"); rsi=m.get("rsi"); rg=m.get("rev_growth")
    sp=m.get("short_pct"); de=m.get("de_ratio"); mh=m.get("macd_hist"); ar=m.get("analyst_rec")
    if fy is not None:
        if fy<-0.05:s+=15
        elif fy<0:s+=8
        elif fy>0.06:s-=10
    if mos is not None:
        if mos<-0.30:s+=12
        elif mos<-0.15:s+=7
        elif mos>0.20:s-=8
    if pe is not None:
        if pe>100:s+=12
        elif pe>60:s+=7
        elif pe>40:s+=3
        elif pe<15:s-=8
    if roe is not None:
        if roe<0:s+=10
        elif roe<0.05:s+=5
        elif roe>0.20:s-=7
    if p200 is not None:
        if p200<-0.10:s+=8
        elif p200<0:s+=4
        elif p200>0.05:s-=5
    if rsi is not None:
        if rsi>75:s+=8
        elif rsi>65:s+=4
        elif rsi<35:s-=5
    if rg is not None:
        if rg<-0.10:s+=10
        elif rg<0:s+=5
        elif rg>0.15:s-=7
    if sp is not None:
        if sp>0.20:s+=8
        elif sp>0.10:s+=4
    if de is not None:
        if de>400:s+=7
        elif de>200:s+=3
    if mh is not None:s+=3 if mh<0 else -2
    if ar is not None:
        if ar>=4:s+=6
        elif ar>=3.5:s+=3
        elif ar<=1.8:s-=5
    return round(min(max(s, 0), 100), 1)


# ─────────────────────────────────────────────────────────────────────────────
#  SECTOR SCAN — fetches tickers with progress, skips failures gracefully
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=2400, show_spinner=False)
def scan_sector(sector: str):
    tickers = SECTORS[sector]["tickers"]
    sub     = SECTORS[sector]["sub"]
    results = []
    for t in tickers:
        raw = get_raw(t)
        if raw is None:
            continue
        m = compute_metrics(raw)
        if m is None:
            continue
        m["sub_sector"] = sub.get(t, m.get("industry", "—"))
        results.append(m)
        time.sleep(0.2)  # gentle rate-limit spacing
    if not results:
        return {"longs": [], "shorts": [], "all": []}
    longs  = sorted(results, key=lambda x: x["long_score"],  reverse=True)[:5]
    shorts = sorted(results, key=lambda x: x["short_score"], reverse=True)[:5]
    return {"longs": longs, "shorts": shorts, "all": results}


# ─────────────────────────────────────────────────────────────────────────────
#  THESIS GENERATORS
# ─────────────────────────────────────────────────────────────────────────────
def long_thesis(m):
    t=m["ticker"]; n=m.get("name",t); cp=m.get("price"); iv=m.get("intrinsic")
    mos=m.get("mos"); fy=m.get("fcf_yield"); roe=m.get("roe"); rg=m.get("rev_growth")
    pm=m.get("profit_margin"); pe=m.get("pe"); au=m.get("analyst_upside"); p200=m.get("pct_sma200")
    lines = []
    if mos and mos>0.08 and iv and cp:
        lines.append("**Valuation Discount — {:.0%} Margin of Safety:** {} trades at ${:.2f}, approximately {:.0%} below our DCF-derived intrinsic value of ${:.2f}. This discount reflects near-term sentiment overhang rather than fundamental deterioration — a textbook asymmetric entry for patient capital.".format(mos,n,cp,mos,iv))
    elif pe and 0<pe<18:
        lines.append("**Compressed Multiple:** At {:.1f}× trailing earnings, {} trades at a meaningful discount to sector peers and its own 5-year historical average. The market is pricing in base-case deterioration the company's operational trajectory does not support.".format(pe,t))
    if fy and fy>0.025:
        lines.append("**High-Quality Cash Generation — {:.1%} FCF Yield:** {} converts revenues into free cash at a {:.1%} yield on market cap — exceeding the 10-year Treasury and most dividend yields in the sector. This FCF engine gives management full optionality: buybacks, debt paydown, or accretive M&A.".format(fy,t,fy))
    if roe and roe>0.12:
        lines.append("**Capital Allocation Discipline — {:.1%} ROE:** A Return on Equity of {:.1%} signals a structurally moated business with pricing power that competitors cannot easily replicate.".format(roe,roe))
    if rg and rg>0.04:
        lines.append("**Top-Line Momentum — {:.1%} Revenue Growth:** Expanding revenue at {:.1%} YoY confirms demand is accelerating — the necessary precondition for operating leverage to produce EPS growth that outpaces consensus estimates.".format(rg,rg))
    if pm and pm>0.08:
        lines.append("**Margin Resilience — {:.1%} Net Margin:** Net margin of {:.1%} places {} in the upper tier of its industry, signaling pricing power maintained despite broad cost inflation pressures.".format(pm,pm,t))
    if p200 and p200>0:
        lines.append("**Technical Confirmation:** Price is {:.1%} above the 200-day moving average — the primary institutional trend filter — confirming a sustained bid from systematic and long-only funds.".format(p200))
    if au and au>0.10:
        lines.append("**Sell-Side Alignment:** Consensus analyst price target implies {:.0%} upside from current levels, signaling Wall Street expects a near-term catalyst to close the gap between price and intrinsic value.".format(au))
    if not lines:
        lines.append("**Multi-Factor Screen Trigger:** {} cleared our proprietary quantitative screen across valuation, capital quality, earnings momentum, and technical trend dimensions — presenting a favorable risk/reward skew relative to sector peers.".format(t))
    return "\n\n".join(lines)


def short_thesis(m):
    t=m["ticker"]; n=m.get("name",t); cp=m.get("price"); iv=m.get("intrinsic")
    mos=m.get("mos"); fy=m.get("fcf_yield"); roe=m.get("roe"); rg=m.get("rev_growth")
    pe=m.get("pe"); de=m.get("de_ratio"); sp=m.get("short_pct"); p200=m.get("pct_sma200")
    lines = []
    if mos and mos<-0.20 and iv and cp:
        lines.append("**Structural Overvaluation — {:.0%} Premium to Intrinsic Value:** At ${:.2f}, {} trades at a {:.0%} premium to our DCF-derived fair value of ${:.2f}. The embedded growth assumptions are heroic relative to the company's actual guidance trajectory. Reversion to fundamental value alone implies significant downside.".format(abs(mos),cp,n,abs(mos),iv))
    elif pe and pe>50:
        lines.append("**Multiple at Serious Risk — {:.1f}× Trailing Earnings:** At {:.1f}× earnings, {} is priced for perfection — yet even modest multiple compression toward the sector median implies double-digit equity losses.".format(pe,pe,t))
    if fy is not None and fy<0:
        lines.append("**Negative Free Cash Flow — Burning {:.1%} of Market Cap:** {} is not generating cash — it is consuming it. In a credit-tightening environment, this dependency on capital markets becomes an existential risk the equity has not yet discounted.".format(abs(fy),t))
    if roe is not None and roe<0.05:
        lines.append("**Return Profile in Decline — {:.1%} ROE:** A sub-5% ROE signals management is destroying capital or facing insurmountable competitive headwinds. Without a credible ROE recovery thesis, the current multiple is unjustified.".format(roe))
    if rg is not None and rg<0:
        lines.append("**Revenue Contraction — {:.1%} YoY:** A shrinking top line triggers a compounding feedback loop: declining revenues → operating deleverage → EPS misses → downward revisions → multiple compression — each stage creating additional selling pressure.".format(rg))
    if de and de>200:
        lines.append("**Leverage Vulnerability — {:.0f}% D/E:** {}'s debt-to-equity of {:.0f}% leaves it acutely exposed to credit market deterioration or sustained elevated rates. Rising interest expense directly erodes equity cash flows.".format(de,t,de))
    if p200 and p200<-0.05:
        lines.append("**Technical Breakdown — {:.1%} Below 200-Day MA:** The stock has broken below its key long-term trend line, triggering systematic selling from quantitative strategies — a technical headwind layered on top of deteriorating fundamentals.".format(abs(p200)))
    if sp and sp>0.08:
        lines.append("**Institutional Short Interest — {:.1%} of Float:** Institutions with primary research access have already established significant short positions, confirming rather than contradicting the bearish thesis.".format(sp))
    if not lines:
        lines.append("**Quantitative Bearish Trigger:** {} has triggered our multi-factor bearish model, exhibiting deteriorating fundamental momentum, stretched valuation, and negative technical structure relative to sector peers.".format(t))
    return "\n\n".join(lines)


def trade_setup(m, bias):
    cp=m.get("price") or 0.0; atr=m.get("atr") or cp*0.02
    iv=m.get("intrinsic"); at=m.get("target_price"); vol=m.get("vol_ann") or 0.30
    if bias=="LONG":
        entry=cp; stop=round(cp-1.5*atr,2)
        if iv and iv>cp: t1=round(cp+(iv-cp)*0.55,2); t2=round(iv,2)
        elif at and at>cp: t1=round(cp+(at-cp)*0.60,2); t2=round(at,2)
        else: t1=round(cp*1.15,2); t2=round(cp*1.28,2)
        rr=round((t1-entry)/max(entry-stop,0.01),1)
        if vol<0.28:
            strike=round(cp*1.02/5)*5
            opts={"strategy":"Long ATM Call — Buy ${:.0f} Strike, 90-Day Expiry".format(strike),"rationale":"Low implied volatility makes options inexpensive. Unlimited upside with loss capped at premium paid.","max_risk":"Premium paid","leverage":"~4–6× delta vs. equity"}
        else:
            bs=round(cp/5)*5; ss=round(cp*1.18/5)*5
            opts={"strategy":"Bull Call Spread — Buy ${:.0f} / Sell ${:.0f} Call, 90 Days".format(bs,ss),"rationale":"Elevated IV inflates premiums. Spread sells an OTM call to reduce net debit by 40–60%, capturing the core upside move.","max_risk":"Net debit paid","leverage":"Max gain = ${:.0f}/share".format(ss-bs)}
        return {"bias":"LONG","entry":"${:.2f}".format(entry),"entry_note":"Limit at ${:.2f} on any 1–2% intraday dip".format(entry*0.99),"stop":"${:.2f}  ({:.1f}% below entry)".format(stop,(entry-stop)/entry*100),"target_1":"${:.2f}  (+{:.1f}% — take 50% here)".format(t1,(t1-entry)/entry*100),"target_2":"${:.2f}  (+{:.1f}% — full target)".format(t2,(t2-entry)/entry*100),"rr":"{:.1f} : 1".format(rr),"sizing":"≤2% portfolio risk. Size = (2% × portfolio) ÷ (entry − stop)","catalyst_window":"60–120 days","options":opts}
    else:
        entry=cp; stop=round(cp+1.5*atr,2)
        if iv and iv<cp: t1=round(cp-(cp-iv)*0.50,2); t2=round(max(iv*1.03,cp*0.70),2)
        else: t1=round(cp*0.85,2); t2=round(cp*0.72,2)
        rr=round((entry-t1)/max(stop-entry,0.01),1)
        bs=round(cp/5)*5; ss=round(cp*0.80/5)*5
        if vol<0.32: opts={"strategy":"Long ATM Put — Buy ${:.0f} Strike, 60-Day Expiry".format(bs),"rationale":"Long puts deliver convex downside capture with max loss capped at premium paid — no unlimited upside risk of equity short.","max_risk":"Premium paid","leverage":"~4× delta downside"}
        else: opts={"strategy":"Bear Put Spread — Buy ${:.0f} / Sell ${:.0f} Put, 60 Days".format(bs,ss),"rationale":"High IV inflates put premiums. Selling the lower-strike put reduces net debit by 30–50% while preserving downside capture.","max_risk":"Net debit paid","leverage":"Max gain = ${:.0f}/share".format(bs-ss)}
        return {"bias":"SHORT","entry":"${:.2f}".format(entry),"entry_note":"Short on bounce to ${:.2f} for tighter entry".format(entry*1.02),"stop":"${:.2f}  ({:.1f}% above entry)".format(stop,(stop-entry)/entry*100),"target_1":"${:.2f}  (−{:.1f}% — cover 50%)".format(t1,(entry-t1)/entry*100),"target_2":"${:.2f}  (−{:.1f}% — full cover)".format(t2,(entry-t2)/entry*100),"rr":"{:.1f} : 1".format(rr),"sizing":"Use options to cap upside risk. Never short without defined stop. ≤2% portfolio risk.","catalyst_window":"30–60 days","options":opts}


def hedge_suggestion(m):
    sector=m.get("sector",""); t=m["ticker"]
    etf=SECTORS.get(sector,{}).get("etf","SPY")
    return ("**Pair Trade — Long {} / Short {} (3:1 Notional Ratio):** Shorting the sector ETF ({}) "
            "at ~one-third the notional of your {} position neutralizes approximately 60–75% of systematic "
            "sector beta — isolating pure idiosyncratic alpha from your thesis.\n\n"
            "**Tail-Risk Hedge:** Purchase {} put options 15–20% OTM with 90-day expiry, sizing the "
            "premium at no more than 0.5% of total portfolio. Caps max drawdown without forfeiting "
            "the core upside thesis.").format(t,etf,etf,t,t)


def catalysts_risks(m, bias):
    t=m["ticker"]; de=m.get("de_ratio")
    if bias=="LONG":
        return ("**Catalyst 1 — Earnings Beat & Guidance Raise:** The next quarterly report is the most "
                "likely near-term catalyst. A beat-and-raise would attack current pessimism and trigger "
                "rapid multiple re-rating.\n\n"
                "**Catalyst 2 — Capital Allocation Announcement:** Any accelerated buyback, special "
                "dividend, or accretive acquisition signals management views shares as undervalued.\n\n"
                "**Risk 1 — Macro / Rates:** A renewed spike in long-duration yields compresses equity "
                "multiples broadly. Mitigate with appropriate sizing and defined stop.\n\n"
                "**Risk 2 — Execution Miss:** Exit if operating margin contracts more than 200bps vs. "
                "the prior year comparison on the next earnings call.").format(t=t)
    else:
        lev = "elevated leverage ({:.0f}% D/E)".format(de) if de and de>100 else "business model dependencies"
        return ("**Catalyst 1 — Earnings Miss & Downward Revision:** Any guidance cut, margin miss, or "
                "revenue shortfall could accelerate re-rating toward fair value.\n\n"
                "**Catalyst 2 — Credit/Liquidity Event:** Given {}'s {}, any credit market tightening "
                "or failed debt refinancing could trigger a feedback loop compressing equity value.\n\n"
                "**Risk 1 — Short Squeeze:** High short interest creates vulnerability to a technical "
                "squeeze. Use long puts rather than outright equity short to define max loss.\n\n"
                "**Risk 2 — M&A Takeout:** A strategic acquirer at a premium would immediately invalidate "
                "the short thesis. Monitor SEC 13D/13G filings closely.").format(t, lev)


# ─────────────────────────────────────────────────────────────────────────────
#  PRICE CHART
# ─────────────────────────────────────────────────────────────────────────────
def price_chart(m, hist):
    if hist is None or hist.empty: return go.Figure()
    close=hist["Close"].astype(float); high=hist["High"].astype(float); low=hist["Low"].astype(float)
    fig=make_subplots(rows=3,cols=1,shared_xaxes=True,vertical_spacing=0.025,row_heights=[0.60,0.20,0.20])
    fig.add_trace(go.Candlestick(x=hist.index,open=hist["Open"],high=hist["High"],low=hist["Low"],close=hist["Close"],name="Price",increasing_line_color="#00d4aa",decreasing_line_color="#ff4d6d",increasing_fillcolor="#00d4aa22",decreasing_fillcolor="#ff4d6d22",line=dict(width=1)),row=1,col=1)
    for name_,p,color,dash in [("SMA 20",20,"#60a5fa","solid"),("SMA 50",50,"#f59e0b","solid"),("SMA 200",200,"#a78bfa","dot")]:
        if len(hist)>=p: fig.add_trace(go.Scatter(x=hist.index,y=close.rolling(p).mean(),name=name_,line=dict(color=color,width=1.3,dash=dash),opacity=0.85),row=1,col=1)
    if len(hist)>=20:
        bb_m=close.rolling(20).mean(); bb_s=close.rolling(20).std()
        fig.add_trace(go.Scatter(x=hist.index,y=bb_m+2*bb_s,line=dict(color="rgba(59,130,246,0.3)",width=0.8,dash="dash"),showlegend=False,name="BB Upper"),row=1,col=1)
        fig.add_trace(go.Scatter(x=hist.index,y=bb_m-2*bb_s,line=dict(color="rgba(59,130,246,0.3)",width=0.8,dash="dash"),fill="tonexty",fillcolor="rgba(59,130,246,0.04)",showlegend=False,name="BB Lower"),row=1,col=1)
    iv=m.get("intrinsic")
    if iv: fig.add_hline(y=iv,line_color="#f59e0b",line_dash="longdash",line_width=1.5,annotation_text="DCF IV ${:.2f}".format(iv),annotation_font_color="#f59e0b",annotation_position="right",row=1,col=1)
    vol_colors=["#00d4aa44" if float(c)>=float(o) else "#ff4d6d44" for c,o in zip(hist["Close"],hist["Open"])]
    fig.add_trace(go.Bar(x=hist.index,y=hist["Volume"],name="Volume",marker_color=vol_colors,showlegend=False),row=2,col=1)
    delta=close.diff(); gain=delta.clip(lower=0).rolling(14).mean(); loss=(-delta.clip(upper=0)).rolling(14).mean()
    rs=gain/loss.replace(0,float("nan")); rsi=100.0-100.0/(1.0+rs)
    fig.add_trace(go.Scatter(x=hist.index,y=rsi,name="RSI(14)",line=dict(color="#e879f9",width=1.5)),row=3,col=1)
    fig.add_hrect(y0=70,y1=100,fillcolor="#ff4d6d",opacity=0.06,row=3,col=1)
    fig.add_hrect(y0=0,y1=30,fillcolor="#00d4aa",opacity=0.06,row=3,col=1)
    fig.add_hline(y=70,line_color="#ff4d6d55",line_dash="dot",line_width=0.8,row=3,col=1)
    fig.add_hline(y=30,line_color="#00d4aa55",line_dash="dot",line_width=0.8,row=3,col=1)
    fig.add_hline(y=50,line_color="#ffffff18",line_dash="dot",line_width=0.5,row=3,col=1)
    fig.update_layout(template="plotly_dark",paper_bgcolor="#050a14",plot_bgcolor="#07111f",font=dict(family="IBM Plex Mono",color="#7a9cc0",size=10),xaxis_rangeslider_visible=False,height=560,margin=dict(l=5,r=5,t=15,b=5),legend=dict(orientation="h",y=1.03,x=0,bgcolor="rgba(0,0,0,0)",font=dict(size=10)))
    for row in range(1,4): fig.update_xaxes(showgrid=True,gridcolor="#0d1e30",gridwidth=0.5,row=row,col=1); fig.update_yaxes(showgrid=True,gridcolor="#0d1e30",gridwidth=0.5,row=row,col=1)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
#  UI RENDERERS
# ─────────────────────────────────────────────────────────────────────────────
def render_news(ticker):
    section_label("MULTI-SOURCE NEWS · 8 FEEDS — YAHOO · REUTERS · CNBC · MARKETWATCH · SEEKING ALPHA · BARRON'S · BENZINGA · GOOGLE")
    edu_box("News aggregated live from 8 independent RSS feeds simultaneously, deduplicated by title.")
    with st.spinner("Aggregating news from 8 sources for {}...".format(ticker)):
        items = fetch_multi_news(ticker)
    if not items:
        warn_box("No news found across RSS feeds for {}. This ticker may not have enough coverage.".format(ticker))
        return
    for item in items[:16]:
        src=item["source"]; color=NEWS_COLORS.get(src,"#3a5a80")
        st.markdown(
            '<div class="news-row"><div class="news-title">'
            '<a href="{}" target="_blank">{}</a>'
            '<span style="background:{c}18;border:1px solid {c}40;color:{c};padding:1px 6px;border-radius:3px;font-family:\'IBM Plex Mono\',monospace;font-size:.58rem;margin-left:6px;">{}</span>'
            '</div><div class="news-meta">{}</div></div>'.format(
                item["link"],item["title"],item["source"],item["date"],c=color),
            unsafe_allow_html=True)


def render_sec_filings(ticker):
    section_label("SEC EDGAR FILINGS · 8-K · 10-K · 10-Q · DEF 14A")
    edu_box("Live EDGAR filings via public Atom RSS. 8-K = material events (earnings, M&A, exec changes). 10-K = annual report. 10-Q = quarterly report. DEF 14A = proxy statement.")
    with st.spinner("Fetching SEC filings from EDGAR for {}...".format(ticker)):
        filings = fetch_sec_filings(ticker)
    if not filings:
        warn_box("No recent EDGAR filings found for {}. Foreign-listed companies may use a different CIK structure.".format(ticker))
        return
    badge_map={"8-K":"badge-8k","10-K":"badge-10k","10-Q":"badge-10q","DEF 14A":"badge-def"}
    for f in filings:
        st.markdown(
            '<div class="filing-row"><span class="filing-badge {badge}">{form}</span>'
            '<div style="flex:1;"><a href="{link}" target="_blank" style="color:#7ab0d8;text-decoration:none;font-size:.84rem;">{title}</a>'
            '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.62rem;color:#2a4a6a;margin-top:3px;">{date} · {summary}</div>'
            '</div></div>'.format(badge=badge_map.get(f["form"],"badge-other"),**f),
            unsafe_allow_html=True)


def render_analyst_activity(raw, ticker):
    section_label("ANALYST ACTIVITY · YFINANCE DATABASE + FINVIZ LIVE SCRAPE")
    edu_box("Two sources combined: yfinance pulls the historical upgrade/downgrade database from SEC disclosures. finviz.com is scraped for the live Wall Street ratings table with price targets.")
    col_yf, col_fv = st.columns(2)
    with col_yf:
        st.markdown('<div class="sec-label" style="font-size:.6rem;margin-top:0;">📊 YFINANCE · ANALYST CHANGES</div>', unsafe_allow_html=True)
        upgrades_df = raw.get("upgrades") if raw else None
        if upgrades_df is not None and isinstance(upgrades_df, pd.DataFrame) and not upgrades_df.empty:
            try:
                df = upgrades_df.copy()
                if not isinstance(df.index, pd.MultiIndex):
                    df.index = pd.to_datetime(df.index, errors="coerce")
                    df = df.sort_index(ascending=False).head(10).reset_index()
                col_lwr = {c.lower(): c for c in df.columns}
                action_col=next((col_lwr[k] for k in col_lwr if "action" in k),None)
                firm_col=next((col_lwr[k] for k in col_lwr if "firm" in k),None)
                to_col=next((col_lwr[k] for k in col_lwr if "tograde" in k or "to grade" in k),None)
                date_col=df.columns[0]
                for _, row in df.head(9).iterrows():
                    action=str(row[action_col]).strip() if action_col else ""
                    firm=str(row[firm_col]).strip() if firm_col else "—"
                    to_gr=str(row[to_col]).strip() if to_col else ""
                    date_v=str(row.get(date_col,""))[:10]
                    al=action.lower()
                    chip="chip-upgrade" if ("upgrade" in al or "initiat" in al or "raised" in al) else "chip-downgrade" if ("downgrade" in al or "lower" in al) else "chip-hold"
                    st.markdown('<div class="analyst-row"><div><div class="analyst-firm">{}</div><div class="analyst-date">{}</div></div><div style="text-align:right;"><span class="{}">{}</span><div class="analyst-date" style="margin-top:3px;">{}</div></div></div>'.format(firm,date_v,chip,action,to_gr),unsafe_allow_html=True)
            except Exception:
                warn_box("Could not parse upgrade data from yfinance for this ticker.")
        else:
            warn_box("No upgrade/downgrade history in yfinance for {}.".format(ticker))
    with col_fv:
        st.markdown('<div class="sec-label" style="font-size:.6rem;margin-top:0;">🌐 FINVIZ · LIVE RATINGS</div>', unsafe_allow_html=True)
        with st.spinner("Scraping finviz for {}...".format(ticker)):
            ratings = fetch_finviz_ratings(ticker)
        if ratings:
            for r in ratings[:8]:
                al=r.get("action","").lower()
                chip="chip-upgrade" if ("upgrade" in al or "initiat" in al or "raised" in al) else "chip-downgrade" if ("downgrade" in al or "lower" in al) else "chip-hold"
                pt_str="PT {}".format(r.get("pt","")) if r.get("pt") else ""
                st.markdown('<div class="analyst-row"><div><div class="analyst-firm">{}</div><div class="analyst-date">{}</div></div><div style="text-align:right;"><span class="{}">{}</span><div class="analyst-pt" style="margin-top:3px;">{} {}</div></div></div>'.format(r.get("firm",""),r.get("date",""),chip,r.get("action",""),r.get("rating",""),pt_str),unsafe_allow_html=True)
        else:
            warn_box("Finviz scrape returned no data — site may be rate-limiting. yfinance data on the left is authoritative.")


def render_institutional(raw):
    section_label("INSTITUTIONAL OWNERSHIP · TOP 13-F HOLDERS")
    edu_box("Institutional 13-F filings sourced via yfinance. Institutions holding >5% of shares must disclose positions quarterly.")
    holders_df=raw.get("holders") if raw else None
    if holders_df is None or not isinstance(holders_df,pd.DataFrame) or holders_df.empty:
        warn_box("Institutional holder data not available for this ticker.")
        return
    try:
        df=holders_df.head(10); col_lwr={c.lower():c for c in df.columns}
        name_col=next((col_lwr[k] for k in col_lwr if "holder" in k or "name" in k),df.columns[0])
        pct_col=next((col_lwr[k] for k in col_lwr if "%" in k or "pct" in k or "share" in k),None)
        val_col=next((col_lwr[k] for k in col_lwr if "value" in k),None)
        hc1,hc2,hc3=st.columns([3,2,2])
        hc1.markdown('<div class="m-label">Institution</div>',unsafe_allow_html=True)
        hc2.markdown('<div class="m-label">% of Shares</div>',unsafe_allow_html=True)
        hc3.markdown('<div class="m-label">Market Value</div>',unsafe_allow_html=True)
        for _,row in df.iterrows():
            name=str(row[name_col]) if name_col else "—"
            pct="{:.2f}%".format(float(row[pct_col])*100) if pct_col and not pd.isna(row[pct_col]) else "—"
            val=fmt_large(float(row[val_col])) if val_col and not pd.isna(row[val_col]) else "—"
            c1,c2,c3=st.columns([3,2,2])
            rs="font-family:'IBM Plex Mono',monospace;font-size:.77rem;padding:5px 0;border-bottom:1px solid #0c1e30;"
            c1.markdown('<div style="{}color:#c8deff;">{}</div>'.format(rs,name),unsafe_allow_html=True)
            c2.markdown('<div style="{}color:#f59e0b;">{}</div>'.format(rs,pct),unsafe_allow_html=True)
            c3.markdown('<div style="{}color:#60a5fa;">{}</div>'.format(rs,val),unsafe_allow_html=True)
    except Exception:
        warn_box("Could not parse institutional holder table.")


# ─────────────────────────────────────────────────────────────────────────────
#  DEEP-DIVE REPORT
# ─────────────────────────────────────────────────────────────────────────────
def render_deep_dive(m, raw, bias):
    t=m["ticker"]; n=m.get("name",t); cp=m.get("price",0)
    hist=raw.get("hist",pd.DataFrame()) if raw else pd.DataFrame()
    ls=m.get("long_score",50); ss=m.get("short_score",50)

    st.markdown(
        '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">'
        '<div><span style="font-family:\'IBM Plex Mono\',monospace;font-size:.64rem;color:#3a5a80;text-transform:uppercase;">DEEP-DIVE REPORT · MULTI-SOURCE</span>'
        '<div style="font-family:\'Outfit\',sans-serif;font-weight:800;font-size:1.45rem;color:#e8f0ff;letter-spacing:-.02em;">{t} &nbsp;<span style="font-size:.88rem;font-weight:400;color:#4a7296;">{n}</span></div>'
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.69rem;color:#2a4a6a;margin-top:4px;">{sub}</div></div>'
        '<div style="text-align:right;"><div style="font-family:\'IBM Plex Mono\',monospace;font-size:1.75rem;font-weight:700;color:#e8f0ff;">${cp:.2f}</div>'
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.67rem;color:#3a5a80;">{curr} · {exch}</div></div></div>'.format(
            t=t,n=n,sub=m.get("sub_sector",m.get("industry","")),cp=cp,curr=m.get("currency","USD"),exch=m.get("exchange","")),
        unsafe_allow_html=True)

    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown("**Long Score**"); st.markdown(score_bar_html(ls,"#00d4aa"),unsafe_allow_html=True)
    with c2: st.markdown("**Short Score**"); st.markdown(score_bar_html(ss,"#ff4d6d"),unsafe_allow_html=True)
    with c3:
        rsi=m.get("rsi"); rsi_c="bear" if rsi and rsi>70 else "bull" if rsi and rsi<35 else "neu"
        st.markdown("**RSI (14)**"); st.markdown('<div class="m-val {}">{}</div>'.format(rsi_c,fmt_val(rsi,".1f")),unsafe_allow_html=True)
    with c4:
        ar=m.get("analyst_rec"); ar_c="bull" if ar and ar<2.5 else "bear" if ar and ar>3.5 else "neu"
        lbl_m={1:"Strong Buy",2:"Buy",3:"Hold",4:"Underperform",5:"Sell"}
        ar_lbl=lbl_m.get(round(ar) if ar else 0,"—")
        st.markdown("**Analyst Consensus**"); st.markdown('<div class="m-val {}" style="font-size:.84rem;">{} ({})</div>'.format(ar_c,ar_lbl,fmt_val(ar,".2f")),unsafe_allow_html=True)

    tiles=[
        ("Market Cap",   fmt_large(m.get("mktcap")),          "neu"),
        ("Trailing P/E", fmt_val(m.get("pe"),".1f","×"),      color_class(m.get("pe"),0,True) if m.get("pe") else "neu"),
        ("Fwd P/E",      fmt_val(m.get("fwd_pe"),".1f","×"), "neu"),
        ("EV/EBITDA",    fmt_val(m.get("ev_ebit"),".1f","×"),"neu"),
        ("FCF Yield",    fmt_pct(m.get("fcf_yield")),          color_class(m.get("fcf_yield"))),
        ("ROE",          fmt_pct(m.get("roe")),                color_class(m.get("roe"),0.08)),
        ("Net Margin",   fmt_pct(m.get("profit_margin")),      color_class(m.get("profit_margin"))),
        ("Rev Growth",   fmt_pct(m.get("rev_growth")),         color_class(m.get("rev_growth"))),
        ("D/E Ratio",    fmt_val(m.get("de_ratio"),".0f","%"), color_class(m.get("de_ratio"),200,True)),
        ("Beta",         fmt_val(m.get("beta"),".2f"),         "neu"),
        ("DCF IV",       "${:.2f}".format(m["intrinsic"]) if m.get("intrinsic") else "N/A","amber"),
        ("Margin of Safety", fmt_pct(m.get("mos")),            color_class(m.get("mos"))),
    ]
    st.markdown(metric_tiles_html(tiles),unsafe_allow_html=True)
    edu_box("All metrics are fetched live via yfinance from SEC filings. DCF Intrinsic Value uses 5-year projected FCF discounted at 10% WACC with conservative capped growth assumptions.")

    section_label("PRICE ACTION · MOVING AVERAGES · BOLLINGER BANDS · RSI · VOLUME")
    if hist is not None and not hist.empty:
        st.plotly_chart(price_chart(m,hist),use_container_width=True)
    else:
        warn_box("Price history unavailable for {}.".format(t))

    render_news(t)
    render_sec_filings(t)
    render_analyst_activity(raw,t)
    render_institutional(raw)

    section_label("SECTION 1 · POSITION TYPE & OPTIMAL EXECUTION STRATEGY")
    bias_color="#00d4aa" if bias=="LONG" else "#ff4d6d"
    bias_label="LONG — High-Conviction Bull" if bias=="LONG" else "SHORT — High-Conviction Bear"
    setup=trade_setup(m,bias)
    st.markdown('<div class="report-box report-{cls}"><div style="font-family:\'IBM Plex Mono\',monospace;font-size:.77rem;color:{col};font-weight:700;margin-bottom:10px;">{arrow} BIAS: {lbl}</div><strong>Optimal Execution:</strong> {strat}<br><br><strong>Rationale:</strong> {rat}<br><br><strong>Max Risk:</strong> {risk} &nbsp;|&nbsp; <strong>Leverage:</strong> {lev}</div>'.format(cls="long" if bias=="LONG" else "short",col=bias_color,arrow="▲" if bias=="LONG" else "▼",lbl=bias_label,strat=setup["options"]["strategy"],rat=setup["options"]["rationale"],risk=setup["options"]["max_risk"],lev=setup["options"].get("leverage","—")),unsafe_allow_html=True)
    edu_box("Options strategy is dynamically determined by annualized realized volatility. Low-vol (<28%) → long naked call/put for maximum convexity. High-vol (>28%) → vertical spread to offset inflated premium.")

    section_label("SECTION 2 · IN-DEPTH FUNDAMENTAL & MACRO THESIS")
    thesis=long_thesis(m) if bias=="LONG" else short_thesis(m)
    st.markdown('<div class="report-box report-{}">{}</div>'.format("long" if bias=="LONG" else "short",thesis),unsafe_allow_html=True)
    edu_box("Every data point in the thesis is derived programmatically from real SEC-reported financials retrieved via yfinance — not hardcoded or estimated.")

    section_label("SECTION 3 · EXACT TRADE SETUP & STRUCTURE")
    c1,c2=st.columns(2)
    with c1:
        st.markdown('<div class="card"><div class="m-label">Entry Trigger</div><div class="m-val neu" style="font-size:.98rem;">{}</div><div style="font-size:.73rem;color:#3a5a80;margin-top:4px;">{}</div></div><div class="card"><div class="m-label">Stop / Invalidation</div><div class="m-val bear">{}</div></div>'.format(setup["entry"],setup["entry_note"],setup["stop"]),unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card"><div class="m-label">Target 1 (take 50% off)</div><div class="m-val bull">{}</div></div><div class="card"><div class="m-label">Target 2 (full thesis)</div><div class="m-val bull">{}</div></div>'.format(setup["target_1"],setup["target_2"]),unsafe_allow_html=True)
    st.markdown('<div style="display:flex;gap:10px;margin:8px 0;flex-wrap:wrap;"><div class="card card-sm" style="flex:1;"><div class="m-label">Risk/Reward</div><div class="m-val amber">{}</div></div><div class="card card-sm" style="flex:1;"><div class="m-label">Catalyst Window</div><div class="m-val neu">{}</div></div><div class="card card-sm" style="flex:2;"><div class="m-label">Position Sizing Rule</div><div style="font-size:.77rem;color:#6a9cc0;margin-top:4px;">{}</div></div></div>'.format(setup["rr"],setup["catalyst_window"],setup["sizing"]),unsafe_allow_html=True)
    edu_box("Stop-loss levels are set at 1.5× the 14-day Average True Range (ATR). ATR measures real volatility including gaps — placing stops beyond the ATR band avoids being shaken out by normal market noise.")

    section_label("SECTION 4 · CATALYSTS · RISKS · HEDGING STRUCTURE")
    st.markdown('<div class="report-box report-blue">{}</div>'.format(catalysts_risks(m,bias)),unsafe_allow_html=True)
    if bias=="LONG":
        st.markdown("**Recommended Hedging Structure:**")
        st.markdown('<div class="report-box report-amber">{}</div>'.format(hedge_suggestion(m)),unsafe_allow_html=True)
        edu_box("A pair trade (long stock / short sector ETF) neutralizes sector beta and isolates stock-specific alpha — how long/short equity funds generate returns uncorrelated with the S&P 500.")


# ─────────────────────────────────────────────────────────────────────────────
#  TAB: SECTOR SCANNER
# ─────────────────────────────────────────────────────────────────────────────
def tab_sector_scanner():
    section_label("11-GICS SECTOR SCANNER · CLICK A SECTOR TO BEGIN")
    st.markdown('<p style="color:#3a5a80;">Click any sector tile below to select it, then click Scan. The model fetches live data for each stock individually with retry logic, scores across FCF yield, DCF margin of safety, ROE, revenue growth, 200-MA trend, RSI, MACD, and analyst consensus.</p>', unsafe_allow_html=True)
    edu_box("Sector data is cached for 40 minutes after the first load to avoid rate-limiting. If a stock fails to fetch it is skipped gracefully — the scan continues with the remaining tickers.")

    if "selected_sector" not in st.session_state:
        st.session_state["selected_sector"] = "Information Technology"

    sector_list = list(SECTORS.keys())
    cols = st.columns(4)
    for i, sname in enumerate(sector_list):
        sdata = SECTORS[sname]
        is_sel = st.session_state["selected_sector"] == sname
        border = "border:2px solid #3b82f6;" if is_sel else "border:1px solid #0f2540;"
        bg     = "background:#0d2040;" if is_sel else "background:#071428;"
        nc     = "color:#60a5fa;" if is_sel else "color:#7a9cc0;"
        ec     = "color:#3b82f6;" if is_sel else "color:#2a4a6a;"
        with cols[i % 4]:
            if st.button(
                "{}\n{}\n{}".format(sdata["icon"], sname.replace(" ", "\n") if len(sname)>18 else sname, sdata["etf"]),
                key="sec_{}".format(i),
                use_container_width=True,
            ):
                st.session_state["selected_sector"] = sname
                if "scan_results_{}".format(sname) not in st.session_state:
                    st.rerun()

    selected = st.session_state["selected_sector"]
    info     = SECTORS[selected]

    st.markdown("""
    <div class="card" style="margin:14px 0 10px;display:flex;align-items:center;gap:14px;">
      <span style="font-size:2rem;">{icon}</span>
      <div>
        <div style="font-family:'Outfit',sans-serif;font-weight:700;font-size:1.05rem;color:#e8f0ff;">{name}</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:.63rem;color:#3a5a80;">SECTOR ETF: {etf} · {n} STOCKS · DATA: YFINANCE + EDGAR + 8-SOURCE NEWS</div>
      </div>
    </div>
    """.format(icon=info["icon"], name=selected, etf=info["etf"], n=len(info["tickers"])), unsafe_allow_html=True)

    cache_key = "scan_results_{}".format(selected)
    col_scan, _ = st.columns([1, 4])
    with col_scan:
        do_scan = st.button("⚡ Scan {}".format(info["etf"]), key="scan_btn", use_container_width=True)

    if do_scan:
        if cache_key in st.session_state:
            del st.session_state[cache_key]

    if cache_key not in st.session_state:
        with st.spinner("Scanning {} — fetching {} tickers one by one (this takes ~30s)...".format(selected, len(info["tickers"]))):
            results = scan_sector(selected)
        st.session_state[cache_key] = results
    else:
        results = st.session_state[cache_key]

    if not results.get("longs") and not results.get("shorts"):
        err_box("Scan returned no results for {}. yfinance may be temporarily rate-limiting — please wait 30 seconds and try again.".format(selected))
        if cache_key in st.session_state:
            del st.session_state[cache_key]
        return

    fetched = len(results.get("all", []))
    total   = len(info["tickers"])
    if fetched < total:
        warn_box("Fetched {}/{} tickers successfully. {} failed to load (rate-limited or unavailable) and were skipped.".format(fetched, total, total-fetched))

    col_l, col_s = st.columns(2)

    with col_l:
        st.markdown('<div class="sec-label" style="border-left-color:#00d4aa;color:#00d4aa;">▲ HIGH-CONVICTION LONG CANDIDATES</div>', unsafe_allow_html=True)
        edu_box("Ranked by composite long score. ≥65/100 = high conviction. Key drivers: FCF yield, DCF margin of safety, ROE quality, revenue momentum, technical trend, and analyst consensus.")
        if not results["longs"]:
            warn_box("No long candidates found — all tickers may have failed to fetch.")
        for m in results["longs"]:
            t=m["ticker"]; cp=m.get("price",0); ls=m.get("long_score",50)
            fy=m.get("fcf_yield"); mos=m.get("mos"); roe=m.get("roe"); rg=m.get("rev_growth")
            with st.expander("▲  {}  ·  {}  ·  Score {:.0f}/100".format(t, m.get("sub_sector","")[:35], ls)):
                st.markdown(
                    '<div style="display:flex;justify-content:space-between;margin-bottom:10px;">'
                    '<div><div style="font-size:.71rem;color:#3a5a80;">{name}</div>'
                    '<div class="m-val neu" style="font-size:1.2rem;">${cp:.2f}</div></div>'
                    '<div style="text-align:right;">{bar}</div></div>'
                    '<div class="metric-grid" style="grid-template-columns:repeat(4,1fr);">'
                    '<div class="metric-tile"><div class="m-label">FCF Yield</div><div class="m-val {fy_c}">{fy_v}</div></div>'
                    '<div class="metric-tile"><div class="m-label">Margin of Safety</div><div class="m-val {mos_c}">{mos_v}</div></div>'
                    '<div class="metric-tile"><div class="m-label">ROE</div><div class="m-val {roe_c}">{roe_v}</div></div>'
                    '<div class="metric-tile"><div class="m-label">Rev Growth</div><div class="m-val {rg_c}">{rg_v}</div></div></div>'.format(
                        name=m.get("name",t),cp=cp,bar=score_bar_html(ls,"#00d4aa"),
                        fy_c="bull" if fy and fy>0 else "bear",fy_v=fmt_pct(fy),
                        mos_c="bull" if mos and mos>0 else "bear",mos_v=fmt_pct(mos),
                        roe_c="bull" if roe and roe>0.12 else "neu",roe_v=fmt_pct(roe),
                        rg_c="bull" if rg and rg>0 else "bear",rg_v=fmt_pct(rg)),
                    unsafe_allow_html=True)
                st.markdown('<div class="report-box report-long" style="margin-top:8px;">{}</div>'.format(long_thesis(m)),unsafe_allow_html=True)
                ts=trade_setup(m,"LONG")
                st.markdown('<div style="display:flex;gap:5px;margin-top:8px;flex-wrap:wrap;"><span class="chip-long">Entry {}</span><span class="chip-short">Stop {}</span><span class="chip-long">T1 {}</span><span class="chip-long">T2 {}</span><span class="chip-blue">R/R {}</span></div>'.format(ts["entry"],ts["stop"].split("(")[0].strip(),ts["target_1"].split("(")[0].strip(),ts["target_2"].split("(")[0].strip(),ts["rr"]),unsafe_allow_html=True)

    with col_s:
        st.markdown('<div class="sec-label" style="border-left-color:#ff4d6d;color:#ff4d6d;">▼ HIGH-CONVICTION SHORT CANDIDATES</div>', unsafe_allow_html=True)
        edu_box("Ranked by composite short score. Key signals: negative FCF, P/E >2× sector median, declining ROE, revenue contraction, 200-MA breakdown, elevated short interest, and bearish analyst consensus.")
        if not results["shorts"]:
            warn_box("No short candidates found — all tickers may have failed to fetch.")
        for m in results["shorts"]:
            t=m["ticker"]; cp=m.get("price",0); ss_score=m.get("short_score",50)
            pe=m.get("pe"); fy=m.get("fcf_yield"); mos=m.get("mos"); rg=m.get("rev_growth")
            with st.expander("▼  {}  ·  {}  ·  Score {:.0f}/100".format(t, m.get("sub_sector","")[:35], ss_score)):
                st.markdown(
                    '<div style="display:flex;justify-content:space-between;margin-bottom:10px;">'
                    '<div><div style="font-size:.71rem;color:#3a5a80;">{name}</div>'
                    '<div class="m-val neu" style="font-size:1.2rem;">${cp:.2f}</div></div>'
                    '<div style="text-align:right;">{bar}</div></div>'
                    '<div class="metric-grid" style="grid-template-columns:repeat(4,1fr);">'
                    '<div class="metric-tile"><div class="m-label">FCF Yield</div><div class="m-val {fy_c}">{fy_v}</div></div>'
                    '<div class="metric-tile"><div class="m-label">Trailing P/E</div><div class="m-val {pe_c}">{pe_v}</div></div>'
                    '<div class="metric-tile"><div class="m-label">Margin of Safety</div><div class="m-val {mos_c}">{mos_v}</div></div>'
                    '<div class="metric-tile"><div class="m-label">Rev Growth</div><div class="m-val {rg_c}">{rg_v}</div></div></div>'.format(
                        name=m.get("name",t),cp=cp,bar=score_bar_html(ss_score,"#ff4d6d"),
                        fy_c="bear" if fy is None or fy<0 else "neu",fy_v=fmt_pct(fy),
                        pe_c="bear" if pe and pe>50 else "neu",pe_v=fmt_val(pe,".1f","×"),
                        mos_c="bear" if mos and mos<0 else "neu",mos_v=fmt_pct(mos),
                        rg_c="bear" if rg and rg<0 else "neu",rg_v=fmt_pct(rg)),
                    unsafe_allow_html=True)
                st.markdown('<div class="report-box report-short" style="margin-top:8px;">{}</div>'.format(short_thesis(m)),unsafe_allow_html=True)
                ts=trade_setup(m,"SHORT")
                st.markdown('<div style="display:flex;gap:5px;margin-top:8px;flex-wrap:wrap;"><span class="chip-short">Short {}</span><span class="chip-long">Stop {}</span><span class="chip-short">T1 {}</span><span class="chip-short">T2 {}</span><span class="chip-blue">R/R {}</span></div>'.format(ts["entry"],ts["stop"].split("(")[0].strip(),ts["target_1"].split("(")[0].strip(),ts["target_2"].split("(")[0].strip(),ts["rr"]),unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  TAB: TICKER DEEP-DIVE
# ─────────────────────────────────────────────────────────────────────────────
def tab_ticker_search():
    section_label("CUSTOM TICKER DEEP-DIVE · FULL 4-SECTION ANALYSIS")
    edu_box(
        "Enter any global ticker (NVDA, AAPL, TSLA, ASML, BHP…). The engine fetches from "
        "yfinance with 4 retry attempts + browser-session headers, SEC EDGAR filings, "
        "8 news RSS sources, and finviz.com analyst ratings — then generates the full report. "
        "If fundamentals are partially unavailable due to rate-limiting, price and chart data "
        "will still be shown."
    )

    c1, c2, c3 = st.columns([3, 1.5, 1])
    with c1:
        ticker_input = st.text_input(
            "Ticker", placeholder="e.g. NVDA, AAPL, MSFT, TSLA, ASML...",
            label_visibility="collapsed", key="ticker_input",
        ).upper().strip()
    with c2:
        bias_sel = st.selectbox(
            "Bias", ["AUTO-DETECT", "LONG", "SHORT"],
            key="bias_sel", label_visibility="collapsed",
        )
    with c3:
        go_btn = st.button("▶ Analyze", key="go_btn", use_container_width=True)

    if not ((go_btn or ticker_input) and ticker_input):
        return

    # ── Fetch with progress feedback ─────────────────────────────────────────
    progress_bar = st.progress(0, text="Connecting to yfinance...")
    status_text  = st.empty()

    status_text.markdown(
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.78rem;color:#3a5a80;">'
        '⟳ Fetching price history and fundamentals for {} (up to 4 attempts)...</div>'.format(ticker_input),
        unsafe_allow_html=True,
    )
    progress_bar.progress(20, text="Fetching data...")

    raw = get_raw(ticker_input)
    progress_bar.progress(60, text="Processing metrics...")

    if not raw:
        progress_bar.empty()
        status_text.empty()
        err_box(
            "Could not retrieve any data for **{}**. Possible reasons:\n\n"
            "• The ticker symbol is incorrect — double-check it (e.g. GOOGL not GOOGLE)\n"
            "• yfinance is temporarily rate-limiting Streamlit Cloud — wait 60 seconds and retry\n"
            "• The stock is delisted or traded on an exchange yfinance doesn't cover\n\n"
            "Try again in 60 seconds. If the issue persists, verify the ticker at finance.yahoo.com.".format(ticker_input)
        )
        return

    m = compute_metrics(raw)
    progress_bar.progress(80, text="Building report...")

    if not m:
        progress_bar.empty()
        status_text.empty()
        # Try to show at least what we got
        hist_raw = raw.get("hist")
        if hist_raw is not None and isinstance(hist_raw, pd.DataFrame) and not hist_raw.empty:
            last_price = float(hist_raw["Close"].iloc[-1])
            warn_box(
                "Fundamentals unavailable for {} (yfinance returned incomplete data), "
                "but price history was fetched. Last close: ${:.2f}. "
                "This usually means yfinance is rate-limiting — wait 60 seconds and retry.".format(
                    ticker_input, last_price)
            )
        else:
            err_box(
                "Data returned but unusable for **{}**. "
                "The ticker may be delisted, or yfinance is temporarily unavailable. "
                "Wait 60 seconds and try again.".format(ticker_input)
            )
        return

    progress_bar.progress(100, text="Done.")
    progress_bar.empty()
    status_text.empty()

    # ── Partial data warning ──────────────────────────────────────────────────
    if raw.get("partial"):
        warn_box(
            "Note: Fundamental data for {} is partial — yfinance returned limited info. "
            "Price chart and technical indicators are complete. "
            "Valuation metrics (P/E, FCF yield, DCF) may show N/A. "
            "Retry in 60 seconds for full data.".format(ticker_input)
        )

    # ── Resolve sub-sector ───────────────────────────────────────────────────
    for sname, sdata in SECTORS.items():
        if ticker_input in sdata["sub"]:
            m["sub_sector"] = sdata["sub"][ticker_input]
            break
    else:
        m["sub_sector"] = m.get("industry", "")

    # ── Auto-detect bias ─────────────────────────────────────────────────────
    if bias_sel == "AUTO-DETECT":
        bias = "LONG" if m.get("long_score", 50) >= m.get("short_score", 50) else "SHORT"
    else:
        bias = bias_sel

    render_deep_dive(m, raw, bias)


# ─────────────────────────────────────────────────────────────────────────────
#  TAB: MACRO DASHBOARD  — fixed: individual fetches, graceful fallbacks
# ─────────────────────────────────────────────────────────────────────────────
def tab_macro_dashboard():
    section_label("MACRO ENVIRONMENT DASHBOARD · RATES · FX · COMMODITIES · SECTOR HEATMAP")
    st.markdown('<p style="color:#3a5a80;">All macro data sourced live via yfinance — fetched one instrument at a time with retry logic to prevent failures. Cached for 30 minutes. Click Refresh to reload.</p>', unsafe_allow_html=True)
    edu_box("VIX above 25 = elevated fear and expensive options. An inverted yield curve (2Y > 10Y) historically precedes U.S. recessions by 12–18 months. DXY above 104 creates headwinds for U.S. multinational earnings.")

    col_r, _ = st.columns([1,5])
    with col_r:
        if st.button("🔄 Refresh Macro Data", key="macro_refresh"):
            st.cache_data.clear()

    with st.spinner("Fetching macro instruments one by one..."):
        mdata = get_macro_snapshot()

    if not mdata:
        err_box("Failed to fetch any macro data from yfinance. This is usually a temporary rate-limit — please wait 1 minute and click Refresh.")
        return

    loaded = len(mdata)
    total  = len(MACRO_SYMBOLS)
    if loaded < total:
        warn_box("Loaded {}/{} macro instruments. {} failed — likely temporary yfinance throttling. Showing available data.".format(loaded, total, total-loaded))

    # ── Indices ──────────────────────────────────────────────────────────────
    section_label("MAJOR MARKET INDICES")
    idx_items = [(lbl,d) for lbl,d in mdata.items() if d["type"]=="index"]
    if idx_items:
        cols = st.columns(min(len(idx_items), 5))
        for i,(lbl,d) in enumerate(idx_items):
            with cols[i % 5]:
                chg=d["chg"]; val=d["last"]; color="#00d4aa" if chg>=0 else "#ff4d6d"
                fmt=d.get("fmt",",.2f")
                try: val_str=("{:"+fmt+"}").format(val)
                except: val_str=str(round(val,2))
                st.markdown(
                    '<div class="macro-tile"><div class="m-label">{}</div>'
                    '<div class="macro-val">{}</div>'
                    '<div class="macro-chg" style="color:{};">{} {:+.2f}%</div></div>'.format(
                        lbl,val_str,color,"▲" if chg>=0 else "▼",chg*100),
                    unsafe_allow_html=True)
    else:
        warn_box("Index data unavailable — yfinance may be throttling. Try refreshing in 60 seconds.")

    # ── Yield curve ──────────────────────────────────────────────────────────
    section_label("U.S. TREASURY YIELD CURVE")
    rate_items = [(lbl,d) for lbl,d in mdata.items() if d["type"]=="rate"]
    col_yc, col_vix = st.columns([3,2])
    with col_yc:
        if rate_items:
            y_labels=[x[0] for x in rate_items]; y_vals=[x[1]["last"] for x in rate_items]
            fig_yc=go.Figure(go.Scatter(x=y_labels,y=y_vals,mode="lines+markers+text",text=["{:.2f}%".format(v) for v in y_vals],textposition="top center",line=dict(color="#3b82f6",width=2.5),marker=dict(color="#60a5fa",size=10),textfont=dict(family="IBM Plex Mono",color="#c8deff",size=11)))
            fig_yc.update_layout(template="plotly_dark",paper_bgcolor="#050a14",plot_bgcolor="#07111f",height=200,margin=dict(l=5,r=5,t=10,b=5),yaxis=dict(ticksuffix="%",showgrid=True,gridcolor="#0d1e30"),xaxis=dict(showgrid=False),font=dict(family="IBM Plex Mono",color="#7a9cc0",size=10))
            st.plotly_chart(fig_yc,use_container_width=True)
        else:
            warn_box("Treasury yield data unavailable.")
        edu_box("An inverted yield curve (short-term > long-term yields) has preceded every U.S. recession since 1970 by 12–18 months. Watch the 2Y–10Y spread.")
    with col_vix:
        vix_d=mdata.get("VIX")
        if vix_d:
            vv=vix_d["last"]; vc="#ff4d6d" if vv>25 else "#f59e0b" if vv>18 else "#00d4aa"
            vlbl="EXTREME FEAR" if vv>35 else "FEAR" if vv>25 else "ELEVATED" if vv>18 else "COMPLACENCY" if vv<13 else "NORMAL"
            st.markdown('<div class="card" style="text-align:center;padding:26px;"><div class="m-label">🌡️ CBOE VIX — FEAR GAUGE</div><div style="font-family:\'IBM Plex Mono\',monospace;font-size:2.8rem;font-weight:700;color:{c};margin:10px 0;">{v:.1f}</div><div style="font-family:\'IBM Plex Mono\',monospace;font-size:.73rem;color:{c};font-weight:700;letter-spacing:.15em;">{lbl}</div><div style="font-size:.71rem;color:#2a4a6a;margin-top:8px;line-height:1.5;">VIX &lt;15: Cheap calls<br>VIX 15–25: Normal<br>VIX &gt;25: Expensive options<br>VIX &gt;40: Crisis</div></div>'.format(c=vc,v=vv,lbl=vlbl),unsafe_allow_html=True)
        else:
            warn_box("VIX data unavailable.")

    # ── FX ───────────────────────────────────────────────────────────────────
    section_label("FOREIGN EXCHANGE  ·  DOLLAR INDEX & MAJOR PAIRS")
    fx_items=[(lbl,d) for lbl,d in mdata.items() if d["type"]=="fx"]
    if fx_items:
        fx_cols=st.columns(min(len(fx_items),4))
        for i,(lbl,d) in enumerate(fx_items):
            with fx_cols[i%4]:
                chg=d["chg"]; val=d["last"]; color="#00d4aa" if chg>=0 else "#ff4d6d"
                fmt=d.get("fmt",".4f")
                try: val_str=("{:"+fmt+"}").format(val)
                except: val_str=str(round(val,4))
                st.markdown('<div class="macro-tile"><div class="m-label">{}</div><div class="macro-val">{}</div><div class="macro-chg" style="color:{};">{} {:+.2f}%</div></div>'.format(lbl,val_str,color,"▲" if chg>=0 else "▼",chg*100),unsafe_allow_html=True)
    else:
        warn_box("FX data unavailable.")
    edu_box("A strong dollar (DXY ↑) is a headwind for U.S. multinationals — it reduces the dollar value of overseas revenues. Weakening DXY is generally bullish for commodities, gold, and EM assets.")

    # ── Commodities ──────────────────────────────────────────────────────────
    section_label("COMMODITY FUTURES  ·  GOLD · WTI CRUDE · COPPER")
    comm_items=[(lbl,d) for lbl,d in mdata.items() if d["type"]=="comm"]
    if comm_items:
        comm_cols=st.columns(min(len(comm_items),5))
        for i,(lbl,d) in enumerate(comm_items):
            with comm_cols[i%5]:
                chg=d["chg"]; val=d["last"]; color="#00d4aa" if chg>=0 else "#ff4d6d"
                fmt=d.get("fmt",",.2f")
                try: val_str="${:"+fmt+"}".format(val)
                except: val_str="$"+str(round(val,2))
                st.markdown('<div class="macro-tile"><div class="m-label">{}</div><div class="macro-val">{}</div><div class="macro-chg" style="color:{};">{} {:+.2f}%</div></div>'.format(lbl,val_str,color,"▲" if chg>=0 else "▼",chg*100),unsafe_allow_html=True)
    else:
        warn_box("Commodity data unavailable.")
    edu_box("Copper is nicknamed 'Dr. Copper' — a leading indicator of global industrial demand. Gold rising with equities = risk-on inflation hedge. Gold rising while equities fall = flight-to-safety.")

    # ── Sector heatmap ───────────────────────────────────────────────────────
    section_label("11-GICS SECTOR ETF PERFORMANCE HEATMAP")
    with st.spinner("Fetching sector ETF performance..."):
        sect_perf = get_sector_etf_perf()

    if sect_perf:
        labels=[]; values=[]
        for sname,sdata in SECTORS.items():
            d=sect_perf.get(sname)
            labels.append("{} {}".format(sdata["icon"],sdata["etf"]))
            values.append(d["chg"]*100 if d else 0.0)
        colors=["rgba(0,212,170,0.7)" if v>=0 else "rgba(255,77,109,0.7)" for v in values]
        border=["#00d4aa" if v>=0 else "#ff4d6d" for v in values]
        fig=go.Figure(go.Bar(x=values,y=labels,orientation="h",text=["{:+.2f}%".format(v) for v in values],textposition="outside",marker=dict(color=colors,line=dict(color=border,width=1)),textfont=dict(family="IBM Plex Mono",size=10,color="#c8deff")))
        fig.update_layout(template="plotly_dark",paper_bgcolor="#050a14",plot_bgcolor="#07111f",font=dict(family="IBM Plex Mono",color="#7a9cc0",size=10),height=360,margin=dict(l=5,r=60,t=10,b=5),xaxis=dict(showgrid=True,gridcolor="#0d1e30",zeroline=True,zerolinecolor="#1e3d6a",ticksuffix="%"),yaxis=dict(showgrid=False))
        st.plotly_chart(fig,use_container_width=True)
        edu_box("Sector ETFs are the official GICS benchmarks used by institutional PMs. XLU + XLP green + XLK red = defensive rotation = recession fears rising. The inverse = risk-on environment.")
    else:
        warn_box("Sector ETF performance data unavailable. Try refreshing in 60 seconds.")


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    st.markdown(
        '<div class="banner">'
        '<div><div class="banner-title">⚡ EQ · INTELLIGENCE TERMINAL</div>'
        '<div class="banner-sub">yfinance · SEC EDGAR · Reuters · CNBC · MarketWatch · Seeking Alpha · Barron\'s · Benzinga · finviz · v3.0</div>'
        '</div>'
        '<div style="text-align:right;">'
        '<div><span class="live-dot"></span><span class="live-text">LIVE · MULTI-SOURCE</span></div>'
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.7rem;color:#3a5a80;">{} UTC</div>'
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.59rem;color:#1e3450;margin-top:3px;">No API keys · Python 3.10+ compatible</div>'
        '</div></div>'.format(now),
        unsafe_allow_html=True)

    tabs = st.tabs(["🌐  Sector Scanner", "🔍  Ticker Deep-Dive", "📊  Macro Dashboard"])
    with tabs[0]: tab_sector_scanner()
    with tabs[1]: tab_ticker_search()
    with tabs[2]: tab_macro_dashboard()

    st.markdown(
        '<div style="margin-top:36px;padding-top:14px;border-top:1px solid #0c1e30;text-align:center;">'
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.61rem;color:#1e3450;letter-spacing:.07em;">'
        '⚡ EQ · INTELLIGENCE v3.0  ·  yfinance · SEC EDGAR · Reuters · CNBC · MarketWatch · Seeking Alpha · Barron\'s · Benzinga · finviz  ·  '
        'Zero API keys  ·  Educational & research purposes only  ·  Not investment advice'
        '</div></div>',
        unsafe_allow_html=True)


if __name__ == "__main__":
    main()
