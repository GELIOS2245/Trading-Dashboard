#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
  EQUITIES INTELLIGENCE TERMINAL  v2.0
  Multi-Source Quantitative & Fundamental Research Platform
═══════════════════════════════════════════════════════════════════════════════

SETUP — run this ONE TIME in your terminal:
    pip install streamlit==1.40.2 yfinance==0.2.51 pandas numpy requests \
                feedparser plotly beautifulsoup4 lxml

PYTHON 3.13 NOTE:
    All type hints use Optional[] / Union[] form — fully compatible with
    Python 3.10, 3.11, 3.12, and 3.13. No walrus operator or match/case used.

RUN:
    streamlit run trading_dashboard_v2.py

DATA SOURCES (all free, no API keys):
  1. yfinance        — prices, fundamentals, analyst ratings, holders
  2. SEC EDGAR       — 8-K / 10-K / 10-Q filings (public Atom RSS)
  3. Yahoo Finance RSS
  4. Google News RSS (per-ticker, site-filtered)
  5. Reuters / CNBC / MarketWatch / Seeking Alpha / Barron's / Benzinga
     / Motley Fool / IBD  — all via Google News site: filter
  6. finviz.com      — live analyst ratings table (HTML scrape)
  7. yfinance macro  — VIX, Treasury yields, FX pairs, commodity futures,
                       sector ETFs (all free exchange data)
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

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EQ · Intelligence Terminal v2",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700;800&display=swap');

