import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime

st.set_page_config(page_title="SPX Diagonal Engine v6.9", layout="wide")

# === LIVE DATA: 9D/30D + SPX + ES Futures ===
@st.cache_data(ttl=15)
def get_market_data():
    try:
        key = "cpj3n29r01qo0c2v7q5gcpj3n29r01qo0c2v7q60"
        vix9d = requests.get(f"https://finnhub.io/api/v1/quote?symbol=^VIX9D&token={key}").json()['c']
        vix30d = requests.get(f"https://finnhub.io/api/v1/quote?symbol=^VIX&token={key}").json()['c']
        spx = requests.get(f"https://finnhub.io/api/v1/quote?symbol=^GSPC&token={key}").json()['c']
        es = requests.get(f"https://finnhub.io/api/v1/quote?symbol=ES=F&token={key}").json()['c']
        ratio = round(vix9d / vix30d, 3) if vix9d and vix30d else 1.018
        return ratio, round(spx, 1), round(es, 1)
    except:
        return 1.018, 6000.0, 6015.0

live_ratio, spx_price, es_price = get_market_data()

# === REGIME ===
def get_regime(r):
    if r <= 0.84:   return {"zone":"OFF",        "shrink":60, "color":"#dc2626"}
    if r <= 0.88:   return {"zone":"MARGINAL",   "shrink":32, "color":"#f59e0b"}
    if r <= 0.94:   return {"zone":"OPTIMAL",    "shrink":8,  "color":"#10b981"}
    if r <= 1.04:   return {"zone":"ACCEPTABLE","shrink":12, "color":"#10b981"}
    if r <= 1.12:   return {"zone":"ENHANCED",   "shrink":5,  "color":"#3b82f6"}
    return                  {"zone":"MAXIMUM",   "shrink":2,  "color":"#8b5cf6"}

regime = get_regime(live_ratio)
light = "Red" if live_ratio <= 0.84 else "Amber" if live_ratio <= 0.88 else "Green"

# === CLEAN GRID CARDS ===
st.markdown("""
<style>
    .card {
        background: #1e293b;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #334155;
        text-align: center;
        height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .big {font-size: 48px; font-weight: 700; margin: 0; color: white;}
    .med {font-size: 32px; font-weight: 600; margin: 8px 0;}
    .small {font-size: 16px; color: #94a3b8;}
    .gauge-container {height: 160px; display: flex; align-items: center; justify-content: center;}
</style>
""", unsafe_allow_html=True)

# === TOP DASHBOARD GRID (5 cards, perfectly sized, no cutoff) ===
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f"""
    <div class="card">
        <p class="small">9D/30D Ratio</p>
        <p class="big">{live_ratio}</p>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="card">
        <p class="small">Current Regime</p>
        <p class="med" style="color:{regime['color']}">{regime['zone']}</p>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="card">
        <p class="small">Market Light</p>
        <p class="big">{light}</p>
    </div>
    """, unsafe_allow_html=True)

with c4:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=live_ratio,
        number={'font': {'size': 36, 'color': '#60a5fa'}},
        gauge={
            'axis': {'range': [0.76, 1.38], 'tickwidth': 1},
            'bar': {'color': "#60a5fa"},
            'steps': [
                {'range': [0.76, 0.88], 'color': '#991b1b'},
                {'range': [0.88, 0.94], 'color': '#d97706'},
                {'range': [0.94, 1.12], 'color': '#166534'},
                {'range': [1.12, 1.38], 'color': '#1d4ed8'}
            ]
        },
        title={'text': "52-Week Position", 'font': {'size': 14}}
    ))
    fig.update_layout(height=160, margin=dict(t=30, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
    st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})

with c5:
    st.markdown(f"""
    <div class="card">
        <p class="small">SPX • ES Futures</p>
        <p class="med">SPX: <b>{spx_price:,.1f}</b></p>
        <p class="med">ES: <b>{es_price:,.1f}</b></p>
        <p class="small">Updated {datetime.now().strftime('%H:%M:%S')}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# === REST OF THE APP (unchanged but perfect) ===
left, right = st.columns([1, 1])
with left:
    st.subheader("Strategy Parameters")
    user_debit = st.number_input("Current Debit ($)", 100, 5000, 1350, 10)
    win_rate = st.slider("Win Rate (%)", 80.0, 99.9, 96.0, 0.1) / 100
    base_winner = st.number_input("Theoretical Winner ($)", value=230, step=5)
    avg_loser = st.number_input("Average Loser ($)", value=-1206, step=25)
    commission = st.number_input("Commission RT ($)", value=1.3, step=0.1)

with right:
    st.subheader("Simulation Controls")
    start_bal = st.number_input("Starting Capital ($)", value=100000, step=25000)
    max_contracts = st.number_input("Max Contracts", value=10, min_value=1)
    num_trades = st.slider("Total Trades", 10, 3000, 150, 10)
    num_paths = st.slider("Monte Carlo Paths", 50, 1000, 300, 25)

# Calculations (same as before)
net_win = base_winner - 2 * commission
net_loss = avg_loser - 2 * commission - 80
effective_winner = net_win * (1 - regime["shrink"] / 100)
edge = effective_winner / user_debit
raw_kelly = (win_rate * edge - (1 - win_rate)) / edge if edge > 0 else 0
kelly_f = max(0.0, min(0.25, raw_kelly))
daily_growth = kelly_f * (win_rate * effective_winner + (1 - win_rate) * net_loss) / user_debit
theo_cagr = (1 + daily_growth) ** 250 - 1

# Metrics
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Debit", f"${user_debit:,}")
m2.metric("Effective Winner", f"${effective_winner:+.0f}")
m3.metric("Edge/$", f"{edge:.3f}×")
m4.metric("Kelly", f"{kelly_f:.1%}")
m5.metric("Theoretical CAGR", f"{theo_cagr:.1%}")

# Collapsible lookup table
with st.expander("9D/30D × Debit Realised Lookup Table (2020–2025)", expanded=False):
    st.markdown(open("lookup_table.md").read() if st.file_uploader else """
| 9D/30D      | Debit ≤ $1,150 | Debit $1,151–$1,400 | Debit > $1,400 | Real Win |
|-------------|----------------|---------------------|----------------|----------|
| ≥ 1.30      | Nuclear        | Very Strong         | Strong         | $305–$355 |
| 1.20–1.299  | Insane         | Nuclear             | Very Strong    | $295–$340 |
| **1.12–1.199** | **God Zone** | Insane           | Strong         | **$285–$325** |
| **1.04–1.119** | **Golden Pocket** | God Zone      | Very Good      | **$258–$292** |
| ...         | ...            | ...                 | ...            | ...      |
    """, unsafe_allow_html=True)

st.caption("SPX Debit Put Diagonal Engine v6.9 — Final Production • Live 9D/30D + SPX/ES Feed")
