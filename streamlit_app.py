import streamlit as st
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime
import requests
import xml.etree.ElementTree as ET
from dateutil import parser

st.set_page_config(page_title="SPX Diagonal Engine v6.9.37 — NEWS FEED", layout="wide")

# ================================
# STYLE
# ================================
st.markdown("""
<style>
    .header-card {background:#1e293b; border:1px solid #334155; border-radius:12px; padding:12px;
                  text-align:center; height:135px; display:flex; flex-direction:column; justify-content:center;}
    .big {font-size:34px; font-weight:700; margin:4px 0; color:white;}
    .small {font-size:12px; color:#94a3b8; margin:0;}
    .nuclear {background:#7f1d1d !important; animation: pulse 1.5s infinite;}
    @keyframes pulse {0% {opacity:1} 50% {opacity:0.6} 100% {opacity:1}}
</style>
""", unsafe_allow_html=True)

# ================================
# LIVE + DAILY FORWARD 9D/30D
# ================================
@st.cache_data(ttl=60)
def get_daily_forward_curve():
    try:
        vix9d = yf.Ticker("^VIX9D").info.get('regularMarketPrice', 18.4)
        vix = yf.Ticker("^VIX").info.get('regularMarketPrice', 18.1)
        spot_ratio = round(vix9d / vix, 3) if vix > 0 else 0.929
        next_future = "VXZ25"  # ← UPDATE THIS ONE LINE EVERY MONTH (Jan 2026 = VXF26)
        fut_price = yf.Ticker(next_future).info.get('regularMarketPrice', vix * 1.02)
        forward_30d = round(vix / fut_price, 3)
        days = np.arange(0, 31)
        t = days / 30
        ratios = spot_ratio + (forward_30d - spot_ratio) * (3*t**2 - 2*t**3)
        labels = ["Today"] + [f"+{d}d" for d in range(1, 31)]
        spx = yf.Ticker("^GSPC").info.get('regularMarketPrice', 6000.0)
        return spot_ratio, ratios.tolist(), labels, round(spx, 1)
    except:
        days = np.arange(0, 31)
        ratios = np.linspace(0.929, 0.935, 31)
        labels = ["Today"] + [f"+{d}d" for d in range(1, 31)]
        return 0.929, ratios.tolist(), labels, 6000.0

spot_ratio, daily_ratios, daily_labels, spx_price = get_daily_forward_curve()
now_str = datetime.now().strftime("%b %d, %H:%M ET")

# ================================
# REGIME
# ================================
def get_regime(r):
    if r >= 1.12: return {"zone":"MAXIMUM", "shrink":2, "alert":True}
    if r >= 1.04: return {"zone":"ENHANCED", "shrink":5, "alert":True}
    if r >= 0.94: return {"zone":"OPTIMAL", "shrink":8, "alert":False}
    if r >= 0.88: return {"zone":"ACCEPTABLE","shrink":12, "alert":False}
    if r >= 0.84: return {"zone":"MARGINAL", "shrink":32, "alert":False}
    return {"zone":"OFF", "shrink":60, "alert":False}

regime = get_regime(spot_ratio)

# ================================
# HEADER + DAILY FORWARD GRAPH
# ================================
c1, c2, c3, c4 = st.columns([1.3, 1.3, 1.3, 3.1])
with c1:
    st.markdown(f'<div class="header-card"><p class="small">Spot 9D/30D</p><p class="big">{spot_ratio}</p></div>', unsafe_allow_html=True)
with c2:
    alert_class = 'nuclear' if regime["alert"] else ''
    st.markdown(f'<div class="header-card {alert_class}"><p class="small">Regime</p><p class="big">{regime["zone"]}</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="header-card"><p class="small">Forward +30d</p><p class="big">{daily_ratios[-1]:.3f}</p></div>', unsafe_allow_html=True)