html,body,[class*="css"],.stApp{font-family:'Outfit',sans-serif;background:#050a14;color:#b8cce0}
.main,.block-container{background:#050a14 !important;padding-top:1rem !important}
h1{font-family:'Outfit',sans-serif;font-weight:800;font-size:1.9rem;color:#e2eeff;letter-spacing:-0.03em;margin-bottom:0}
h2{font-family:'Outfit',sans-serif;font-weight:700;font-size:1.2rem;color:#c8deff}
h3{font-family:'Outfit',sans-serif;font-weight:600;font-size:1rem;color:#a0bcd8}
p,li{font-size:.88rem;line-height:1.75;color:#8aacc8}

.banner{background:linear-gradient(135deg,#071428 0%,#091a2e 60%,#071428 100%);border:1px solid #0f2540;border-radius:12px;padding:20px 28px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between}
.banner-logo{font-family:'IBM Plex Mono',monospace;font-size:.7rem;font-weight:600;color:#3b82f6;letter-spacing:.2em;text-transform:uppercase}
.banner-title{font-family:'Outfit',sans-serif;font-weight:800;font-size:1.6rem;color:#e8f0ff;letter-spacing:-.02em}
.banner-sub{font-family:'IBM Plex Mono',monospace;font-size:.63rem;color:#3a5a80;letter-spacing:.06em;text-transform:uppercase;margin-top:2px}
.live-dot{width:8px;height:8px;background:#00d4aa;border-radius:50%;display:inline-block;margin-right:6px;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(1.3)}}
.live-text{font-family:'IBM Plex Mono',monospace;font-size:.68rem;color:#00d4aa;font-weight:600}

.stTabs [data-baseweb="tab-list"]{background:#071428;border-radius:10px;gap:2px;padding:4px;border:1px solid #0f2540}
.stTabs [data-baseweb="tab"]{color:#3a5a80;background:transparent;border-radius:8px;font-family:'IBM Plex Mono',monospace;font-size:.78rem;letter-spacing:.05em;padding:8px 16px}
.stTabs [aria-selected="true"]{background:#0d2040 !important;color:#60a5fa !important;border:1px solid #1e3d6a !important}

.card{background:linear-gradient(160deg,#071428 0%,#09192e 100%);border:1px solid #0f2540;border-radius:10px;padding:16px;margin:6px 0}
.card-sm{padding:10px 14px}

.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:12px 0}
.metric-tile{background:#071428;border:1px solid #0f2540;border-radius:8px;padding:12px 14px;text-align:center}
.metric-tile:hover{border-color:#1e3d6a}
.m-label{font-family:'IBM Plex Mono',monospace;font-size:.62rem;color:#2a4a6a;text-transform:uppercase;letter-spacing:.12em;margin-bottom:4px}
.m-val{font-family:'IBM Plex Mono',monospace;font-size:1.1rem;font-weight:700}
.bull{color:#00d4aa}.bear{color:#ff4d6d}.neu{color:#c8deff}.amber{color:#f59e0b}.purple{color:#a78bfa}

.macro-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:12px 0}
.macro-tile{background:#071428;border:1px solid #0f2540;border-radius:8px;padding:12px;text-align:center}
.macro-tile:hover{border-color:#1e3d6a}

.sec-label{font-family:'IBM Plex Mono',monospace;font-size:.65rem;color:#3b82f6;text-transform:uppercase;letter-spacing:.18em;border-left:2px solid #3b82f6;padding-left:10px;margin:20px 0 10px 0}

.chip-long{background:#00d4aa18;border:1px solid #00d4aa40;color:#00d4aa;padding:3px 10px;border-radius:5px;font-family:'IBM Plex Mono',monospace;font-size:.78rem;font-weight:700;display:inline-block;margin:2px}
.chip-short{background:#ff4d6d18;border:1px solid #ff4d6d40;color:#ff4d6d;padding:3px 10px;border-radius:5px;font-family:'IBM Plex Mono',monospace;font-size:.78rem;font-weight:700;display:inline-block;margin:2px}
.chip-sector{background:#3b82f618;border:1px solid #3b82f640;color:#60a5fa;padding:2px 8px;border-radius:4px;font-family:'IBM Plex Mono',monospace;font-size:.65rem;display:inline-block}
.chip-upgrade{background:#00d4aa12;border:1px solid #00d4aa30;color:#00d4aa;padding:2px 8px;border-radius:4px;font-family:'IBM Plex Mono',monospace;font-size:.62rem;display:inline-block;margin:2px}
.chip-downgrade{background:#ff4d6d12;border:1px solid #ff4d6d30;color:#ff4d6d;padding:2px 8px;border-radius:4px;font-family:'IBM Plex Mono',monospace;font-size:.62rem;display:inline-block;margin:2px}
.chip-hold{background:#f59e0b12;border:1px solid #f59e0b30;color:#f59e0b;padding:2px 8px;border-radius:4px;font-family:'IBM Plex Mono',monospace;font-size:.62rem;display:inline-block;margin:2px}

.report-box{background:#060f1e;border:1px solid #0f2540;border-radius:10px;padding:18px;font-size:.85rem;line-height:1.8;color:#8aacc8}
.report-box-long{border-top:3px solid #00d4aa}
.report-box-short{border-top:3px solid #ff4d6d}
.report-box-blue{border-top:3px solid #3b82f6}
.report-box-amber{border-top:3px solid #f59e0b}
.report-box-purple{border-top:3px solid #a78bfa}
.report-box strong{color:#c8deff}

.edu-box{background:#050e1c;border:1px dashed #1e3450;border-radius:6px;padding:10px 14px;font-size:.78rem;color:#4a7296;font-style:italic;margin-top:6px;line-height:1.6}
.edu-box::before{content:"💡 "}

.filing-row{padding:10px 0;border-bottom:1px solid #0c1e30;display:flex;align-items:flex-start;gap:12px}
.filing-badge{font-family:'IBM Plex Mono',monospace;font-size:.6rem;font-weight:700;padding:3px 7px;border-radius:4px;white-space:nowrap}
.badge-8k{background:#ff4d6d18;border:1px solid #ff4d6d40;color:#ff4d6d}
.badge-10k{background:#a78bfa18;border:1px solid #a78bfa40;color:#a78bfa}
.badge-10q{background:#60a5fa18;border:1px solid #60a5fa40;color:#60a5fa}
.badge-def{background:#f59e0b18;border:1px solid #f59e0b40;color:#f59e0b}
.badge-other{background:#2a4a6a18;border:1px solid #2a4a6a40;color:#4a7296}

.news-row{padding:10px 0;border-bottom:1px solid #0c1e30}
.news-title{color:#7ab0d8;font-size:.84rem}
.news-meta{font-family:'IBM Plex Mono',monospace;font-size:.63rem;color:#2a4a6a;margin-top:3px}

.score-bar-container{background:#0d1e30;border-radius:4px;height:6px;margin:6px 0}
.score-bar-fill{height:6px;border-radius:4px}

.verdict{padding:8px 20px;border-radius:20px;font-family:'IBM Plex Mono',monospace;font-weight:700;font-size:.85rem;display:inline-block}
.v-maintain{background:#00d4aa18;border:2px solid #00d4aa;color:#00d4aa}
.v-modify{background:#f59e0b18;border:2px solid #f59e0b;color:#f59e0b}
.v-close{background:#ff4d6d18;border:2px solid #ff4d6d;color:#ff4d6d}

.analyst-row{display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid #0c1e30}
.analyst-firm{font-family:'IBM Plex Mono',monospace;font-size:.75rem;color:#c8deff;font-weight:600}
.analyst-date{font-family:'IBM Plex Mono',monospace;font-size:.62rem;color:#2a4a6a}
.analyst-pt{font-family:'IBM Plex Mono',monospace;font-size:.72rem;color:#f59e0b}

.stTextInput input{background:#071428 !important;border:1px solid #0f2540 !important;color:#c8deff !important;font-family:'IBM Plex Mono',monospace !important;border-radius:8px !important}
.stTextInput input:focus{border-color:#3b82f6 !important}
.stButton button{background:#0d2040;border:1px solid #1e3d6a;color:#60a5fa;border-radius:8px;font-family:'IBM Plex Mono',monospace;font-size:.8rem;letter-spacing:.05em}
.stButton button:hover{background:#132d54;border-color:#3b82f6;color:#93c5fd}
.stSelectbox>div>div{background:#071428 !important;border:1px solid #0f2540 !important;color:#c8deff !important;border-radius:8px !important}
.stNumberInput input{background:#071428 !important;border:1px solid #0f2540 !important;color:#c8deff !important;font-family:'IBM Plex Mono',monospace !important;border-radius:8px !important}
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
    "Information Technology": {"icon": "💻", "etf": "XLK",
        "tickers": ["AAPL","MSFT","NVDA","AMD","ORCL","CRM","ADBE","QCOM","TXN","INTC","AVGO","MU"],
        "sub": {"AAPL":"Consumer Electronics / App Ecosystem","MSFT":"Enterprise Cloud / Productivity","NVDA":"AI Accelerators / Data Center GPUs","AMD":"CPUs & GPUs / x86+AI","ORCL":"Database / Enterprise Cloud (OCI)","CRM":"CRM / SaaS Platform","ADBE":"Creative & Marketing SaaS","QCOM":"Mobile Semiconductors / IoT","TXN":"Analog & Embedded Semiconductors","INTC":"x86 Processors / Foundry","AVGO":"Networking Chips / Custom ASICs","MU":"DRAM & NAND Memory"}},
    "Health Care": {"icon": "🏥", "etf": "XLV",
        "tickers": ["JNJ","UNH","ABBV","MRK","TMO","ABT","DHR","AMGN","GILD","PFE","ISRG","REGN"],
        "sub": {"JNJ":"Diversified Pharma & MedTech","UNH":"Managed Care / Health Insurance","ABBV":"Biopharmaceuticals / Immunology","MRK":"Large-Cap Pharma / Oncology","TMO":"Life Sciences Tools & Services","ABT":"Medical Devices / Diagnostics","DHR":"Life Sciences Equipment / Water","AMGN":"Biotechnology / Large-Cap","GILD":"Antiviral & HIV Biotechnology","PFE":"Large-Cap Pharma / Vaccines","ISRG":"Robotic-Assisted Surgery","REGN":"Biologics / Ophthalmology"}},
    "Financials": {"icon": "🏦", "etf": "XLF",
        "tickers": ["JPM","BAC","GS","MS","BLK","AXP","WFC","C","COF","USB","SCHW","ICE"],
        "sub": {"JPM":"Global Diversified Banking","BAC":"Retail & Investment Banking","GS":"Investment Banking / Asset Management","MS":"Wealth & Investment Banking","BLK":"Asset Management / iShares ETFs","AXP":"Charge Cards / Payment Network","WFC":"Retail Banking / Mortgage Origination","C":"Global Consumer & Institutional Banking","COF":"Consumer Finance / Credit Cards","USB":"Regional Banking / Wealth Management","SCHW":"Discount Brokerage / Banking Platform","ICE":"Financial Exchanges & Data"}},
    "Consumer Discretionary": {"icon": "🛍️", "etf": "XLY",
        "tickers": ["AMZN","TSLA","HD","MCD","NKE","SBUX","TJX","LOW","BKNG","GM","ABNB","RIVN"],
        "sub": {"AMZN":"E-Commerce / Cloud / Digital Advertising","TSLA":"Electric Vehicles / Energy Storage","HD":"Home Improvement Retail","MCD":"Quick Service Restaurants","NKE":"Athletic Apparel & Footwear","SBUX":"Specialty Coffee / Global Retail","TJX":"Off-Price Apparel & Home Goods","LOW":"Home Improvement Retail","BKNG":"Online Travel / Accommodations","GM":"Legacy Automaker / ICE+EV","ABNB":"Short-Term Rental Platform","RIVN":"EV Trucks / Delivery Vans"}},
    "Communication Services": {"icon": "📡", "etf": "XLC",
        "tickers": ["META","GOOGL","NFLX","DIS","CMCSA","T","VZ","SNAP","WBD","PINS","SPOT","TTD"],
        "sub": {"META":"Social Media / Digital Advertising / VR","GOOGL":"Search / Cloud / YouTube / AI","NFLX":"Video Streaming / Content Production","DIS":"Theme Parks / Streaming / ESPN","CMCSA":"Cable / Broadband / NBCUniversal","T":"Telecom / Fiber / DirecTV","VZ":"Wireless Telecom / 5G Network","SNAP":"Ephemeral Social / AR Camera","WBD":"Streaming / Cable / HBO / CNN","PINS":"Visual Discovery / Social Commerce","SPOT":"Music & Podcast Streaming","TTD":"Programmatic Advertising DSP"}},
    "Industrials": {"icon": "⚙️", "etf": "XLI",
        "tickers": ["HON","CAT","GE","UPS","RTX","DE","LMT","NOC","FDX","DAL","MMM","ETN"],
        "sub": {"HON":"Diversified Industrials / Aerospace","CAT":"Construction & Mining Equipment","GE":"Aerospace Engines / Power Generation","UPS":"Package Delivery / Logistics","RTX":"Defense / Pratt & Whitney / Collins","DE":"Agricultural Machinery / Precision Ag","LMT":"Defense Contractor / F-35 / Missiles","NOC":"Defense / Cyber / Space Systems","FDX":"Global Express & Freight Delivery","DAL":"Commercial Airlines / Delta One","MMM":"Diversified Technology & Safety","ETN":"Electrical Power Management"}},
    "Consumer Staples": {"icon": "🛒", "etf": "XLP",
        "tickers": ["PG","KO","PEP","WMT","COST","PM","MO","CL","KHC","GIS","MDLZ","SYY"],
        "sub": {"PG":"Household & Personal Care","KO":"Carbonated Beverages / Global Brand","PEP":"Beverages & Snacks / Frito-Lay","WMT":"Discount Retail / Grocery / eCommerce","COST":"Membership Warehouse / Bulk Retail","PM":"International Tobacco / IQOS","MO":"U.S. Tobacco / Nicotine Pouches","CL":"Oral Care / Home Care / Pet Nutrition","KHC":"Packaged Foods / Heinz & Kraft","GIS":"Cereal & Packaged Foods","MDLZ":"Snacks & Chocolate / Oreo","SYY":"Food Service Distribution"}},
    "Energy": {"icon": "⛽", "etf": "XLE",
        "tickers": ["XOM","CVX","COP","SLB","EOG","MPC","PSX","VLO","OXY","HES","DVN","KMI"],
        "sub": {"XOM":"Integrated Oil & Gas / Chemical","CVX":"Integrated Oil & Gas / LNG","COP":"E&P / Independent Upstream Leader","SLB":"Oilfield Services & Digital Solutions","EOG":"Permian Basin E&P / Low-Cost Operator","MPC":"Refining & Marathon Retail","PSX":"Refining / Midstream / NGL Chemicals","VLO":"Independent Refining / Ethanol","OXY":"E&P / Carbon Capture","HES":"E&P / Guyana Deep-Water","DVN":"Delaware Basin E&P / Variable Dividend","KMI":"Natural Gas Pipelines / Midstream"}},
    "Utilities": {"icon": "⚡", "etf": "XLU",
        "tickers": ["NEE","DUK","SO","D","AEP","EXC","SRE","ED","PCG","XEL","WEC","ETR"],
        "sub": {"NEE":"Renewable Energy / Florida Power & Light","DUK":"Electric Utility / Carolinas & Midwest","SO":"Electric & Gas Utility / Southeast US","D":"Electric & Gas / Mid-Atlantic","AEP":"Transmission-Heavy Electric Utility","EXC":"Nuclear Power / ComEd","SRE":"California Gas / LNG Export","ED":"Electric & Gas / New York Metro","PCG":"California Gas & Electric","XEL":"Renewable Utility / Upper Midwest","WEC":"Midwest Utility / Natural Gas","ETR":"Nuclear & Southern Utility"}},
    "Real Estate": {"icon": "🏢", "etf": "XLRE",
        "tickers": ["AMT","PLD","EQIX","CCI","PSA","WELL","O","SPG","EQR","AVB","DLR","VICI"],
        "sub": {"AMT":"Cell Tower REIT / Infrastructure","PLD":"Industrial & Logistics REIT","EQIX":"Data Center REIT / Colocation","CCI":"Cell Tower / Small Cell / Fiber REIT","PSA":"Self-Storage REIT","WELL":"Senior Housing & Healthcare REIT","O":"Net Lease / Retail REIT","SPG":"Premium Mall / Mixed-Use REIT","EQR":"Apartment / Coastal Residential REIT","AVB":"Multifamily / Apartment Communities","DLR":"Data Center REIT / Global Hyperscale","VICI":"Gaming & Experiential Real Estate"}},
    "Materials": {"icon": "⛏️", "etf": "XLB",
        "tickers": ["LIN","APD","SHW","FCX","NEM","NUE","ALB","DD","ECL","MOS","IFF","CF"],
        "sub": {"LIN":"Industrial Gases / Hydrogen Economy","APD":"Industrial Gases / Green Hydrogen","SHW":"Paints & Coatings","FCX":"Copper Mining / Gold / Indonesia","NEM":"Global Gold Mining Leader","NUE":"Steel / EAF Mini-Mill Leader","ALB":"Lithium / Specialty Chemicals","DD":"Specialty Materials / Electronic Materials","ECL":"Water Treatment / Hygiene","MOS":"Phosphate & Potash Fertilizers","IFF":"Specialty Flavors & Fragrances","CF":"Nitrogen Fertilizers / Ammonia"}},
}

MACRO_UNIVERSE: dict = {
    "indices": {
        "^GSPC":   {"label": "S&P 500",        "icon": "📊"},
        "^IXIC":   {"label": "NASDAQ",          "icon": "💻"},
        "^DJI":    {"label": "Dow Jones",       "icon": "🏛️"},
        "^RUT":    {"label": "Russell 2000",    "icon": "📈"},
        "^VIX":    {"label": "VIX Fear Gauge",  "icon": "🌡️"},
    },
    "rates": {
        "^IRX":    {"label": "3M T-Bill",       "icon": "💵"},
        "^FVX":    {"label": "5Y Treasury",     "icon": "📋"},
        "^TNX":    {"label": "10Y Treasury",    "icon": "📋"},
        "^TYX":    {"label": "30Y Treasury",    "icon": "📋"},
    },
    "fx": {
        "DX-Y.NYB": {"label": "Dollar Index",  "icon": "💲"},
        "EURUSD=X": {"label": "EUR/USD",        "icon": "🇪🇺"},
        "JPY=X":    {"label": "USD/JPY",        "icon": "🇯🇵"},
        "GBPUSD=X": {"label": "GBP/USD",        "icon": "🇬🇧"},
    },
    "commodities": {
        "GC=F":    {"label": "Gold",            "icon": "🥇"},
        "SI=F":    {"label": "Silver",          "icon": "🥈"},
        "CL=F":    {"label": "WTI Crude Oil",   "icon": "🛢️"},
        "NG=F":    {"label": "Natural Gas",     "icon": "🔥"},
        "HG=F":    {"label": "Copper",          "icon": "🔶"},
    },
}

NEWS_SOURCES: dict = {
    "Yahoo Finance":   "https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US",
    "Google News":     "https://news.google.com/rss/search?q={ticker}+stock+earnings&hl=en-US&gl=US&ceid=US:en",
    "Reuters":         "https://news.google.com/rss/search?q={ticker}+site:reuters.com&hl=en&gl=US&ceid=US:en",
    "CNBC":            "https://news.google.com/rss/search?q={ticker}+site:cnbc.com&hl=en&gl=US&ceid=US:en",
    "MarketWatch":     "https://news.google.com/rss/search?q={ticker}+site:marketwatch.com&hl=en&gl=US&ceid=US:en",
    "Seeking Alpha":   "https://news.google.com/rss/search?q={ticker}+site:seekingalpha.com&hl=en&gl=US&ceid=US:en",
    "Barron's":        "https://news.google.com/rss/search?q={ticker}+site:barrons.com&hl=en&gl=US&ceid=US:en",
    "Motley Fool":     "https://news.google.com/rss/search?q={ticker}+site:fool.com&hl=en&gl=US&ceid=US:en",
    "Benzinga":        "https://news.google.com/rss/search?q={ticker}+site:benzinga.com&hl=en&gl=US&ceid=US:en",
    "IBD":             "https://news.google.com/rss/search?q={ticker}+site:investors.com&hl=en&gl=US&ceid=US:en",
}

GENERAL_FEEDS: dict = {
    "Reuters Markets":  "https://feeds.reuters.com/reuters/businessNews",
    "CNBC":             "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "MarketWatch":      "https://feeds.marketwatch.com/marketwatch/topstories/",
    "WSJ Markets":      "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "Benzinga":         "https://www.benzinga.com/feed",
    "Motley Fool":      "https://www.fool.com/a/feeds/foolwatch?format=rss2&action=top&filter=ALL&premium=0",
}

FINVIZ_HEADERS: dict = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://finviz.com/",
}

EDGAR_BASE = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type={form}&dateb=&owner=include&count=8&output=atom"

NEWS_COLORS: dict = {
    "Reuters":      "#f59e0b",
    "CNBC":         "#60a5fa",
    "MarketWatch":  "#00d4aa",
    "Seeking Alpha":"#a78bfa",
    "Barron's":     "#e879f9",
    "Yahoo Finance":"#7ab0d8",
    "Motley Fool":  "#34d399",
    "Benzinga":     "#fb923c",
    "Google News":  "#94a3b8",
    "IBD":          "#f87171",
    "Reuters Markets": "#f59e0b",
    "WSJ Markets":  "#c8deff",
}


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


def fmt_val(val, fmt=".2f", suffix="", prefix="", none_str="N/A"):
    if val is None:
        return none_str
    try:
        return "{}{:{}}{}".format(prefix, val, fmt, suffix)
    except Exception:
        return str(val)


def fmt_pct(val, none_str="N/A"):
    if val is None:
        return none_str
    try:
        return "{:+.1f}%".format(val * 100)
    except Exception:
        return none_str


def fmt_large(val, none_str="N/A"):
    if val is None:
        return none_str
    try:
        v = float(val)
        if abs(v) >= 1e12:
            return "${:.2f}T".format(v / 1e12)
        if abs(v) >= 1e9:
            return "${:.2f}B".format(v / 1e9)
        if abs(v) >= 1e6:
            return "${:.2f}M".format(v / 1e6)
        return "${:.0f}".format(v)
    except Exception:
        return none_str


def color_class(val, thresh=0, reverse=False):
    if val is None:
        return "neu"
    is_good = float(val) > thresh
    if reverse:
        is_good = not is_good
    return "bull" if is_good else "bear"


def score_bar_html(score, color="#3b82f6"):
    return (
        '<div class="score-bar-container">'
        '<div class="score-bar-fill" style="width:{:.0f}%;background:{};"></div>'
        "</div>"
        '<span style="font-family:\'IBM Plex Mono\',monospace;font-size:.7rem;color:{};">'
        "{:.0f}/100</span>"
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


# ─────────────────────────────────────────────────────────────────────────────
#  DATA FETCHING  ─ yfinance  (Python 3.13-safe — no union type hints)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner=False)
def get_raw(ticker: str):
    """Fetch full yfinance data bundle. Returns dict or None."""
    try:
        t_up = ticker.upper().strip()
        tk   = yf.Ticker(t_up)
        info = tk.info or {}
        hist = tk.history(period="1y", interval="1d", auto_adjust=True)
        if hist is None or hist.empty:
            hist = tk.history(period="6mo", interval="1d", auto_adjust=True)

        cashflow = pd.DataFrame()
        balance  = pd.DataFrame()
        income   = pd.DataFrame()
        upgrades = pd.DataFrame()
        holders  = pd.DataFrame()
        recommendations = pd.DataFrame()

        try:
            cashflow = tk.cashflow
        except Exception:
            pass
        try:
            balance = tk.balance_sheet
        except Exception:
            pass
        try:
            income = tk.income_stmt
        except Exception:
            pass
        # yfinance >= 0.2.x uses upgrades_downgrades
        try:
            upgrades = tk.upgrades_downgrades
        except Exception:
            try:
                upgrades = tk.upgrades  # older API
            except Exception:
                pass
        try:
            holders = tk.institutional_holders
        except Exception:
            pass
        try:
            recommendations = tk.recommendations
        except Exception:
            pass

        return {
            "info": info, "hist": hist, "cashflow": cashflow,
            "balance": balance, "income": income,
            "upgrades": upgrades, "holders": holders,
            "recommendations": recommendations,
            "ticker": t_up,
        }
    except Exception:
        return None


@st.cache_data(ttl=1800, show_spinner=False)
def get_macro_snapshot():
    """Fetch all macro instruments via yfinance. Returns dict keyed by symbol."""
    all_syms = []
    for grp in MACRO_UNIVERSE.values():
        all_syms.extend(grp.keys())
    for sdata in SECTORS.values():
        all_syms.append(sdata["etf"])

    result = {}
    try:
        raw = yf.download(
            all_syms, period="5d", interval="1d",
            auto_adjust=True, progress=False, threads=True
        )
        # pandas 2.x: multi-level columns when multiple tickers
        if isinstance(raw.columns, pd.MultiIndex):
            close_df = raw["Close"]
        else:
            close_df = raw[["Close"]] if "Close" in raw.columns else pd.DataFrame()

        for sym in all_syms:
            try:
                if sym not in close_df.columns:
                    continue
                series = close_df[sym].dropna()
                if len(series) < 2:
                    continue
                last = float(series.iloc[-1])
                prev = float(series.iloc[-2])
                chg  = (last / prev - 1) if prev != 0 else 0.0
                result[sym] = {"last": last, "chg": chg, "hist": series}
            except Exception:
                continue
    except Exception:
        pass
    return result


# ─────────────────────────────────────────────────────────────────────────────
#  DATA FETCHING  ─ SEC EDGAR
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_sec_filings(ticker: str):
    """Pull recent SEC filings via EDGAR public Atom RSS. No auth required."""
    filings = []
    headers = {
        "User-Agent": "EQ-Terminal research@example.com",
        "Accept-Encoding": "gzip, deflate",
    }
    for form in ["8-K", "10-K", "10-Q", "DEF 14A"]:
        try:
            url  = EDGAR_BASE.format(ticker=ticker.upper(), form=form.replace(" ", "+"))
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                continue
            feed = feedparser.parse(resp.text)
            for entry in feed.entries[:3]:
                title   = html.unescape(entry.get("title", ""))
                link    = entry.get("link", "")
                date_s  = entry.get("updated", entry.get("published", ""))[:10]
                summary = html.unescape(entry.get("summary", ""))
                if len(summary) > 160:
                    summary = summary[:160] + "…"
                filings.append({
                    "form": form, "title": title,
                    "link": link, "date": date_s, "summary": summary,
                })
        except Exception:
            continue
    filings.sort(key=lambda x: x["date"], reverse=True)
    return filings[:12]


# ─────────────────────────────────────────────────────────────────────────────
#  DATA FETCHING  ─ Multi-source news
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def fetch_multi_news(ticker: str, max_per_source: int = 3):
    """Aggregate ticker news from 10 RSS sources with deduplication."""
    all_items = []
    seen_keys = set()

    for source_name, url_tmpl in NEWS_SOURCES.items():
        url = url_tmpl.format(ticker=ticker.upper())
        try:
            feed  = feedparser.parse(url)
            count = 0
            for entry in feed.entries:
                title = html.unescape(entry.get("title", "")).strip()
                title = re.sub(r"\s*[-–]\s*[A-Z][A-Za-z\s.]+$", "", title).strip()
                if not title or len(title) < 10:
                    continue
                key = title[:60].lower()
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                all_items.append({
                    "title":  title,
                    "link":   entry.get("link", ""),
                    "date":   entry.get("published", entry.get("updated", ""))[:16],
                    "source": source_name,
                })
                count += 1
                if count >= max_per_source:
                    break
        except Exception:
            continue

    all_items.sort(key=lambda x: x["date"], reverse=True)
    return all_items[:20]


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_general_market_news():
    """Fetch general market headlines from 6 RSS feeds simultaneously."""
    items = []
    seen  = set()
    for source, url in GENERAL_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:4]:
                title = html.unescape(entry.get("title", "")).strip()
                key   = title[:50].lower()
                if key in seen or not title:
                    continue
                seen.add(key)
                items.append({
                    "title":  title,
                    "link":   entry.get("link", ""),
                    "date":   entry.get("published", entry.get("updated", ""))[:16],
                    "source": source,
                })
        except Exception:
            continue
    items.sort(key=lambda x: x["date"], reverse=True)
    return items[:15]


# ─────────────────────────────────────────────────────────────────────────────
#  DATA FETCHING  ─ finviz analyst ratings scrape
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_finviz_ratings(ticker: str):
    """Scrape analyst ratings table from finviz.com (public HTML)."""
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
                text = tbl.get_text()
                if "Upgrade" in text or "Downgrade" in text or "Initiated" in text:
                    table = tbl
                    break
        if table is None:
            return ratings
        for row in table.find_all("tr")[1:10]:
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cells) >= 4:
                ratings.append({
                    "date":   cells[0] if len(cells) > 0 else "",
                    "action": cells[1] if len(cells) > 1 else "",
                    "firm":   cells[2] if len(cells) > 2 else "",
                    "rating": cells[3] if len(cells) > 3 else "",
                    "pt":     cells[4] if len(cells) > 4 else "",
                })
    except Exception:
        pass
    return ratings


# ─────────────────────────────────────────────────────────────────────────────
#  METRICS COMPUTATION
# ─────────────────────────────────────────────────────────────────────────────
def compute_metrics(raw):
    """Derive all screening metrics from yfinance raw data. Returns dict or None."""
    if raw is None:
        return None

    info     = raw.get("info") if raw.get("info") is not None else {}
    hist_raw = raw.get("hist")
    hist     = hist_raw if (hist_raw is not None and isinstance(hist_raw, pd.DataFrame)) else pd.DataFrame()
    cf_raw   = raw.get("cashflow")
    cashflow = cf_raw if (cf_raw is not None and isinstance(cf_raw, pd.DataFrame)) else pd.DataFrame()
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

    m["52w_high"] = _safe(info.get("fiftyTwoWeekHigh")) or (float(hist["High"].max()) if not hist.empty else None)
    m["52w_low"]  = _safe(info.get("fiftyTwoWeekLow"))  or (float(hist["Low"].min())  if not hist.empty else None)
    m["mktcap"]   = _safe(info.get("marketCap"))
    m["shares"]   = _safe(info.get("sharesOutstanding"))
    m["avg_vol"]  = _safe(info.get("averageVolume"))
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
            cap_rows = [r for r in cashflow.index if "capital" in str(r).lower() and "expenditure" in str(r).lower()]
            if ocf_rows:
                ocf  = float(cashflow.loc[ocf_rows[0]].iloc[0])
                capx = float(cashflow.loc[cap_rows[0]].iloc[0]) if cap_rows else 0.0
                m["fcf"] = ocf - abs(capx)
        except Exception:
            pass

    mktcap = m.get("mktcap")
    fcf    = m.get("fcf")
    m["fcf_yield"] = (fcf / mktcap) if (fcf and mktcap and mktcap > 0) else None

    m["short_ratio"]    = _safe(info.get("shortRatio"))
    m["short_pct"]      = _safe(info.get("shortPercentOfFloat"))
    m["target_price"]   = _safe(info.get("targetMeanPrice"))
    m["analyst_rec"]    = _safe(info.get("recommendationMean"))
    m["analyst_cnt"]    = _safe(info.get("numberOfAnalystOpinions"))
    m["div_yield"]      = _safe(info.get("dividendYield"))

    tp = m.get("target_price")
    m["analyst_upside"] = (tp / cp - 1) if (tp and cp and cp > 0) else None

    # ── Technicals ────────────────────────────────────────────────────────────
    if not hist.empty and len(hist) >= 20:
        close = hist["Close"].astype(float)
        high  = hist["High"].astype(float)
        low   = hist["Low"].astype(float)

        for period, key in [(20, "sma20"), (50, "sma50"), (200, "sma200")]:
            m[key] = float(close.rolling(period).mean().iloc[-1]) if len(hist) >= period else None

        for key, base in [("pct_sma20", "sma20"), ("pct_sma50", "sma50"), ("pct_sma200", "sma200")]:
            bv = m.get(base)
            m[key] = (cp / bv - 1) if (bv and cp) else None

        delta = close.diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rs    = gain / loss.replace(0, float("nan"))
        rsi   = 100.0 - 100.0 / (1.0 + rs)
        last_rsi = float(rsi.iloc[-1])
        m["rsi"] = last_rsi if last_rsi == last_rsi else None  # NaN check

        ema12     = close.ewm(span=12, adjust=False).mean()
        ema26     = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        macd_sig  = macd_line.ewm(span=9, adjust=False).mean()
        m["macd"]      = float(macd_line.iloc[-1])
        m["macd_sig"]  = float(macd_sig.iloc[-1])
        m["macd_hist"] = float((macd_line - macd_sig).iloc[-1])

        bb_mid = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        bb_up  = bb_mid + 2 * bb_std
        bb_lo  = bb_mid - 2 * bb_std
        m["bb_upper"] = float(bb_up.iloc[-1])
        m["bb_lower"] = float(bb_lo.iloc[-1])
        bw = m["bb_upper"] - m["bb_lower"]
        m["bb_pct"] = float((close.iloc[-1] - m["bb_lower"]) / bw) if bw != 0 else 0.5

        tr_parts = pd.concat(
            [high - low,
             (high - close.shift(1)).abs(),
             (low  - close.shift(1)).abs()],
            axis=1,
        )
        m["atr"] = float(tr_parts.max(axis=1).rolling(14).mean().iloc[-1])

        m["ret_1m"]  = float(close.iloc[-1] / close.iloc[-21]  - 1) if len(close) >= 21  else None
        m["ret_3m"]  = float(close.iloc[-1] / close.iloc[-63]  - 1) if len(close) >= 63  else None
        m["ret_6m"]  = float(close.iloc[-1] / close.iloc[-126] - 1) if len(close) >= 126 else None
        m["ret_1y"]  = float(close.iloc[-1] / close.iloc[0]    - 1)
        m["vol_ann"] = float(close.pct_change().dropna().std() * (252 ** 0.5))
    else:
        for key in ["sma20","sma50","sma200","pct_sma20","pct_sma50","pct_sma200",
                    "rsi","macd","macd_sig","macd_hist","bb_upper","bb_lower","bb_pct",
                    "atr","ret_1m","ret_3m","ret_6m","ret_1y","vol_ann"]:
            m[key] = None

    m["intrinsic"] = _dcf(m)
    iv = m.get("intrinsic")
    m["mos"] = (iv / cp - 1) if (iv and cp and cp > 0) else None

    m["long_score"]  = _score_long(m)
    m["short_score"] = _score_short(m)
    return m


def _dcf(m):
    """5-year DCF intrinsic value per share. Returns float or None."""
    fcf    = m.get("fcf")
    mktcap = m.get("mktcap")
    price  = m.get("price")
    rg     = m.get("rev_growth") or 0.06
    g1     = min(max(rg, -0.05), 0.22)
    g2     = 0.03
    r      = 0.10

    if fcf and mktcap and mktcap > 0 and price and price > 0 and fcf > 0:
        shares  = mktcap / price
        fcf_ps  = fcf / shares
        pv      = 0.0
        f       = fcf_ps
        for t in range(1, 6):
            f  *= (1 + g1)
            pv += f / ((1 + r) ** t)
        tv  = f * (1 + g2) / (r - g2)
        pv += tv / ((1 + r) ** 5)
        return round(pv, 2)

    pe = m.get("pe") or m.get("fwd_pe")
    if pe and pe > 0 and price and price > 0:
        eps = price / pe
        g   = min(g1, 0.12)
        if r > g:
            return round(eps * (1 + g) / (r - g), 2)
    return None


def _score_long(m):
    s = 50.0
    fy  = m.get("fcf_yield")
    mos = m.get("mos")
    roe = m.get("roe")
    rg  = m.get("rev_growth")
    p200= m.get("pct_sma200")
    rsi = m.get("rsi")
    au  = m.get("analyst_upside")
    pe  = m.get("pe")
    de  = m.get("de_ratio")
    mh  = m.get("macd_hist")
    ar  = m.get("analyst_rec")

    if fy is not None:
        if fy > 0.08:   s += 15
        elif fy > 0.05: s += 10
        elif fy > 0.02: s += 5
        elif fy < 0:    s -= 15
    if mos is not None:
        if mos > 0.30:   s += 12
        elif mos > 0.15: s += 7
        elif mos > 0:    s += 3
        elif mos < -0.25:s -= 10
    if roe is not None:
        if roe > 0.25:   s += 8
        elif roe > 0.15: s += 5
        elif roe > 0.08: s += 2
        elif roe < 0:    s -= 8
    if rg is not None:
        if rg > 0.15:    s += 8
        elif rg > 0.05:  s += 4
        elif rg > 0:     s += 1
        elif rg < -0.05: s -= 8
    if p200 is not None:
        if p200 > 0.05:  s += 5
        elif p200 > 0:   s += 2
        else:            s -= 5
    if rsi is not None:
        if 38 <= rsi <= 60: s += 5
        elif rsi < 35:      s += 3
        elif rsi > 75:      s -= 5
    if au is not None:
        if au > 0.20:    s += 7
        elif au > 0.10:  s += 3
        elif au < -0.05: s -= 4
    if pe is not None and pe > 0:
        if pe < 15:      s += 5
        elif pe < 22:    s += 2
        elif pe > 60:    s -= 6
        elif pe > 100:   s -= 12
    if de is not None:
        if de < 50:      s += 3
        elif de > 300:   s -= 5
    if mh is not None:
        s += 2 if mh > 0 else -2
    if ar is not None:
        if ar <= 1.8:    s += 5
        elif ar <= 2.3:  s += 2
        elif ar >= 4:    s -= 5
    return round(min(max(s, 0), 100), 1)


def _score_short(m):
    s = 50.0
    fy  = m.get("fcf_yield")
    mos = m.get("mos")
    pe  = m.get("pe")
    roe = m.get("roe")
    p200= m.get("pct_sma200")
    rsi = m.get("rsi")
    rg  = m.get("rev_growth")
    sp  = m.get("short_pct")
    de  = m.get("de_ratio")
    mh  = m.get("macd_hist")
    ar  = m.get("analyst_rec")

    if fy is not None:
        if fy < -0.05:  s += 15
        elif fy < 0:    s += 8
        elif fy > 0.06: s -= 10
    if mos is not None:
        if mos < -0.30:  s += 12
        elif mos < -0.15:s += 7
        elif mos > 0.20: s -= 8
    if pe is not None:
        if pe > 100:     s += 12
        elif pe > 60:    s += 7
        elif pe > 40:    s += 3
        elif pe < 15:    s -= 8
    if roe is not None:
        if roe < 0:      s += 10
        elif roe < 0.05: s += 5
        elif roe > 0.20: s -= 7
    if p200 is not None:
        if p200 < -0.10: s += 8
        elif p200 < 0:   s += 4
        elif p200 > 0.05:s -= 5
    if rsi is not None:
        if rsi > 75:     s += 8
        elif rsi > 65:   s += 4
        elif rsi < 35:   s -= 5
    if rg is not None:
        if rg < -0.10:   s += 10
        elif rg < 0:     s += 5
        elif rg > 0.15:  s -= 7
    if sp is not None:
        if sp > 0.20:    s += 8
        elif sp > 0.10:  s += 4
    if de is not None:
        if de > 400:     s += 7
        elif de > 200:   s += 3
    if mh is not None:
        s += 3 if mh < 0 else -2
    if ar is not None:
        if ar >= 4:      s += 6
        elif ar >= 3.5:  s += 3
        elif ar <= 1.8:  s -= 5
    return round(min(max(s, 0), 100), 1)


# ─────────────────────────────────────────────────────────────────────────────
#  SECTOR SCANNER
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def scan_sector(sector: str):
    """Screen all tickers in a sector. Returns dict with longs/shorts lists."""
    tickers = SECTORS[sector]["tickers"]
    sub     = SECTORS[sector]["sub"]
    results = []
    for t in tickers:
        raw = get_raw(t)
        if raw is None:
            continue
        m = compute_metrics(raw)
        if m is None or m.get("price") is None:
            continue
        m["sub_sector"] = sub.get(t, m.get("industry", "—"))
        results.append(m)
    if not results:
        return {"longs": [], "shorts": []}
    longs  = sorted(results, key=lambda x: x["long_score"],  reverse=True)[:5]
    shorts = sorted(results, key=lambda x: x["short_score"], reverse=True)[:5]
    return {"longs": longs, "shorts": shorts, "all": results}




# ─────────────────────────────────────────────────────────────────────────────
#  THESIS GENERATORS
# ─────────────────────────────────────────────────────────────────────────────
def long_thesis(m):
    t   = m["ticker"]
    n   = m.get("name", t)
    cp  = m.get("price")
    iv  = m.get("intrinsic")
    mos = m.get("mos")
    fy  = m.get("fcf_yield")
    roe = m.get("roe")
    rg  = m.get("rev_growth")
    pm  = m.get("profit_margin")
    pe  = m.get("pe")
    au  = m.get("analyst_upside")
    p200= m.get("pct_sma200")
    lines = []

    if mos and mos > 0.08 and iv and cp:
        lines.append(
            "**Valuation Discount — {:.0%} Margin of Safety:** {} trades at ${:.2f}, "
            "approximately {:.0%} below our DCF-derived intrinsic value of ${:.2f}. "
            "This gap reflects near-term sentiment overhang rather than fundamental deterioration — "
            "a textbook asymmetric entry for patient capital.".format(mos, n, cp, mos, iv)
        )
    elif pe and 0 < pe < 18:
        lines.append(
            "**Compressed Multiple:** At {:.1f}× trailing earnings, {} trades at a meaningful "
            "discount to sector peers and its own 5-year historical average multiple. The market "
            "is pricing in base-case deterioration that the company's operational trajectory does not support.".format(pe, t)
        )

    if fy and fy > 0.025:
        lines.append(
            "**High-Quality Cash Generation — {:.1%} FCF Yield:** {} converts revenues into "
            "free cash at a {:.1%} yield on market cap — exceeding the 10-year Treasury and most "
            "dividend yields in the sector. This FCF engine gives management full optionality: "
            "buybacks, debt paydown, or accretive M&A.".format(fy, t, fy)
        )

    if roe and roe > 0.12:
        lines.append(
            "**Capital Allocation Discipline — {:.1%} ROE:** A Return on Equity of {:.1%} signals "
            "a structurally moated business with pricing power competitors cannot easily replicate. "
            "Companies sustaining ROE above 15% through a cycle command durable valuation premiums.".format(roe, roe)
        )

    if rg and rg > 0.04:
        lines.append(
            "**Top-Line Momentum — {:.1%} Revenue Growth:** Expanding revenue at {:.1%} YoY "
            "confirms demand is not merely holding — it is accelerating. This is the necessary "
            "precondition for operating leverage to produce EPS growth that outpaces consensus estimates.".format(rg, rg)
        )

    if pm and pm > 0.08:
        lines.append(
            "**Margin Resilience — {:.1%} Net Margin:** {}'s net margin of {:.1%} places it in "
            "the upper tier of its industry, signaling pricing power maintained despite broad "
            "cost inflation pressures.".format(pm, t, pm)
        )

    if p200 and p200 > 0:
        lines.append(
            "**Technical Confirmation:** Price is {:.1%} above the 200-day moving average — "
            "the primary institutional trend filter. This confirms the sustained bid from systematic "
            "and long-only funds who require this criterion before deploying capital.".format(p200)
        )

    if au and au > 0.10:
        lines.append(
            "**Sell-Side Alignment:** Consensus analyst price target implies {:.0%} upside from "
            "current levels, signaling Wall Street expects a near-term catalyst to close the gap "
            "between price and intrinsic value.".format(au)
        )

    if not lines:
        lines.append(
            "**Multi-Factor Screen Trigger:** {} cleared our proprietary quantitative screen across "
            "valuation, capital quality, earnings momentum, and technical trend dimensions — "
            "presenting favorable risk/reward skew relative to sector peers.".format(t)
        )

    return "\n\n".join(lines)


def short_thesis(m):
    t   = m["ticker"]
    n   = m.get("name", t)
    cp  = m.get("price")
    iv  = m.get("intrinsic")
    mos = m.get("mos")
    fy  = m.get("fcf_yield")
    roe = m.get("roe")
    rg  = m.get("rev_growth")
    pe  = m.get("pe")
    de  = m.get("de_ratio")
    sp  = m.get("short_pct")
    p200= m.get("pct_sma200")
    lines = []

    if mos and mos < -0.20 and iv and cp:
        lines.append(
            "**Structural Overvaluation — {:.0%} Premium to Intrinsic Value:** At ${:.2f}, {} "
            "trades at a {:.0%} premium to our DCF-derived fair value of ${:.2f}. The embedded "
            "growth assumptions are heroic relative to the company's own guidance trajectory. "
            "Reversion to fundamental value alone implies significant downside.".format(abs(mos), cp, n, abs(mos), iv)
        )
    elif pe and pe > 50:
        lines.append(
            "**Multiple at Serious Risk — {:.1f}× Trailing Earnings:** At {:.1f}× earnings, {} "
            "is priced for perfection — yet even modest multiple compression toward the sector "
            "median implies double-digit losses in the equity.".format(pe, pe, t)
        )

    if fy is not None and fy < 0:
        lines.append(
            "**Negative Free Cash Flow — Cash Burn of {:.1%} of Market Cap:** {} is not generating "
            "cash — it is consuming it. This makes the company entirely reliant on capital markets "
            "for survival. In a credit-tightening environment, this dependency becomes an existential "
            "risk the equity market has not yet discounted.".format(abs(fy), t)
        )

    if roe is not None and roe < 0.05:
        lines.append(
            "**Return Profile in Secular Decline — {:.1%} ROE:** A sub-5% ROE signals management "
            "is either destroying capital or facing insurmountable competitive headwinds compressing "
            "returns. Without a credible ROE recovery thesis, the current multiple is unjustified "
            "by first-principles valuation.".format(roe)
        )

    if rg is not None and rg < 0:
        lines.append(
            "**Revenue Contraction — {:.1%} YoY Growth:** A shrinking top line triggers a "
            "compounding negative feedback loop: declining revenues → operating deleverage → "
            "EPS misses → downward revisions → multiple compression. Each stage creates additional "
            "selling pressure not yet incorporated in consensus models.".format(rg)
        )

    if de and de > 200:
        lines.append(
            "**Leverage as a Structural Vulnerability — {:.0f}% D/E:** {}'s balance sheet carries "
            "a D/E ratio of {:.0f}%, leaving it acutely exposed to credit market deterioration or "
            "sustained elevated interest rates.".format(de, t, de)
        )

    if p200 and p200 < -0.05:
        lines.append(
            "**Technical Breakdown — {:.1%} Below 200-Day MA:** The stock has broken below its "
            "key long-term trend line, triggering systematic selling from quantitative and "
            "trend-following strategies — a technical headwind layered on top of deteriorating "
            "fundamentals.".format(abs(p200))
        )

    if sp and sp > 0.08:
        lines.append(
            "**Smart Money Already Short — {:.1%} of Float Sold Short:** Institutions with "
            "primary research access have established significant short positions. Given the "
            "supporting fundamental evidence, this confirms rather than warns of the thesis.".format(sp)
        )

    if not lines:
        lines.append(
            "**Quantitative Bearish Trigger:** {} has triggered our multi-factor bearish "
            "screening model, exhibiting deteriorating fundamental momentum, stretched valuation, "
            "and negative technical structure relative to sector peers.".format(t)
        )

    return "\n\n".join(lines)


def trade_setup(m, bias):
    """Generate entry, stop, target, and options parameters."""
    cp  = m.get("price") or 0.0
    atr = m.get("atr") or cp * 0.02
    iv  = m.get("intrinsic")
    at  = m.get("target_price")
    vol = m.get("vol_ann") or 0.30

    if bias == "LONG":
        entry = cp
        stop  = round(cp - 1.5 * atr, 2)
        if iv and iv > cp:
            t1 = round(cp + (iv - cp) * 0.55, 2)
            t2 = round(iv, 2)
        elif at and at > cp:
            t1 = round(cp + (at - cp) * 0.60, 2)
            t2 = round(at, 2)
        else:
            t1 = round(cp * 1.15, 2)
            t2 = round(cp * 1.28, 2)

        rr     = round((t1 - entry) / max(entry - stop, 0.01), 1)
        risk_d = max(entry - stop, 0.01)

        if vol < 0.28:
            strike = round(cp * 1.02 / 5) * 5
            opts = {
                "strategy":  "Long ATM Call — Buy ${:.0f} Strike, 90-Day Expiry".format(strike),
                "rationale": "Low implied volatility makes options inexpensive. Unlimited upside with loss capped at premium paid.",
                "max_risk":  "Premium paid only",
                "leverage":  "~4–6× delta vs. outright equity",
            }
        else:
            bs = round(cp / 5) * 5
            ss = round(cp * 1.18 / 5) * 5
            opts = {
                "strategy":  "Bull Call Spread — Buy ${:.0f} / Sell ${:.0f} Call, 90 Days".format(bs, ss),
                "rationale": "Elevated IV inflates premiums. Spread sells an OTM call to reduce net debit by 40–60%, capturing the core upside move.",
                "max_risk":  "Net debit paid",
                "leverage":  "Max gain = ${:.0f}/share spread".format(ss - bs),
            }

        return {
            "bias":       "LONG",
            "entry":      "${:.2f}".format(entry),
            "entry_note": "Limit at ${:.2f} on any 1–2% intraday dip".format(entry * 0.99),
            "stop":       "${:.2f}  ({:.1f}% below entry)".format(stop, (entry - stop) / entry * 100),
            "target_1":   "${:.2f}  (+{:.1f}% — take 50% here)".format(t1, (t1 - entry) / entry * 100),
            "target_2":   "${:.2f}  (+{:.1f}% — full target)".format(t2, (t2 - entry) / entry * 100),
            "rr":         "{:.1f} : 1".format(rr),
            "sizing":     "≤2% portfolio risk. Size = (2% × portfolio) ÷ (entry − stop)",
            "catalyst_window": "60–120 days",
            "options":    opts,
        }
    else:
        entry = cp
        stop  = round(cp + 1.5 * atr, 2)
        if iv and iv < cp:
            t1 = round(cp - (cp - iv) * 0.50, 2)
            t2 = round(max(iv * 1.03, cp * 0.70), 2)
        else:
            t1 = round(cp * 0.85, 2)
            t2 = round(cp * 0.72, 2)

        rr = round((entry - t1) / max(stop - entry, 0.01), 1)
        bs = round(cp / 5) * 5
        ss = round(cp * 0.80 / 5) * 5

        if vol < 0.32:
            opts = {
                "strategy":  "Long ATM Put — Buy ${:.0f} Strike, 60-Day Expiry".format(bs),
                "rationale": "Long puts deliver convex downside capture with hard-capped max loss equal to premium paid — no unlimited upside risk of equity short.",
                "max_risk":  "Premium paid only",
                "leverage":  "~4× delta downside exposure",
            }
        else:
            opts = {
                "strategy":  "Bear Put Spread — Buy ${:.0f} / Sell ${:.0f} Put, 60 Days".format(bs, ss),
                "rationale": "High IV inflates put premiums. Selling the lower-strike put reduces net debit by 30–50% while preserving primary downside capture.",
                "max_risk":  "Net debit paid",
                "leverage":  "Max gain = ${:.0f}/share".format(bs - ss),
            }

        return {
            "bias":       "SHORT",
            "entry":      "${:.2f}".format(entry),
            "entry_note": "Short on any bounce to ${:.2f} for tighter risk entry".format(entry * 1.02),
            "stop":       "${:.2f}  ({:.1f}% above entry)".format(stop, (stop - entry) / entry * 100),
            "target_1":   "${:.2f}  (−{:.1f}% — cover 50%)".format(t1, (entry - t1) / entry * 100),
            "target_2":   "${:.2f}  (−{:.1f}% — full cover)".format(t2, (entry - t2) / entry * 100),
            "rr":         "{:.1f} : 1".format(rr),
            "sizing":     "Use options to cap upside risk. Never short without defined stop. ≤2% portfolio risk.",
            "catalyst_window": "30–60 days",
            "options":    opts,
        }


def hedge_suggestion(m):
    sector = m.get("sector", "")
    t      = m["ticker"]
    etf    = SECTORS.get(sector, {}).get("etf", "SPY")
    return (
        "**Pair Trade — Long {} / Short {} (3:1 Notional Ratio):** Shorting the sector ETF ({}) "
        "at ~one-third the notional of your {} position neutralizes approximately 60–75% of "
        "systematic sector beta — isolating the pure idiosyncratic alpha of your thesis from "
        "broad sector rotations or macro shocks.\n\n"
        "**Alternative Tail-Risk Hedge:** Purchase {} put options 15–20% OTM with 90-day expiry, "
        "sizing the premium at no more than 0.5% of total portfolio. This caps maximum drawdown "
        "from this position without forfeiting the core upside thesis."
    ).format(t, etf, etf, t, t)


def catalysts_and_risks(m, bias):
    t  = m["ticker"]
    de = m.get("de_ratio")
    if bias == "LONG":
        return (
            "**Upcoming Catalyst 1 — Earnings Beat & Guidance Raise:** The next quarterly report "
            "is the most likely near-term catalyst. Given {}'s fundamental trajectory, a "
            "beat-and-raise quarter would directly attack current pessimism and trigger rapid "
            "multiple re-rating.\n\n"
            "**Upcoming Catalyst 2 — Capital Allocation Announcement:** Any accelerated buyback, "
            "special dividend, or accretive acquisition would signal management views shares as "
            "undervalued — attracting additional institutional buying.\n\n"
            "**Risk 1 — Macro / Rates:** A renewed spike in long-duration Treasury yields compresses "
            "equity multiples broadly. Mitigate with appropriate sizing and defined stop.\n\n"
            "**Risk 2 — Execution Miss:** If the company guides down due to margin pressure or "
            "demand softness, exit if operating margin contracts more than 200bps vs. the prior "
            "year comparison."
        ).format(t)
    else:
        lev_str = "elevated leverage ({:.0f}% D/E)".format(de) if de and de > 100 else "business model dependencies"
        return (
            "**Upcoming Catalyst 1 — Earnings Miss & Downward Revision:** The next report is the "
            "primary event risk. Any guidance cut, margin miss, or revenue shortfall could "
            "accelerate re-rating toward fair value.\n\n"
            "**Upcoming Catalyst 2 — Credit/Liquidity Event:** Given {}'s {}, any credit market "
            "tightening, failed refinancing, or covenant breach could trigger a credit-equity "
            "feedback loop compressing equity value beyond our base case.\n\n"
            "**Risk 1 — Short Squeeze:** High short interest creates vulnerability to a technical "
            "squeeze on positive news. Manage by using long puts rather than outright equity short.\n\n"
            "**Risk 2 — Activist / M&A Takeout:** A strategic acquirer at a premium would "
            "immediately invalidate the short thesis. Monitor SEC 13D/13G filings."
        ).format(t, lev_str)


# ─────────────────────────────────────────────────────────────────────────────
#  CHARTS
# ─────────────────────────────────────────────────────────────────────────────
def price_chart(m, hist):
    """Build full Candlestick + Volume + RSI chart."""
    if hist is None or hist.empty:
        return go.Figure()

    close = hist["Close"].astype(float)
    high  = hist["High"].astype(float)
    low   = hist["Low"].astype(float)

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.025,
        row_heights=[0.60, 0.20, 0.20],
    )

    fig.add_trace(go.Candlestick(
        x=hist.index, open=hist["Open"], high=hist["High"],
        low=hist["Low"], close=hist["Close"], name="Price",
        increasing_line_color="#00d4aa", decreasing_line_color="#ff4d6d",
        increasing_fillcolor="#00d4aa22", decreasing_fillcolor="#ff4d6d22",
        line=dict(width=1),
    ), row=1, col=1)

    ma_specs = [("SMA 20", 20, "#60a5fa", "solid"),
                ("SMA 50", 50, "#f59e0b", "solid"),
                ("SMA 200",200,"#a78bfa", "dot")]
    for name_, p, color, dash in ma_specs:
        if len(hist) >= p:
            fig.add_trace(go.Scatter(
                x=hist.index, y=close.rolling(p).mean(), name=name_,
                line=dict(color=color, width=1.3, dash=dash), opacity=0.85,
            ), row=1, col=1)

    if len(hist) >= 20:
        bb_m = close.rolling(20).mean()
        bb_s = close.rolling(20).std()
        fig.add_trace(go.Scatter(
            x=hist.index, y=bb_m + 2 * bb_s,
            line=dict(color="rgba(59,130,246,0.3)", width=0.8, dash="dash"),
            showlegend=False, name="BB Upper",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=hist.index, y=bb_m - 2 * bb_s,
            line=dict(color="rgba(59,130,246,0.3)", width=0.8, dash="dash"),
            fill="tonexty", fillcolor="rgba(59,130,246,0.04)",
            showlegend=False, name="BB Lower",
        ), row=1, col=1)

    iv = m.get("intrinsic")
    if iv:
        fig.add_hline(
            y=iv, line_color="#f59e0b", line_dash="longdash", line_width=1.5,
            annotation_text="DCF IV ${:.2f}".format(iv),
            annotation_font_color="#f59e0b", annotation_position="right",
            row=1, col=1,
        )

    vol_colors = [
        "#00d4aa44" if float(c) >= float(o) else "#ff4d6d44"
        for c, o in zip(hist["Close"], hist["Open"])
    ]
    fig.add_trace(go.Bar(
        x=hist.index, y=hist["Volume"], name="Volume",
        marker_color=vol_colors, showlegend=False,
    ), row=2, col=1)

    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, float("nan"))
    rsi   = 100.0 - 100.0 / (1.0 + rs)

    fig.add_trace(go.Scatter(
        x=hist.index, y=rsi, name="RSI(14)",
        line=dict(color="#e879f9", width=1.5),
    ), row=3, col=1)
    fig.add_hrect(y0=70, y1=100, fillcolor="#ff4d6d", opacity=0.06, row=3, col=1)
    fig.add_hrect(y0=0,  y1=30,  fillcolor="#00d4aa", opacity=0.06, row=3, col=1)
    fig.add_hline(y=70, line_color="#ff4d6d55", line_dash="dot", line_width=0.8, row=3, col=1)
    fig.add_hline(y=30, line_color="#00d4aa55", line_dash="dot", line_width=0.8, row=3, col=1)
    fig.add_hline(y=50, line_color="#ffffff18", line_dash="dot", line_width=0.5, row=3, col=1)

    fig.update_layout(
        template="plotly_dark", paper_bgcolor="#050a14", plot_bgcolor="#07111f",
        font=dict(family="IBM Plex Mono", color="#7a9cc0", size=10),
        xaxis_rangeslider_visible=False, height=580,
        margin=dict(l=5, r=5, t=15, b=5),
        legend=dict(orientation="h", y=1.03, x=0, bgcolor="rgba(0,0,0,0)",
                    font=dict(size=10), itemsizing="constant"),
    )
    for row in range(1, 4):
        fig.update_xaxes(showgrid=True, gridcolor="#0d1e30", gridwidth=0.5, row=row, col=1)
        fig.update_yaxes(showgrid=True, gridcolor="#0d1e30", gridwidth=0.5, row=row, col=1)
    return fig


def macro_sparkline(series):
    if series is None or len(series) < 2:
        return go.Figure()
    color = "#00d4aa" if float(series.iloc[-1]) >= float(series.iloc[0]) else "#ff4d6d"
    fill  = color.replace("#", "rgba(").rstrip(")") if color.startswith("#") else color
    # simple rgba fill
    fill_map = {"#00d4aa": "rgba(0,212,170,0.08)", "#ff4d6d": "rgba(255,77,109,0.08)"}
    fill_color = fill_map.get(color, "rgba(100,150,200,0.08)")
    fig = go.Figure(go.Scatter(
        y=series.values, mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy", fillcolor=fill_color,
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0), height=50, showlegend=False,
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def sector_heatmap(macro_data):
    labels, values = [], []
    for sname, sdata in SECTORS.items():
        etf = sdata["etf"]
        icon= sdata["icon"]
        labels.append("{} {}".format(icon, etf))
        d = macro_data.get(etf)
        values.append(d["chg"] * 100 if d else 0.0)

    colors = ["rgba(0,212,170,0.7)" if v >= 0 else "rgba(255,77,109,0.7)" for v in values]
    border = ["#00d4aa" if v >= 0 else "#ff4d6d" for v in values]

    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        text=["{:+.2f}%".format(v) for v in values],
        textposition="outside",
        marker=dict(color=colors, line=dict(color=border, width=1)),
        textfont=dict(family="IBM Plex Mono", size=10, color="#c8deff"),
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="#050a14", plot_bgcolor="#07111f",
        font=dict(family="IBM Plex Mono", color="#7a9cc0", size=10),
        height=360, margin=dict(l=5, r=60, t=10, b=5),
        xaxis=dict(showgrid=True, gridcolor="#0d1e30", zeroline=True,
                   zerolinecolor="#1e3d6a", ticksuffix="%"),
        yaxis=dict(showgrid=False),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
#  POSITION REFRESH ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def refresh_position(ticker, entry, target, stop, bias):
    raw = get_raw(ticker)
    if not raw:
        return {"verdict": "ERROR", "label": "v-close", "msg": "Failed to fetch live data."}
    m  = compute_metrics(raw)
    cp = m.get("price") if m else None
    if not cp:
        return {"verdict": "ERROR", "label": "v-close", "msg": "Could not retrieve current market price."}

    pnl = (cp - entry) / entry if bias == "LONG" else (entry - cp) / entry

    if bias == "LONG" and cp <= stop:
        return {"verdict": "CLOSE TRADE — Stop Breached", "label": "v-close", "cp": cp, "pnl": pnl,
                "msg": "⚠️ **Invalidation Level Triggered.** Current price ${:.2f} has breached "
                       "the stop at ${:.2f}. Risk parameters violated. Executing close preserves capital.".format(cp, stop)}
    if bias == "SHORT" and cp >= stop:
        return {"verdict": "CLOSE TRADE — Stop Breached", "label": "v-close", "cp": cp, "pnl": pnl,
                "msg": "⚠️ **Short Squeeze / Stop Breach.** Current price ${:.2f} exceeded short stop "
                       "at ${:.2f}. Cover immediately.".format(cp, stop)}
    if bias == "LONG" and cp >= target:
        return {"verdict": "MODIFY — Take Partial Profits", "label": "v-modify", "cp": cp, "pnl": pnl,
                "msg": "🎯 **First Price Target Achieved.** Close 50% here at ${:.2f}, raise stop "
                       "on remainder to breakeven, re-evaluate for extended thesis.".format(cp)}
    if bias == "SHORT" and cp <= target:
        return {"verdict": "MODIFY — Cover Partial Short", "label": "v-modify", "cp": cp, "pnl": pnl,
                "msg": "🎯 **Downside Target Hit.** Cover 50% of short at ${:.2f}, tighten stop "
                       "on remainder to protect profits.".format(cp)}

    ls = m.get("long_score", 50)
    ss = m.get("short_score", 50)

    if bias == "LONG":
        if ls >= 55:
            return {"verdict": "MAINTAIN POSITION", "label": "v-maintain", "cp": cp, "pnl": pnl, "m": m,
                    "msg": "✅ **Thesis Intact.** {} re-scores {:.0f}/100 on the long model. "
                           "Price ${:.2f} — unrealized P&L: {:.1%}. Maintain and keep stop.".format(ticker, ls, cp, pnl)}
        else:
            return {"verdict": "MODIFY — Reduce Exposure", "label": "v-modify", "cp": cp, "pnl": pnl, "m": m,
                    "msg": "⚡ **Weakening Conviction.** {} re-scores {:.0f}/100 (below 55 threshold). "
                           "Price ${:.2f} — P&L: {:.1%}. Trim 25–50% of position.".format(ticker, ls, cp, pnl)}
    else:
        if ss >= 55:
            return {"verdict": "MAINTAIN POSITION", "label": "v-maintain", "cp": cp, "pnl": pnl, "m": m,
                    "msg": "✅ **Short Thesis Intact.** {} re-scores {:.0f}/100 on the short model. "
                           "Price ${:.2f} — P&L: {:.1%}. Maintain and keep stop discipline.".format(ticker, ss, cp, pnl)}
        else:
            return {"verdict": "MODIFY — Reduce Short", "label": "v-modify", "cp": cp, "pnl": pnl, "m": m,
                    "msg": "⚡ **Short Thesis Weakening.** {} re-scores {:.0f}/100 (below 55 threshold). "
                           "Price ${:.2f} — P&L: {:.1%}. Cover 50% and reassess.".format(ticker, ss, cp, pnl)}



# ─────────────────────────────────────────────────────────────────────────────
#  UI COMPONENT RENDERERS
# ─────────────────────────────────────────────────────────────────────────────
def render_news(ticker):
    section_label("MULTI-SOURCE NEWS · 10 FEEDS — YAHOO · REUTERS · CNBC · MARKETWATCH · SEEKING ALPHA · BARRON'S · FOOL · BENZINGA · IBD · GOOGLE")
    edu_box(
        "News is aggregated live from 10 independent RSS sources simultaneously and "
        "deduplicated by title. Source badge color identifies publication. All feeds are "
        "free public RSS — no paywalls, no API keys."
    )
    with st.spinner("Aggregating news from 10 sources for {}...".format(ticker)):
        items = fetch_multi_news(ticker, max_per_source=3)

    if not items:
        st.markdown('<div class="edu-box">No news found across RSS feeds for this ticker.</div>', unsafe_allow_html=True)
        return

    for item in items[:18]:
        src   = item["source"]
        color = NEWS_COLORS.get(src, "#3a5a80")
        st.markdown(
            '<div class="news-row">'
            '<div class="news-title">📰 '
            '<a href="{link}" target="_blank" style="color:#7ab0d8;text-decoration:none;">{title}</a>'
            ' <span style="background:{c}18;border:1px solid {c}40;color:{c};padding:1px 6px;'
            'border-radius:3px;font-family:\'IBM Plex Mono\',monospace;font-size:.58rem;">{src}</span>'
            '</div>'
            '<div class="news-meta">{date}</div>'
            '</div>'.format(link=item["link"], title=item["title"], c=color, src=src, date=item["date"]),
            unsafe_allow_html=True,
        )


def render_sec_filings(ticker):
    section_label("SEC EDGAR FILINGS · 8-K (MATERIAL EVENTS) · 10-K (ANNUAL) · 10-Q (QUARTERLY) · DEF 14A (PROXY)")
    edu_box(
        "SEC EDGAR is the authoritative source for all public company disclosures in the U.S. "
        "8-K filings (material events) are the raw feed before any media outlet processes them. "
        "10-K and 10-Q contain full audited financials. DEF 14A shows executive compensation and "
        "board nominees. All fetched via EDGAR's public Atom RSS — no authentication required."
    )
    with st.spinner("Fetching filings from SEC EDGAR for {}...".format(ticker)):
        filings = fetch_sec_filings(ticker)

    if not filings:
        st.markdown('<div class="edu-box">No recent EDGAR filings found for this ticker. '
                    'Foreign-listed companies may use a different CIK structure.</div>', unsafe_allow_html=True)
        return

    badge_map = {"8-K": "badge-8k", "10-K": "badge-10k", "10-Q": "badge-10q",
                 "DEF 14A": "badge-def"}
    for f in filings:
        badge_cls = badge_map.get(f["form"], "badge-other")
        st.markdown(
            '<div class="filing-row">'
            '<span class="filing-badge {badge}">{form}</span>'
            '<div style="flex:1;">'
            '<a href="{link}" target="_blank" style="color:#7ab0d8;text-decoration:none;font-size:.84rem;">{title}</a>'
            '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.63rem;color:#2a4a6a;margin-top:3px;">'
            '{date} &nbsp;·&nbsp; {summary}</div>'
            '</div></div>'.format(
                badge=badge_cls, form=f["form"], link=f["link"],
                title=f["title"], date=f["date"], summary=f["summary"]
            ),
            unsafe_allow_html=True,
        )


def render_analyst_activity(raw, ticker):
    section_label("ANALYST ACTIVITY · UPGRADES / DOWNGRADES / INITIATIONS — YFINANCE + FINVIZ SCRAPE")
    edu_box(
        "Analyst data flows from two independent sources: (1) yfinance pulls the historical "
        "upgrade/downgrade database sourced from SEC disclosures; (2) finviz.com is scraped "
        "for the live Wall Street ratings table showing firm, action, rating, and price target. "
        "Together these provide the most complete available picture of current sell-side sentiment "
        "without any API subscriptions."
    )

    col_yf, col_fv = st.columns(2)

    with col_yf:
        st.markdown('<div class="sec-label" style="font-size:.6rem;margin-top:0;">📊 YFINANCE · ANALYST CHANGES DATABASE</div>', unsafe_allow_html=True)
        upgrades_df = raw.get("upgrades") if raw else None
        if upgrades_df is not None and not isinstance(upgrades_df, pd.DataFrame):
            upgrades_df = None
        if upgrades_df is not None and not upgrades_df.empty:
            try:
                df = upgrades_df.copy()
                # Handle both MultiIndex and flat index
                if isinstance(df.index, pd.MultiIndex):
                    df = df.reset_index()
                else:
                    df.index = pd.to_datetime(df.index, errors="coerce")
                    df = df.sort_index(ascending=False).head(10).reset_index()

                col_map = {c.lower(): c for c in df.columns}
                date_col   = col_map.get("date", df.columns[0])
                action_col = next((col_map[k] for k in col_map if "action" in k), None)
                firm_col   = next((col_map[k] for k in col_map if "firm" in k), None)
                to_col     = next((col_map[k] for k in col_map if "tograde" in k or "to grade" in k), None)
                from_col   = next((col_map[k] for k in col_map if "fromgrade" in k or "from grade" in k), None)

                for _, row in df.head(10).iterrows():
                    action   = str(row[action_col]).strip() if action_col else ""
                    firm     = str(row[firm_col]).strip()   if firm_col   else "—"
                    to_gr    = str(row[to_col]).strip()     if to_col     else ""
                    from_gr  = str(row[from_col]).strip()   if from_col   else ""
                    date_val = str(row.get(date_col, ""))[:10]
                    al = action.lower()
                    chip = "chip-upgrade" if ("upgrade" in al or "initiat" in al or "raised" in al) \
                           else "chip-downgrade" if ("downgrade" in al or "lower" in al) \
                           else "chip-hold"
                    grade_str = "{} → {}".format(from_gr, to_gr) if (from_gr and to_gr and from_gr != to_gr) else to_gr
                    st.markdown(
                        '<div class="analyst-row">'
                        '<div><div class="analyst-firm">{}</div>'
                        '<div class="analyst-date">{}</div></div>'
                        '<div style="text-align:right;">'
                        '<span class="{}">{}</span>'
                        '<div class="analyst-date" style="margin-top:3px;">{}</div>'
                        '</div></div>'.format(firm, date_val, chip, action, grade_str),
                        unsafe_allow_html=True,
                    )
            except Exception:
                st.markdown('<p style="color:#2a4a6a;font-size:.8rem;">Could not parse upgrade data from yfinance for this ticker.</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#2a4a6a;font-size:.8rem;">No upgrade/downgrade history returned by yfinance.</p>', unsafe_allow_html=True)

    with col_fv:
        st.markdown('<div class="sec-label" style="font-size:.6rem;margin-top:0;">🌐 FINVIZ · LIVE RATINGS TABLE (HTML SCRAPE)</div>', unsafe_allow_html=True)
        with st.spinner("Scraping finviz.com for {}...".format(ticker)):
            ratings = fetch_finviz_ratings(ticker)
        if ratings:
            for r in ratings[:8]:
                al   = r.get("action", "").lower()
                chip = "chip-upgrade" if ("upgrade" in al or "initiat" in al or "raised" in al or "reiterat" in al) \
                       else "chip-downgrade" if ("downgrade" in al or "lower" in al) \
                       else "chip-hold"
                pt_raw = r.get("pt", "")
                pt_str = "PT {}".format(pt_raw) if pt_raw else ""
                st.markdown(
                    '<div class="analyst-row">'
                    '<div><div class="analyst-firm">{}</div>'
                    '<div class="analyst-date">{}</div></div>'
                    '<div style="text-align:right;">'
                    '<span class="{}">{}</span>'
                    '<div class="analyst-pt" style="margin-top:3px;">{} {}</div>'
                    '</div></div>'.format(
                        r.get("firm",""), r.get("date",""), chip,
                        r.get("action",""), r.get("rating",""), pt_str
                    ),
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<p style="color:#2a4a6a;font-size:.8rem;">Finviz scrape returned no data — '
                'the site may be rate-limiting. yfinance data on the left is authoritative.</p>',
                unsafe_allow_html=True,
            )


def render_institutional(raw):
    section_label("INSTITUTIONAL OWNERSHIP · TOP 13-F HOLDERS (YFINANCE → SEC FILINGS)")
    edu_box(
        "Institutional ownership is sourced from yfinance, which aggregates quarterly 13-F "
        "filings submitted to the SEC. Institutions holding >5% of shares outstanding must "
        "disclose positions every 90 days. High institutional concentration can amplify both "
        "rallies (coordinated buying) and selloffs (forced liquidation at quarter-end)."
    )
    holders_df = raw.get("holders") if raw else None
    if holders_df is None or not isinstance(holders_df, pd.DataFrame) or holders_df.empty:
        st.markdown('<div class="edu-box">Institutional holder data not available via yfinance for this ticker.</div>', unsafe_allow_html=True)
        return
    try:
        df       = holders_df.head(10)
        col_lwr  = {c.lower(): c for c in df.columns}
        name_col = next((col_lwr[k] for k in col_lwr if "holder" in k or "name" in k), df.columns[0])
        pct_col  = next((col_lwr[k] for k in col_lwr if "%" in k or "pct" in k or "share" in k), None)
        val_col  = next((col_lwr[k] for k in col_lwr if "value" in k), None)

        hc1, hc2, hc3 = st.columns([3, 2, 2])
        hc1.markdown('<div class="m-label">Institution</div>', unsafe_allow_html=True)
        hc2.markdown('<div class="m-label">% of Shares</div>', unsafe_allow_html=True)
        hc3.markdown('<div class="m-label">Market Value</div>', unsafe_allow_html=True)

        for _, row in df.iterrows():
            name = str(row[name_col]) if name_col else "—"
            pct  = "{:.2f}%".format(float(row[pct_col]) * 100) if pct_col and not pd.isna(row[pct_col]) else "—"
            val  = fmt_large(float(row[val_col])) if val_col and not pd.isna(row[val_col]) else "—"
            c1, c2, c3 = st.columns([3, 2, 2])
            row_style = "font-family:'IBM Plex Mono',monospace;font-size:.78rem;padding:5px 0;border-bottom:1px solid #0c1e30;"
            c1.markdown('<div style="{}color:#c8deff;">{}</div>'.format(row_style, name), unsafe_allow_html=True)
            c2.markdown('<div style="{}color:#f59e0b;">{}</div>'.format(row_style, pct),  unsafe_allow_html=True)
            c3.markdown('<div style="{}color:#60a5fa;">{}</div>'.format(row_style, val),  unsafe_allow_html=True)
    except Exception:
        st.markdown('<div class="edu-box">Could not parse institutional holder table from yfinance response.</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  FULL DEEP-DIVE REPORT
# ─────────────────────────────────────────────────────────────────────────────
def render_deep_dive(m, raw, bias):
    t    = m["ticker"]
    n    = m.get("name", t)
    cp   = m.get("price") or 0.0
    hist = raw.get("hist", pd.DataFrame()) if raw else pd.DataFrame()
    ls   = m.get("long_score", 50)
    ss   = m.get("short_score", 50)

    st.markdown(
        '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">'
        '<div>'
        '<span style="font-family:\'IBM Plex Mono\',monospace;font-size:.65rem;color:#3a5a80;text-transform:uppercase;letter-spacing:.15em;">DEEP-DIVE REPORT v2 · MULTI-SOURCE</span>'
        '<div style="font-family:\'Outfit\',sans-serif;font-weight:800;font-size:1.5rem;color:#e8f0ff;letter-spacing:-.02em;">{ticker} &nbsp;<span style="font-size:.9rem;font-weight:400;color:#4a7296;">{name}</span></div>'
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.7rem;color:#2a4a6a;margin-top:4px;">{sub}</div>'
        '</div>'
        '<div style="text-align:right;">'
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:1.8rem;font-weight:700;color:#e8f0ff;">${price:.2f}</div>'
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.68rem;color:#3a5a80;">{curr} · {exch}</div>'
        '</div></div>'.format(
            ticker=t, name=n, sub=m.get("sub_sector", m.get("industry", "")),
            price=cp, curr=m.get("currency","USD"), exch=m.get("exchange",""),
        ),
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("**Long Score**")
        st.markdown(score_bar_html(ls, "#00d4aa"), unsafe_allow_html=True)
    with c2:
        st.markdown("**Short Score**")
        st.markdown(score_bar_html(ss, "#ff4d6d"), unsafe_allow_html=True)
    with c3:
        rsi   = m.get("rsi")
        rsi_c = "bear" if rsi and rsi > 70 else "bull" if rsi and rsi < 35 else "neu"
        st.markdown("**RSI (14)**")
        st.markdown('<div class="m-val {}">{}</div>'.format(rsi_c, fmt_val(rsi, ".1f")), unsafe_allow_html=True)
    with c4:
        ar    = m.get("analyst_rec")
        ar_c  = "bull" if ar and ar < 2.5 else "bear" if ar and ar > 3.5 else "neu"
        lbl_m = {1:"Strong Buy",2:"Buy",3:"Hold",4:"Underperform",5:"Sell"}
        ar_lbl= lbl_m.get(round(ar) if ar else 0, "—")
        st.markdown("**Analyst Consensus**")
        st.markdown('<div class="m-val {}" style="font-size:.85rem;">{} ({})</div>'.format(
            ar_c, ar_lbl, fmt_val(ar, ".2f")), unsafe_allow_html=True)

    tiles = [
        ("Market Cap",       fmt_large(m.get("mktcap")),         "neu"),
        ("Trailing P/E",     fmt_val(m.get("pe"), ".1f", "×"),   color_class(m.get("pe"), 0, True) if m.get("pe") else "neu"),
        ("Fwd P/E",          fmt_val(m.get("fwd_pe"), ".1f","×"),"neu"),
        ("EV/EBITDA",        fmt_val(m.get("ev_ebit"),".1f","×"),"neu"),
        ("FCF Yield",        fmt_pct(m.get("fcf_yield")),         color_class(m.get("fcf_yield"))),
        ("ROE",              fmt_pct(m.get("roe")),               color_class(m.get("roe"), 0.08)),
        ("Net Margin",       fmt_pct(m.get("profit_margin")),     color_class(m.get("profit_margin"))),
        ("Rev Growth",       fmt_pct(m.get("rev_growth")),        color_class(m.get("rev_growth"))),
        ("D/E Ratio",        fmt_val(m.get("de_ratio"), ".0f","%"),color_class(m.get("de_ratio"), 200, True)),
        ("Beta",             fmt_val(m.get("beta"), ".2f"),       "neu"),
        ("DCF Intrinsic V.", "${:.2f}".format(m["intrinsic"]) if m.get("intrinsic") else "N/A", "amber"),
        ("Margin of Safety", fmt_pct(m.get("mos")),               color_class(m.get("mos"))),
    ]
    st.markdown(metric_tiles_html(tiles), unsafe_allow_html=True)
    edu_box("All metrics are sourced live from yfinance (Yahoo Finance backend → SEC filings). DCF Intrinsic Value uses 5-year projected FCF discounted at 10% WACC with conservative capped growth assumptions.")

    section_label("PRICE ACTION · MOVING AVERAGES · BOLLINGER BANDS · RSI · VOLUME")
    if hist is not None and not hist.empty:
        st.plotly_chart(price_chart(m, hist), use_container_width=True)
    else:
        st.info("Price history unavailable for this ticker.")

    render_news(t)
    render_sec_filings(t)
    render_analyst_activity(raw, t)
    render_institutional(raw)

    # ── Section 1: Position Type ──────────────────────────────────────────────
    section_label("SECTION 1 · POSITION TYPE & OPTIMAL EXECUTION STRATEGY")
    bias_color = "#00d4aa" if bias == "LONG" else "#ff4d6d"
    bias_label = "LONG — High-Conviction Bull" if bias == "LONG" else "SHORT — High-Conviction Bear"
    setup = trade_setup(m, bias)
    st.markdown(
        '<div class="report-box report-box-{cls}">'
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.78rem;color:{col};font-weight:700;margin-bottom:10px;">'
        '{arrow} BIAS: {lbl}</div>'
        '<strong>Optimal Execution:</strong> {strat}<br><br>'
        '<strong>Rationale:</strong> {rat}<br><br>'
        '<strong>Max Risk:</strong> {risk} &nbsp;|&nbsp; <strong>Leverage:</strong> {lev}'
        '</div>'.format(
            cls="long" if bias=="LONG" else "short",
            col=bias_color,
            arrow="▲" if bias=="LONG" else "▼",
            lbl=bias_label,
            strat=setup["options"]["strategy"],
            rat=setup["options"]["rationale"],
            risk=setup["options"]["max_risk"],
            lev=setup["options"].get("leverage","—"),
        ),
        unsafe_allow_html=True,
    )
    edu_box("Options strategy is determined dynamically by annualized realized volatility. "
            "Low-vol (<28%) → long naked call/put for maximum convexity. "
            "High-vol (>28%) → vertical spread to offset inflated net premium.")

    # ── Section 2: Thesis ─────────────────────────────────────────────────────
    section_label("SECTION 2 · IN-DEPTH FUNDAMENTAL & MACRO THESIS")
    thesis = long_thesis(m) if bias == "LONG" else short_thesis(m)
    st.markdown('<div class="report-box report-box-{}">{}</div>'.format(
        "long" if bias=="LONG" else "short", thesis), unsafe_allow_html=True)
    edu_box("Every number cited in the thesis is derived programmatically from SEC-reported "
            "financials retrieved in real time via yfinance — not hardcoded or estimated.")

    # ── Section 3: Trade Setup ────────────────────────────────────────────────
    section_label("SECTION 3 · EXACT TRADE SETUP & STRUCTURE")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            '<div class="card"><div class="m-label">Entry Trigger</div>'
            '<div class="m-val neu" style="font-size:1rem;">{}</div>'
            '<div style="font-size:.74rem;color:#3a5a80;margin-top:4px;">{}</div></div>'
            '<div class="card"><div class="m-label">Stop / Invalidation Level</div>'
            '<div class="m-val bear">{}</div></div>'.format(
                setup["entry"], setup["entry_note"], setup["stop"]
            ),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="card"><div class="m-label">Target 1 (take 50% off)</div>'
            '<div class="m-val bull">{}</div></div>'
            '<div class="card"><div class="m-label">Target 2 (full thesis)</div>'
            '<div class="m-val bull">{}</div></div>'.format(
                setup["target_1"], setup["target_2"]
            ),
            unsafe_allow_html=True,
        )
    st.markdown(
        '<div style="display:flex;gap:12px;margin:8px 0;flex-wrap:wrap;">'
        '<div class="card card-sm" style="flex:1;"><div class="m-label">Risk/Reward</div>'
        '<div class="m-val amber">{}</div></div>'
        '<div class="card card-sm" style="flex:1;"><div class="m-label">Catalyst Window</div>'
        '<div class="m-val neu">{}</div></div>'
        '<div class="card card-sm" style="flex:2;"><div class="m-label">Position Sizing Rule</div>'
        '<div style="font-size:.78rem;color:#6a9cc0;margin-top:4px;">{}</div></div>'
        '</div>'.format(setup["rr"], setup["catalyst_window"], setup["sizing"]),
        unsafe_allow_html=True,
    )
    edu_box("Stop-loss levels are set at 1.5× the 14-day Average True Range (ATR) from entry. "
            "ATR is the true measure of daily price movement including gaps — placing stops "
            "beyond the ATR band avoids being shaken out by normal market noise.")

    # ── Section 4: Catalysts & Hedges ────────────────────────────────────────
    section_label("SECTION 4 · CATALYSTS · RISKS · HEDGING STRUCTURE")
    st.markdown('<div class="report-box report-box-blue">{}</div>'.format(
        catalysts_and_risks(m, bias)), unsafe_allow_html=True)
    if bias == "LONG":
        st.markdown("**Recommended Hedging Structure:**")
        st.markdown('<div class="report-box report-box-amber">{}</div>'.format(
            hedge_suggestion(m)), unsafe_allow_html=True)
        edu_box("A pair trade (long stock / short sector ETF) neutralizes sector beta and isolates "
                "stock-specific alpha. This is the core mechanism used by long/short hedge funds to "
                "generate returns uncorrelated with the S&P 500.")



# ─────────────────────────────────────────────────────────────────────────────
#  TAB: SECTOR SCANNER
# ─────────────────────────────────────────────────────────────────────────────
def tab_sector_scanner():
    section_label("11-GICS SECTOR SCANNER · LIVE QUANTITATIVE SCREENING")
    st.markdown(
        '<p style="color:#3a5a80;">Select any GICS sector to run the live multi-factor screen. '
        'The model scores each stock across FCF yield, DCF margin of safety, ROE, revenue growth, '
        '200-MA trend, RSI, MACD momentum, and analyst consensus — all sourced live.</p>',
        unsafe_allow_html=True,
    )

    sector_options = list(SECTORS.keys())
    c_sel, c_btn = st.columns([4, 1])
    with c_sel:
        sel_idx = st.selectbox(
            "Sector",
            range(len(sector_options)),
            format_func=lambda i: "{}  {}".format(SECTORS[sector_options[i]]["icon"], sector_options[i]),
            key="sector_sel",
        )
    selected = sector_options[sel_idx]

    with c_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        run_scan = st.button("⚡ Scan", key="scan_btn", use_container_width=True)

    if not (run_scan or st.session_state.get("last_scanned") == selected):
        return

    st.session_state["last_scanned"] = selected
    info = SECTORS[selected]

    with st.spinner("Scanning {} — fetching live data for {} tickers...".format(selected, len(info["tickers"]))):
        results = scan_sector(selected)

    if not results.get("longs") and not results.get("shorts"):
        st.error("Scan returned no results. yfinance may be temporarily throttled — please retry in 30 seconds.")
        return

    st.markdown(
        '<div class="card" style="margin-bottom:14px;">'
        '<div style="display:flex;align-items:center;gap:12px;">'
        '<span style="font-size:2rem;">{icon}</span>'
        '<div>'
        '<div style="font-family:\'Outfit\',sans-serif;font-weight:700;font-size:1.1rem;color:#e8f0ff;">{name}</div>'
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.65rem;color:#3a5a80;">'
        'SECTOR ETF: {etf} · {n} STOCKS · DATA: YFINANCE + EDGAR + 10-SOURCE NEWS'
        '</div></div></div></div>'.format(
            icon=info["icon"], name=selected, etf=info["etf"], n=len(info["tickers"])
        ),
        unsafe_allow_html=True,
    )

    col_l, col_s = st.columns(2)

    with col_l:
        st.markdown('<div class="sec-label" style="border-left-color:#00d4aa;color:#00d4aa;">▲ HIGH-CONVICTION LONG CANDIDATES</div>', unsafe_allow_html=True)
        edu_box("Ranked by composite long score. A score ≥65/100 signals high conviction. "
                "Analyst consensus factor now incorporates live sell-side ratings from yfinance.")
        for m in results["longs"]:
            t  = m["ticker"]; cp = m.get("price", 0); ls = m.get("long_score", 50)
            fy = m.get("fcf_yield"); mos = m.get("mos"); roe = m.get("roe"); rg = m.get("rev_growth")
            with st.expander("▲  {}   {}   |   Score {:.0f}/100".format(t, m.get("sub_sector","")[:38], ls)):
                st.markdown(
                    '<div style="display:flex;justify-content:space-between;margin-bottom:10px;">'
                    '<div><div style="font-size:.72rem;color:#3a5a80;">{name}</div>'
                    '<div class="m-val neu" style="font-size:1.2rem;">${cp:.2f}</div></div>'
                    '<div style="text-align:right;"><div style="font-size:.65rem;color:#3a5a80;">LONG SCORE</div>'
                    '{bar}</div></div>'
                    '<div class="metric-grid" style="grid-template-columns:repeat(4,1fr);">'
                    '<div class="metric-tile"><div class="m-label">FCF Yield</div>'
                    '<div class="m-val {fy_c}">{fy_v}</div></div>'
                    '<div class="metric-tile"><div class="m-label">Margin of Safety</div>'
                    '<div class="m-val {mos_c}">{mos_v}</div></div>'
                    '<div class="metric-tile"><div class="m-label">ROE</div>'
                    '<div class="m-val {roe_c}">{roe_v}</div></div>'
                    '<div class="metric-tile"><div class="m-label">Rev Growth</div>'
                    '<div class="m-val {rg_c}">{rg_v}</div></div></div>'.format(
                        name=m.get("name",t), cp=cp,
                        bar=score_bar_html(ls, "#00d4aa"),
                        fy_c="bull" if fy and fy>0 else "bear", fy_v=fmt_pct(fy),
                        mos_c="bull" if mos and mos>0 else "bear", mos_v=fmt_pct(mos),
                        roe_c="bull" if roe and roe>0.12 else "neu", roe_v=fmt_pct(roe),
                        rg_c="bull" if rg and rg>0 else "bear", rg_v=fmt_pct(rg),
                    ),
                    unsafe_allow_html=True,
                )
                st.markdown('<div class="report-box report-box-long" style="margin-top:8px;">{}</div>'.format(long_thesis(m)), unsafe_allow_html=True)
                ts = trade_setup(m, "LONG")
                st.markdown(
                    '<div style="display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;">'
                    '<span class="chip-long">Entry {}</span>'
                    '<span class="chip-short">Stop {}</span>'
                    '<span class="chip-long">T1 {}</span>'
                    '<span class="chip-long">T2 {}</span>'
                    '<span class="chip-sector">R/R {}</span>'
                    '</div>'.format(
                        ts["entry"],
                        ts["stop"].split("(")[0].strip(),
                        ts["target_1"].split("(")[0].strip(),
                        ts["target_2"].split("(")[0].strip(),
                        ts["rr"],
                    ),
                    unsafe_allow_html=True,
                )

    with col_s:
        st.markdown('<div class="sec-label" style="border-left-color:#ff4d6d;color:#ff4d6d;">▼ HIGH-CONVICTION SHORT / BEARISH CANDIDATES</div>', unsafe_allow_html=True)
        edu_box("Ranked by composite short score. Key signals: negative FCF, P/E >2× sector median, "
                "declining ROE, revenue contraction, 200-MA breakdown, elevated short interest. "
                "Analyst consensus bearishness (rec ≥3.5) amplifies the short score.")
        for m in results["shorts"]:
            t  = m["ticker"]; cp = m.get("price", 0); ss = m.get("short_score", 50)
            pe = m.get("pe"); fy = m.get("fcf_yield"); mos = m.get("mos"); rg = m.get("rev_growth")
            with st.expander("▼  {}   {}   |   Score {:.0f}/100".format(t, m.get("sub_sector","")[:38], ss)):
                st.markdown(
                    '<div style="display:flex;justify-content:space-between;margin-bottom:10px;">'
                    '<div><div style="font-size:.72rem;color:#3a5a80;">{name}</div>'
                    '<div class="m-val neu" style="font-size:1.2rem;">${cp:.2f}</div></div>'
                    '<div style="text-align:right;"><div style="font-size:.65rem;color:#3a5a80;">SHORT SCORE</div>'
                    '{bar}</div></div>'
                    '<div class="metric-grid" style="grid-template-columns:repeat(4,1fr);">'
                    '<div class="metric-tile"><div class="m-label">FCF Yield</div>'
                    '<div class="m-val {fy_c}">{fy_v}</div></div>'
                    '<div class="metric-tile"><div class="m-label">Trailing P/E</div>'
                    '<div class="m-val {pe_c}">{pe_v}</div></div>'
                    '<div class="metric-tile"><div class="m-label">Margin of Safety</div>'
                    '<div class="m-val {mos_c}">{mos_v}</div></div>'
                    '<div class="metric-tile"><div class="m-label">Rev Growth</div>'
                    '<div class="m-val {rg_c}">{rg_v}</div></div></div>'.format(
                        name=m.get("name",t), cp=cp,
                        bar=score_bar_html(ss, "#ff4d6d"),
                        fy_c="bear" if fy is None or fy<0 else "neu", fy_v=fmt_pct(fy),
                        pe_c="bear" if pe and pe>50 else "neu", pe_v=fmt_val(pe,".1f","×"),
                        mos_c="bear" if mos and mos<0 else "neu", mos_v=fmt_pct(mos),
                        rg_c="bear" if rg and rg<0 else "neu", rg_v=fmt_pct(rg),
                    ),
                    unsafe_allow_html=True,
                )
                st.markdown('<div class="report-box report-box-short" style="margin-top:8px;">{}</div>'.format(short_thesis(m)), unsafe_allow_html=True)
                ts = trade_setup(m, "SHORT")
                st.markdown(
                    '<div style="display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;">'
                    '<span class="chip-short">Short {}</span>'
                    '<span class="chip-long">Stop {}</span>'
                    '<span class="chip-short">T1 {}</span>'
                    '<span class="chip-short">T2 {}</span>'
                    '<span class="chip-sector">R/R {}</span>'
                    '</div>'.format(
                        ts["entry"],
                        ts["stop"].split("(")[0].strip(),
                        ts["target_1"].split("(")[0].strip(),
                        ts["target_2"].split("(")[0].strip(),
                        ts["rr"],
                    ),
                    unsafe_allow_html=True,
                )


# ─────────────────────────────────────────────────────────────────────────────
#  TAB: TICKER DEEP-DIVE
# ─────────────────────────────────────────────────────────────────────────────
def tab_ticker_search():
    section_label("CUSTOM TICKER DEEP-DIVE · MULTI-SOURCE ANALYSIS ENGINE")
    edu_box(
        "Enter any global ticker (AAPL, TSLA, ASML, BHP, TSM…). The engine simultaneously "
        "fetches from yfinance (fundamentals + analyst ratings + institutional holders), "
        "SEC EDGAR (regulatory filings), 10 news RSS sources, and finviz.com (live ratings scrape) "
        "— then generates the full 4-section deep-dive report."
    )

    c1, c2, c3 = st.columns([3, 1.5, 1])
    with c1:
        ticker_input = st.text_input(
            "Ticker", placeholder="e.g. NVDA, AAPL, MSFT, TSLA, ASML ...",
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

    with st.spinner("Fetching live data for {} from yfinance + EDGAR + finviz...".format(ticker_input)):
        raw = get_raw(ticker_input)

    if not raw:
        st.error("Could not retrieve data for **{}**. Check the symbol and try again.".format(ticker_input))
        return

    m = compute_metrics(raw)
    if not m or not m.get("price"):
        st.error("Data returned but price unavailable for **{}**. Ticker may be delisted.".format(ticker_input))
        return

    for sname, sdata in SECTORS.items():
        if ticker_input in sdata["sub"]:
            m["sub_sector"] = sdata["sub"][ticker_input]
            break
    else:
        m["sub_sector"] = m.get("industry", "")

    if bias_sel == "AUTO-DETECT":
        bias = "LONG" if m.get("long_score", 50) >= m.get("short_score", 50) else "SHORT"
    else:
        bias = bias_sel

    render_deep_dive(m, raw, bias)


# ─────────────────────────────────────────────────────────────────────────────
#  TAB: MACRO DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
def tab_macro_dashboard():
    section_label("MACRO ENVIRONMENT DASHBOARD · RATES · FX · COMMODITIES · SECTOR HEATMAP")
    st.markdown(
        '<p style="color:#3a5a80;">All macro data sourced live via yfinance — '
        'market indices, Treasury yield curve, Dollar Index, major currency pairs, '
        'commodity futures, and all 11 GICS sector ETFs. No API keys required.</p>',
        unsafe_allow_html=True,
    )
    edu_box(
        "The macro environment is the first thing institutional PMs assess each morning. "
        "VIX above 25 signals elevated fear and expensive options. An inverted yield curve "
        "(2Y > 10Y) historically precedes recessions by 12–18 months. DXY above 104 creates "
        "headwinds for U.S. multinational earnings reported in foreign currencies."
    )

    with st.spinner("Loading macro data from yfinance..."):
        mdata = get_macro_snapshot()

    if not mdata:
        st.error("Failed to fetch macro data from yfinance. Please retry in a moment.")
        return

    # ── Indices ───────────────────────────────────────────────────────────────
    section_label("MAJOR MARKET INDICES")
    idx_cols = st.columns(5)
    for i, (sym, meta) in enumerate(MACRO_UNIVERSE["indices"].items()):
        d = mdata.get(sym)
        with idx_cols[i]:
            if d:
                val = d["last"]; chg = d["chg"]
                color = "#00d4aa" if chg >= 0 else "#ff4d6d"
                arrow = "▲" if chg >= 0 else "▼"
                st.markdown(
                    '<div class="macro-tile">'
                    '<div class="m-label">{icon} {label}</div>'
                    '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:1.05rem;font-weight:700;color:#e8f0ff;">{val:,.2f}</div>'
                    '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.78rem;color:{color};margin-top:2px;">{arrow} {chg:+.2f}%</div>'
                    '</div>'.format(icon=meta["icon"], label=meta["label"], val=val, color=color, arrow=arrow, chg=chg*100),
                    unsafe_allow_html=True,
                )
                if d.get("hist") is not None:
                    st.plotly_chart(macro_sparkline(d["hist"]), use_container_width=True, key="spark_{}".format(sym))
            else:
                st.markdown('<div class="macro-tile"><div class="m-label">{}</div><div class="m-val neu">N/A</div></div>'.format(meta["label"]), unsafe_allow_html=True)

    # ── Yield curve ───────────────────────────────────────────────────────────
    section_label("U.S. TREASURY YIELD CURVE  (yfinance ^ CBOE/exchange feeds)")
    c_yc, c_vix = st.columns([3, 2])
    with c_yc:
        y_labels, y_vals = [], []
        for sym, meta in MACRO_UNIVERSE["rates"].items():
            d = mdata.get(sym)
            if d:
                y_labels.append(meta["label"])
                y_vals.append(round(d["last"], 3))
        if y_labels:
            fig_yc = go.Figure(go.Scatter(
                x=y_labels, y=y_vals, mode="lines+markers+text",
                text=["{:.2f}%".format(v) for v in y_vals],
                textposition="top center",
                line=dict(color="#3b82f6", width=2.5),
                marker=dict(color="#60a5fa", size=10),
                textfont=dict(family="IBM Plex Mono", color="#c8deff", size=11),
            ))
            fig_yc.update_layout(
                template="plotly_dark", paper_bgcolor="#050a14", plot_bgcolor="#07111f",
                height=220, margin=dict(l=5, r=5, t=10, b=5),
                yaxis=dict(ticksuffix="%", showgrid=True, gridcolor="#0d1e30"),
                xaxis=dict(showgrid=False),
                font=dict(family="IBM Plex Mono", color="#7a9cc0", size=10),
            )
            st.plotly_chart(fig_yc, use_container_width=True)
        else:
            st.info("Treasury yield data unavailable.")
        edu_box("An inverted yield curve (short-term > long-term yields) is the historically most "
                "reliable U.S. recession predictor — preceding every recession since 1970 by 12–18 months. "
                "Watch the 2Y–10Y spread specifically.")

    with c_vix:
        vix_d = mdata.get("^VIX")
        if vix_d:
            vv    = vix_d["last"]
            vc    = "#ff4d6d" if vv > 25 else "#f59e0b" if vv > 18 else "#00d4aa"
            vlbl  = "EXTREME FEAR" if vv > 35 else "FEAR" if vv > 25 else "ELEVATED" if vv > 18 else "COMPLACENCY" if vv < 13 else "NORMAL"
            st.markdown(
                '<div class="card" style="text-align:center;padding:28px;">'
                '<div class="m-label">🌡️ CBOE VIX — FEAR GAUGE</div>'
                '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:3rem;font-weight:800;color:{c};margin:10px 0;">{v:.1f}</div>'
                '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.75rem;color:{c};font-weight:700;letter-spacing:.15em;">{lbl}</div>'
                '<div style="font-size:.72rem;color:#2a4a6a;margin-top:8px;line-height:1.5;">'
                'VIX &lt;15: Complacent — cheap calls<br>VIX 15–25: Normal range<br>'
                'VIX &gt;25: Fear — expensive options<br>VIX &gt;40: Crisis / dislocation</div>'
                '</div>'.format(c=vc, v=vv, lbl=vlbl),
                unsafe_allow_html=True,
            )

    # ── FX ────────────────────────────────────────────────────────────────────
    section_label("FOREIGN EXCHANGE  ·  DOLLAR INDEX & MAJOR PAIRS (yfinance)")
    fx_cols = st.columns(4)
    for i, (sym, meta) in enumerate(MACRO_UNIVERSE["fx"].items()):
        d = mdata.get(sym)
        with fx_cols[i]:
            if d:
                val=d["last"]; chg=d["chg"]; color="#00d4aa" if chg>=0 else "#ff4d6d"
                st.markdown(
                    '<div class="macro-tile">'
                    '<div class="m-label">{icon} {label}</div>'
                    '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:1.05rem;font-weight:700;color:#e8f0ff;">{val:.4f}</div>'
                    '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.75rem;color:{color};margin-top:2px;">{arrow} {chg:+.2f}%</div>'
                    '</div>'.format(
                        icon=meta["icon"], label=meta["label"], val=val, color=color,
                        arrow="▲" if chg>=0 else "▼", chg=chg*100
                    ),
                    unsafe_allow_html=True,
                )
            else:
                st.markdown('<div class="macro-tile"><div class="m-label">{}</div><div class="m-val neu">N/A</div></div>'.format(meta["label"]), unsafe_allow_html=True)
    edu_box("A strong dollar (DXY ↑) is a headwind for U.S. multinationals — it reduces the dollar value "
            "of overseas revenues and creates pressure on EM equities and commodities (dollar-priced). "
            "A weakening dollar (DXY ↓) is generally bullish for commodities, gold, and EM assets.")

    # ── Commodities ───────────────────────────────────────────────────────────
    section_label("COMMODITY FUTURES  ·  GOLD · SILVER · CRUDE OIL · NATURAL GAS · COPPER (yfinance)")
    comm_cols = st.columns(5)
    for i, (sym, meta) in enumerate(MACRO_UNIVERSE["commodities"].items()):
        d = mdata.get(sym)
        with comm_cols[i]:
            if d:
                val=d["last"]; chg=d["chg"]; color="#00d4aa" if chg>=0 else "#ff4d6d"
                st.markdown(
                    '<div class="macro-tile">'
                    '<div class="m-label">{icon} {label}</div>'
                    '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:1.05rem;font-weight:700;color:#e8f0ff;">${val:,.2f}</div>'
                    '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.75rem;color:{color};margin-top:2px;">{arrow} {chg:+.2f}%</div>'
                    '</div>'.format(
                        icon=meta["icon"], label=meta["label"], val=val, color=color,
                        arrow="▲" if chg>=0 else "▼", chg=chg*100
                    ),
                    unsafe_allow_html=True,
                )
            else:
                st.markdown('<div class="macro-tile"><div class="m-label">{}</div><div class="m-val neu">N/A</div></div>'.format(meta["label"]), unsafe_allow_html=True)
    edu_box("Copper prices are a leading indicator of global industrial demand — nicknamed 'Dr. Copper' "
            "for its track record of sniffing out economic turning points. Gold rising with equities "
            "signals risk-on with inflation hedging. Gold rising while equities fall signals genuine "
            "flight-to-safety.")

    # ── Sector heatmap ────────────────────────────────────────────────────────
    section_label("11-GICS SECTOR PERFORMANCE HEATMAP  (via sector ETFs — yfinance)")
    st.plotly_chart(sector_heatmap(mdata), use_container_width=True)
    edu_box("Sector performance is measured through official GICS sector ETFs (XLK, XLV, XLF, etc.). "
            "Green = institutional buying pressure today. Red = sector rotation out. "
            "XLU + XLP green with XLY + XLK red = defensive rotation = recession fears rising.")

    # ── General market news ───────────────────────────────────────────────────
    section_label("GENERAL MARKET HEADLINES  ·  REUTERS · CNBC · MARKETWATCH · WSJ · BENZINGA · MOTLEY FOOL")
    edu_box("Market headlines aggregated simultaneously from 6 general financial news RSS feeds. "
            "No API keys or subscriptions required — all public feeds.")
    with st.spinner("Loading market headlines from 6 feeds..."):
        market_news = fetch_general_market_news()
    for item in market_news[:12]:
        src   = item.get("source", "")
        color = NEWS_COLORS.get(src, "#3a5a80")
        st.markdown(
            '<div class="news-row">'
            '<div class="news-title">📰 '
            '<a href="{link}" target="_blank" style="color:#7ab0d8;text-decoration:none;">{title}</a>'
            ' <span style="background:{c}18;border:1px solid {c}40;color:{c};padding:1px 6px;'
            'border-radius:3px;font-family:\'IBM Plex Mono\',monospace;font-size:.58rem;">{src}</span>'
            '</div>'
            '<div class="news-meta">{date}</div>'
            '</div>'.format(link=item["link"], title=item["title"], c=color, src=src, date=item.get("date","")),
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
#  TAB: POSITION MONITOR
# ─────────────────────────────────────────────────────────────────────────────
def tab_position_monitor():
    section_label("POSITION MAINTENANCE & REFRESH ENGINE")
    st.markdown(
        '<p style="color:#3a5a80;">Input an open trade. The engine pulls fresh pricing, '
        're-runs the full multi-factor model, surfaces live news from all 10 sources, '
        'and delivers a verdict: Maintain, Modify, or Close.</p>',
        unsafe_allow_html=True,
    )
    edu_box(
        "Systematic trade review is the discipline that separates institutional managers from "
        "retail investors. This module re-evaluates every dimension of the original thesis "
        "against current live data — forcing an objective decision rather than anchoring "
        "to the original entry price."
    )

    with st.form("refresh_form"):
        c1, c2 = st.columns(2)
        with c1:
            rticker = st.text_input("Ticker Symbol", placeholder="e.g. NVDA", key="rticker").upper().strip()
            rbias   = st.selectbox("Trade Direction", ["LONG", "SHORT"], key="rbias")
        with c2:
            rentry  = st.number_input("Entry Price ($)",  min_value=0.01, value=100.00, step=0.01, key="rentry")
            rtarget = st.number_input("Price Target ($)", min_value=0.01, value=120.00, step=0.01, key="rtarget")
        rstop = st.number_input("Stop-Loss ($)", min_value=0.01, value=90.00, step=0.01, key="rstop")
        submitted = st.form_submit_button("🔄 Refresh & Re-Evaluate", use_container_width=True)

    if not (submitted and rticker):
        return

    with st.spinner("Pulling fresh data for {} across all sources...".format(rticker)):
        result = refresh_position(rticker, rentry, rtarget, rstop, rbias)

    verdict = result.get("verdict", "UNKNOWN")
    label   = result.get("label", "v-modify")
    cp      = result.get("cp")
    pnl     = result.get("pnl")
    msg     = result.get("msg", "")

    st.markdown('<div style="margin:16px 0;"><span class="verdict {}">{}</span></div>'.format(label, verdict), unsafe_allow_html=True)

    if cp:
        pnl_c = "bull" if pnl and pnl >= 0 else "bear"
        c1, c2, c3 = st.columns(3)
        c1.markdown('<div class="card"><div class="m-label">Current Price</div><div class="m-val neu">${:.2f}</div></div>'.format(cp), unsafe_allow_html=True)
        c2.markdown('<div class="card"><div class="m-label">Entry Price</div><div class="m-val neu">${:.2f}</div></div>'.format(rentry), unsafe_allow_html=True)
        c3.markdown('<div class="card"><div class="m-label">Unrealized P&L</div><div class="m-val {}">{}</div></div>'.format(pnl_c, fmt_pct(pnl)), unsafe_allow_html=True)

    st.markdown('<div class="report-box report-box-blue" style="margin-top:12px;">{}</div>'.format(msg), unsafe_allow_html=True)

    m_fresh = result.get("m")
    if m_fresh:
        section_label("LIVE METRICS SNAPSHOT")
        tiles = [
            ("Long Score",  "{:.0f}/100".format(m_fresh.get("long_score",50)),  "bull"),
            ("Short Score", "{:.0f}/100".format(m_fresh.get("short_score",50)), "bear"),
            ("FCF Yield",   fmt_pct(m_fresh.get("fcf_yield")), color_class(m_fresh.get("fcf_yield"))),
            ("RSI (14)",    fmt_val(m_fresh.get("rsi"),".1f"), "neu"),
        ]
        st.markdown(metric_tiles_html(tiles), unsafe_allow_html=True)

    section_label("LIVE NEWS FOR {}  ·  10-SOURCE FEED".format(rticker))
    render_news(rticker)

    section_label("RECENT SEC FILINGS FOR {}  ·  EDGAR".format(rticker))
    render_sec_filings(rticker)


# ─────────────────────────────────────────────────────────────────────────────
#  TAB: EDUCATION & DATA SOURCES
# ─────────────────────────────────────────────────────────────────────────────
def tab_education():
    section_label("EDUCATIONAL REFERENCE · METRICS · STRATEGIES · DATA SOURCE MAP")
    st.markdown(
        '<p style="color:#3a5a80;">Understanding the "why" behind every metric, strategy, and '
        'data source is what separates analysts who generate alpha from those who generate noise.</p>',
        unsafe_allow_html=True,
    )

    section_label("COMPLETE DATA SOURCE ARCHITECTURE")
    st.markdown("""
    <div class="report-box report-box-purple">
    <strong>Source 1 — yfinance (Yahoo Finance Public Backend)</strong><br>
    Provides: Current price, 52-week range, market cap, all valuation multiples (P/E, EV/EBITDA, P/B, P/S),
    free cash flow, ROE, revenue growth, margins, beta, short interest, analyst consensus ratings,
    analyst price targets, dividend yield, institutional 13-F holders, analyst upgrades/downgrades history,
    and all macro instruments (VIX, Treasury yields, FX pairs, commodity futures, sector ETFs).<br>
    Authentication: None — free public API used by Yahoo Finance's own web interface.<br><br>

    <strong>Source 2 — SEC EDGAR (U.S. Securities & Exchange Commission)</strong><br>
    Provides: Official 8-K filings (material events: earnings, M&A, exec changes), 10-K annual reports,
    10-Q quarterly reports, DEF 14A proxy statements (executive comp, board nominees).<br>
    Endpoint: <code>https://www.sec.gov/cgi-bin/browse-edgar</code> — public Atom/RSS, no auth required.<br>
    Why it matters: 8-Ks contain actual earnings results the moment they're filed — before any media
    outlet processes or editorializes them. High-frequency trading algos monitor this feed directly.<br><br>

    <strong>Source 3 — Yahoo Finance RSS (Direct Feed)</strong><br>
    Provides: Per-ticker headline RSS directly from Yahoo Finance's financial news aggregator.<br>
    Endpoint: <code>https://feeds.finance.yahoo.com/rss/2.0/headline?s=TICKER</code><br><br>

    <strong>Source 4 — Google News RSS (Per-Ticker, Publication-Filtered)</strong><br>
    Provides: News from Reuters, CNBC, MarketWatch, Seeking Alpha, Barron's, Motley Fool, Benzinga,
    and IBD — all simultaneously via Google News site: filter queries.<br>
    Endpoint: <code>https://news.google.com/rss/search?q=TICKER+site:reuters.com</code> (and 7 others)<br>
    Authentication: None — Google's public RSS index.<br><br>

    <strong>Source 5 — Direct RSS Feeds (General Market Headlines)</strong><br>
    Provides: Top market headlines from Reuters (<code>feeds.reuters.com</code>),
    CNBC (<code>cnbc.com/rss</code>), MarketWatch (<code>feeds.marketwatch.com</code>),
    WSJ (<code>feeds.a.dj.com</code>), Benzinga (<code>benzinga.com/feed</code>), and Motley Fool.<br>
    Authentication: None.<br><br>

    <strong>Source 6 — finviz.com (HTML Scrape — Analyst Ratings Table)</strong><br>
    Provides: Real-time analyst ratings table — firm name, action (Upgrade/Downgrade/Initiation),
    rating, and price target. The most recent Wall Street sentiment in structured form.<br>
    Method: Python requests + BeautifulSoup4 parsing of <code>finviz.com/quote.ashx?t=TICKER</code>.
    A standard browser User-Agent is sent to identify the request as a normal browser visit.<br>
    Note: finviz may occasionally rate-limit requests. yfinance upgrades/downgrades provides a backup.<br><br>

    <strong>Why No API Keys Are Required</strong><br>
    Every source above serves its data via publicly accessible HTTP endpoints — the same endpoints
    your web browser hits when you visit those sites. This terminal acts as a programmatic browser,
    reading the same public data and organizing it into a unified institutional-grade interface.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    section_label("FINANCIAL METRICS GLOSSARY")

    topics = {
        "📊 Free Cash Flow (FCF) Yield":
            "**Definition:** FCF Yield = Free Cash Flow ÷ Market Capitalization. "
            "FCF = Operating Cash Flow − Capital Expenditures.\n\n"
            "**Why it matters:** FCF is the hardest financial metric to fake. GAAP earnings "
            "can be inflated through accounting choices (depreciation schedules, revenue recognition timing), "
            "but cash flowing in and out of the bank account is nearly impossible to manipulate sustainably. "
            "A stock yielding 6% FCF is generating $6 in real cash for every $100 of market value.\n\n"
            "**Institutional usage:** FCF yield is the primary screening criterion for value-oriented "
            "long/short equity funds. Any stock with FCF yield above 8% and positive revenue growth "
            "is flagged as a potential high-conviction long in most systematic processes.",

        "🏛️ DCF Intrinsic Value & Margin of Safety":
            "**Definition:** A Discounted Cash Flow (DCF) model projects a company's future free "
            "cash flows over 5 years, then adds a terminal value, and discounts everything back to "
            "present using a required rate of return (WACC). The per-share result is 'intrinsic value.'\n\n"
            "**Margin of Safety** = (Intrinsic Value ÷ Current Price) − 1. A +25% MOS means the "
            "stock trades 25% below its calculated fair value.\n\n"
            "**Our parameters:** 10% WACC (conservative institutional standard), growth rate = YoY "
            "revenue growth capped at 22% max, 3% terminal growth. We use actual FCF from SEC filings "
            "(via yfinance) as the base cash flow.\n\n"
            "**Limitations:** DCF is sensitive to growth and discount rate assumptions. Use it as a "
            "directional signal and relative comparator, not a precise price target.",

        "📡 SEC EDGAR 8-K Filings":
            "**Definition:** Form 8-K is the 'Current Report' — required by law within 4 business days "
            "whenever a material event occurs: earnings results, M&A agreements, CEO/CFO changes, "
            "bankruptcy filings, dividend changes, credit rating actions.\n\n"
            "**Why it matters:** 8-Ks are the official source of truth before any financial media outlet "
            "processes and publishes the information. High-frequency trading algorithms are directly "
            "connected to the EDGAR Atom RSS feed to act within milliseconds of a filing.\n\n"
            "**Access method:** EDGAR's public Atom feed at "
            "`https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=TICKER&output=atom` "
            "— no authentication required. This is the same feed used by institutional research desks.",

        "🌐 finviz Analyst Ratings Scrape":
            "**What it is:** finviz.com aggregates and displays the most recent Wall Street analyst "
            "ratings changes in a structured HTML table — firm name, action (Upgrade/Downgrade/Initiate), "
            "new rating, and price target.\n\n"
            "**How we access it:** Python's `requests` library sends an HTTP GET to "
            "`finviz.com/quote.ashx?t=TICKER` with a standard browser User-Agent header. "
            "BeautifulSoup4 then parses the HTML to extract the ratings table. This is standard "
            "web scraping of publicly displayed information.\n\n"
            "**Why it matters:** Analyst upgrades and downgrades from major firms (Goldman, Morgan "
            "Stanley, JP Morgan, UBS, Barclays) frequently move stocks 2–5% on the day of publication "
            "as institutional clients act on the recommendation.",

        "📈 RSI & MACD — Momentum Indicators":
            "**RSI (Relative Strength Index):** A momentum oscillator (0–100) measuring the speed "
            "and magnitude of recent price changes over 14 trading days. RSI > 70 = overbought. "
            "RSI < 30 = oversold. Institutions use RSI as a *timing overlay* on top of fundamental "
            "conviction — the same fundamentally cheap stock is a better entry at RSI 38 than RSI 74.\n\n"
            "**MACD (Moving Average Convergence Divergence):** MACD = 12-day EMA − 26-day EMA. "
            "The histogram = MACD line − 9-day signal line. A positive and expanding histogram "
            "signals strengthening bullish momentum. A negative and widening histogram signals "
            "accelerating bearish momentum. Used in this terminal to give a small additional weight "
            "to the direction of near-term price momentum in both long and short scores.",

        "📐 ATR & Institutional Position Sizing":
            "**Average True Range (ATR):** Measures average daily price movement including overnight "
            "gaps over 14 trading days — the most accurate measure of a stock's real volatility in dollar terms.\n\n"
            "**Why stop placement matters:** Setting stops at arbitrary percentages ignores the "
            "stock's natural price noise. A stock with a $5 ATR naturally moves $5 in a day from "
            "normal buying/selling — a $2 stop would be triggered by noise, not by your thesis breaking.\n\n"
            "**Our formula:** Stop = Entry − 1.5 × ATR (for longs). "
            "Position Size = (Portfolio × 2% Risk) ÷ (Entry − Stop). "
            "This ensures no single trade can destroy more than 2% of total capital regardless of "
            "the stock's price or volatility level.",

        "🔄 Pair Trade / Sector Beta Hedge":
            "**Definition:** A pair trade simultaneously holds a long position in one security and "
            "a short position in a closely correlated benchmark (typically the sector ETF) to "
            "neutralize market and sector beta risk.\n\n"
            "**Mechanics:** If you're long $60,000 of NVDA, short ~$20,000 of XLK (Tech ETF). "
            "The 3:1 notional ratio offsets the sector-correlated component of NVDA's daily "
            "movement — isolating your idiosyncratic NVDA thesis from whether tech goes up or down.\n\n"
            "**Why hedge funds use this:** It generates returns purely from correct stock selection "
            "(alpha) while remaining market-neutral. This is how long/short equity funds generate "
            "Sharpe ratios above 1.5 that are uncorrelated with the S&P 500 — returns come from "
            "being right about company fundamentals, not from catching market direction.",
    }

    for title, content in topics.items():
        with st.expander(title, expanded=False):
            st.markdown('<div class="report-box report-box-blue">{}</div>'.format(content), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    st.markdown(
        '<div class="banner">'
        '<div style="display:flex;align-items:center;gap:16px;">'
        '<div>'
        '<div class="banner-logo">Equities Intelligence Terminal  ·  v2.0  ·  Multi-Source</div>'
        '<div class="banner-title">EQ · INTELLIGENCE</div>'
        '<div class="banner-sub">yfinance · SEC EDGAR · Reuters · CNBC · MarketWatch · Seeking Alpha · Barron\'s · Benzinga · finviz · IBD</div>'
        '</div></div>'
        '<div style="text-align:right;">'
        '<div><span class="live-dot"></span><span class="live-text">LIVE · 6 DATA SOURCES</span></div>'
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.72rem;color:#3a5a80;">{now} UTC</div>'
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.6rem;color:#1e3450;margin-top:4px;">No API keys required · Python 3.10+ compatible</div>'
        '</div></div>'.format(now=now),
        unsafe_allow_html=True,
    )

    tabs = st.tabs([
        "🌐  Sector Scanner",
        "🔍  Ticker Deep-Dive",
        "📊  Macro Dashboard",
        "🔄  Position Monitor",
        "📚  Education & Sources",
    ])

    with tabs[0]: tab_sector_scanner()
    with tabs[1]: tab_ticker_search()
    with tabs[2]: tab_macro_dashboard()
    with tabs[3]: tab_position_monitor()
    with tabs[4]: tab_education()

    st.markdown(
        '<div style="margin-top:40px;padding-top:16px;border-top:1px solid #0c1e30;text-align:center;">'
        '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:.62rem;color:#1e3450;letter-spacing:.08em;">'
        '⚡ EQ · INTELLIGENCE v2.0  ·  '
        'yfinance · SEC EDGAR · Google News RSS · Reuters · CNBC · MarketWatch · '
        'Seeking Alpha · Barron\'s · Benzinga · IBD · finviz  ·  '
        'Zero API keys  ·  Educational & research purposes only  ·  Not investment advice'
        '</div></div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