with c4:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_labels, y=daily_ratios,
        mode='lines+markers+text',
        line=dict(color='#60a5fa', width=7),
        marker=dict(size=14),
        text=[f"{r:.3f}" for r in daily_ratios[::4]],
        textposition="top center",
        textfont=dict(size=13, color="#e2e8f0")
    ))
    fig.add_hline(y=1.0, line_dash="dash", line_color="#e11d48", annotation_text="1.00")
    fig.update_layout(
        title="Daily Forward 9D/30D Curve — Next 30 Days",
        height=360,
        margin=dict(l=30,r=30,t=60,b=30),
        paper_bgcolor="#1e293b", plot_bgcolor="#1e293b",
        font_color="#e2e8f0",
        yaxis=dict(range=[min(daily_ratios)-0.03, max(daily_ratios)+0.03], dtick=0.01, gridcolor="#334155"),
        xaxis=dict(tickangle=45, showgrid=False)
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ================================
# ALERTS
# ================================
if regime["alert"]:
    st.error("NUCLEAR ALERT — MAX SIZE DIAGONALS RIGHT NOW")
elif max(daily_ratios[1:15]) > spot_ratio + 0.03:
    st.success("Forward rising next 2 weeks — GOD ZONE INCOMING — SCALE UP")
elif min(daily_ratios[5:]) < spot_ratio - 0.04:
    st.warning("Forward falling soon — Reduce size or skip")
else:
    st.info("Forward stable — Normal sizing")

st.markdown("---")

# ================================
# TODAY'S MARKET MOVERS NEWS FEED
# ================================
@st.cache_data(ttl=300)  # Refresh every 5 minutes
def get_market_news():
    try:
        query = "S%26P+500+OR+SPX+OR+Nasdaq+market+move+OR+up+OR+down+OR+gains+OR+drops+OR+Fed"
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        response = requests.get(url, timeout=10)
        root = ET.fromstring(response.content)
        articles = []
        for item in root.findall(".//item")[:20]:
            title = item.find("title").text or ""
            link = item.find("link").text or ""
            pub_date_str = item.find("pubDate").text or ""
            pub_date = parser.parse(pub_date_str) if pub_date_str else datetime.now()
            description = item.find("description").text or ""
            if any(kw in title.lower() for kw in ["s&p", "spx", "nasdaq", "dow", "fed", "market"]):
                articles.append({
                    "title": title,
                    "link": link,
                    "time": pub_date.strftime("%H:%M"),
                    "desc": (description[:200] + "...") if len(description) > 200 else description
                })
        articles.sort(key=lambda x: x["time"], reverse=True)
        return articles[:4]
    except:
        return []

news = get_market_news()

with st.expander("Today's Market Movers News (Top 4 Relevant)", expanded=True):
    if news:
        for article in news:
            st.markdown(f"**[{article['title']}]({article['link']})** — {article['time']}")
            st.caption(article['desc'])
            st.markdown("---")
    else:
        st.info("No relevant news found or loading... (refreshes every 5 min)")

st.markdown("---")

# ================================
# INPUTS & CALCULATIONS
# ================================
left, right = st.columns(2)
with left:
    st.subheader("Strategy Parameters")
    debit = st.number_input("Current Debit ($)", 100, 5000, 1350, 10)
    winrate_pct = st.slider("Win Rate (%)", 0, 100, 96, 1)
    winrate = winrate_pct / 100
    winner = st.number_input("Theoretical Winner ($)", value=230, step=5)
    loser = st.number_input("Average Loser ($)", value=-1206, step=25)
    comm = st.number_input("Commission RT ($)", value=1.3, step=0.1)
with right:
    st.subheader("Monte Carlo Simulation")
    start_bal = st.number_input("Starting Capital ($)", value=100000, step=25000)
    max_cont = st.number_input("Max Contracts", value=10, min_value=1)
    trades = st.slider("Total Trades", 10, 3000, 150, 10)
    paths = st.slider("Monte Carlo Paths", 50, 1000, 300, 25)

net_win = winner - 2 * comm
eff_winner = net_win * (1 - regime["shrink"]/100)
edge = eff_winner / debit if debit > 0 else 0
kelly = (winrate * edge - (1-winrate)) / edge if edge > 0 else 0
kelly_f = max(0.0, min(0.25, kelly))

m1,m2,m3,m4,m5 = st.columns(5)
m1.metric("Debit", f"${debit:,}")
m2.metric("Effective Winner", f"${eff_winner:+.0f}")
m3.metric("Edge/$", f"{edge:.3f}×")
m4.metric("Kelly", f"{kelly_f:.1%}")
m5.metric("Shrink", f"{regime['shrink']}%")

# ================================
# SACRED TABLE
# ================================
with st.expander("Sacred 9D/30D Performance Table (2020–Nov 2025) — Your Legend", expanded=True):
    st.markdown("""
**Realised | 8–9 DTE short 0.25% OTM put → 16–18 DTE –20 wide long**
| 9D/30D Ratio | Typical debit | Realised winner | Model Winner | Realised Edge/$ | Verdict |
|------------------|---------------------|------------------------|--------------|------------------|------------------------|
| ≥ 1.12 | $550 – $1,100 | $285 – $355 | $224+ | 0.30x+ | **MAXIMUM / NUCLEAR** |
| 1.04 – 1.119 | $750 – $1,150 | $258 – $292 | $220 | 0.24x–0.30x | **ENHANCED** |
| 0.94 – 1.039 | $1,050 – $1,550 | $225 – $275 | $208 | 0.19x–0.23x | **OPTIMAL** |
| 0.88 – 0.939 | $1,400 – $1,750 | $215 – $245 | $195 | 0.13x–0.16x | **ACCEPTABLE** |
| 0.84 – 0.879 | $1,650 – $2,100 | $185 – $220 | $180 | 0.10x–0.12x | **MARGINAL** |
| ≤ 0.839 | $2,000 – $2,800 | $110 – $170 | $110 | ≤ 0.07x | **OFF** |
    """, unsafe_allow_html=True)

# ================================
# MONTE CARLO
# ================================
if st.button("RUN MONTE CARLO", use_container_width=True):
    with st.spinner(f"Running {paths} paths × {trades} trades..."):
        np.random.seed(42)
        finals = []
        all_paths = []
        for _ in range(paths):
            bal = start_bal
            path = [bal]
            streak = 0
            for _ in range(trades):
                contracts = min(max_cont, max(1, int(kelly_f * bal * 0.5 / debit)))
                won = np.random.random() < (winrate if streak == 0 else winrate * 0.6)
                pnl = (eff_winner if won else loser) * contracts
                if np.random.random() < 0.01: pnl = loser * 2.5 * contracts
                streak = streak + 1 if not won and np.random.random() < 0.5 else 0
                bal = max(bal + pnl, 1000)
                path.append(bal)
            finals.append(bal)
            all_paths.append(path)
        
        finals = np.array(finals)
        mean_path = np.mean(all_paths, axis=0)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            fig = go.Figure()
            for p in all_paths[:100]:
                fig.add_trace(go.Scatter(y=p, mode='lines', line=dict(width=1, color="#475569"), showlegend=False))
            fig.add_trace(go.Scatter(y=mean_path, mode='lines', line=dict(color='#60a5fa', width=5), name='Mean Path'))
            fig.add_hline(y=start_bal, line_color="#e11d48", line_dash="dash")
            fig.update_layout(height=560, template="plotly_dark", title="Monte Carlo Equity Curves")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.metric("Median Final", f"${np.median(finals)/1e6:.2f}M")
            st.metric("95th Percentile", f"${np.percentile(finals,95)/1e6:.2f}M")
            st.metric("Ruin Rate", f"{(finals<10000).mean():.2%}")

st.caption("SPX Diagonal Engine v6.9.37 — NEWS FEED ADDED • Daily Forward • Full Table • Full MC • Dec 2025")
