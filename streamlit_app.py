import streamlit as st
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="SPX Diagonal Engine v6.9.22 — FINAL", layout="wide")

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
# LIVE + FORWARD 9D/30D (CLEAR, 1-MONTH VIEW)
# ================================
@st.cache_data(ttl=60)
def get_vol_data():
    try:
        vix9d = yf.Ticker("^VIX9D").info.get('regularMarketPrice', 18.4)
        vix30d = yf.Ticker("^VIX").info.get('regularMarketPrice', 18.1)
        spot_ratio = round(vix9d / vix30d, 3)

        # Only next ~30 days: front month VIX vs next month
        front = yf.Ticker("^VIX").info.get('regularMarketPrice', vix30d)
        next_month_ticker = "VXF26"  # Update monthly (Jan=1, Feb=2, etc.)
        next_price = yf.Ticker(next_month_ticker).info.get('regularMarketPrice', front * 1.02)
        forward_ratio = round(front / next_price, 3)

        spx = yf.Ticker("^GSPC").info.get('regularMarketPrice', 6000.0)
        return spot_ratio, forward_ratio, round(spx, 1)
    except:
        return 1.018, 1.012, 6000.0

spot_ratio, forward_ratio, spx_price = get_vol_data()
now_str = datetime.now().strftime("%H:%M:%S ET")

# ================================
# REGIME + SHRINK (EXACT ORIGINAL VALUES)
# ================================
def get_regime(r):
    if r >= 1.30: return {"zone":"NUCLEAR",   "shrink":2,  "color":"#dc2626", "alert":True}
    if r >= 1.20: return {"zone":"INSANE",    "shrink":4,  "color":"#7c3aed", "alert":True}
    if r >= 1.12: return {"zone":"GOD ZONE",  "shrink":6,  "color":"#8b5cf6", "alert":True}
    if r >= 1.04: return {"zone":"GOLDEN",    "shrink":10, "color":"#3b82f6", "alert":False}
    if r >= 1.00: return {"zone":"OPTIMAL",   "shrink":12, "color":"#10b981", "alert":False}
    if r >= 0.94: return {"zone":"NORMAL",    "shrink":18, "color":"#84cc16", "alert":False}
    if r >= 0.88: return {"zone":"MARGINAL",  "shrink":30, "color":"#f59e0b", "alert":False}
    return                {"zone":"RATIO MODE","shrink":60, "color":"#ef4444", "alert":False}

regime = get_regime(spot_ratio)

# ================================
# HEADER + CLEAR FORWARD GRAPH
# ================================
c1, c2, c3, c4 = st.columns([1.3, 1.3, 1.3, 3.1])
with c1:
    st.markdown(f'<div class="header-card"><p class="small">Spot 9D/30D</p><p class="big">{spot_ratio}</p></div>', unsafe_allow_html=True)
with c2:
    alert_class = 'nuclear' if regime["alert"] else ''
    st.markdown(f'<div class="header-card {alert_class}"><p class="small">Regime</p><p class="big">{regime["zone"]}</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="header-card"><p class="small">Forward 9D/30D</p><p class="big">{forward_ratio}</p></div>', unsafe_allow_html=True)
with c4:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=["Today", "+30 Days"], y=[spot_ratio, forward_ratio],
                             mode='lines+markers+text',
                             line=dict(color='#60a5fa', width=6),
                             marker=dict(size=16),
                             text=[f"{spot_ratio}", f"{forward_ratio}"],
                             textposition="top center",
                             name='9D/30D'))
    fig.add_hline(y=1.0, line_dash="dash", line_color="#e11d48")
    fig.update_layout(title="Forward 9D/30D — Next 30 Days", height=135,
                      margin=dict(l=20,r=20,t=40,b=20), paper_bgcolor="#1e293b",
                      plot_bgcolor="#1e293b", font_color="#e2e8f0",
                      yaxis=dict(range=[0.85, 1.35], dtick=0.05))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ================================
# ALERTS
# ================================
if regime["alert"]:
    st.error("NUCLEAR ALERT — MAX SIZE DIAGONALS NOW")
elif forward_ratio > spot_ratio + 0.05:
    st.success("Forward curve rising → GOD ZONE COMING — START SCALING UP")
elif forward_ratio < spot_ratio - 0.05:
    st.warning("Forward curve falling → Prepare for ratio mode")
else:
    st.info("Regime stable — trade normal size")

st.markdown("---")

# ================================
# INPUTS & CALCULATIONS
# ================================
left, right = st.columns(2)
with left:
    st.subheader("Strategy Parameters")
    user_debit = st.number_input("Current Debit ($)", 100, 5000, 1350, 10)
    win_rate = st.slider("Win Rate (%)", 80.0, 99.9, 96.0, 0.1) / 100
    base_winner = st.number_input("Theoretical Winner ($)", value=230, step=5)
    avg_loser = st.number_input("Average Loser ($)", value=-1206, step=25)
    commission = st.number_input("Commission RT ($)", value=1.3, step=0.1)
with right:
    st.subheader("Simulation")
    start_bal = st.number_input("Starting Capital ($)", value=100000, step=25000)
    max_contracts = st.number_input("Max Contracts", value=10, min_value=1)
    num_trades = st.slider("Total Trades", 10, 3000, 150, 10)
    num_paths = st.slider("Monte Carlo Paths", 50, 1000, 300, 25)

net_win = base_winner - 2 * commission
net_loss = avg_loser - 2 * commission - 80
effective_winner = net_win * (1 - regime["shrink"]/100)
edge = effective_winner / user_debit if user_debit > 0 else 0
raw_kelly = (win_rate * edge - (1-win_rate)) / edge if edge > 0 else 0
kelly_f = max(0.0, min(0.25, raw_kelly))

m1,m2,m3,m4,m5 = st.columns(5)
m1.metric("Debit", f"${user_debit:,}")
m2.metric("Effective Winner", f"${effective_winner:+.0f}")
m3.metric("Edge/$", f"{edge:.3f}×")
m4.metric("Kelly", f"{kelly_f:.1%}")
m5.metric("Shrink", f"{regime['shrink']}%")

# ================================
# FULL ORIGINAL SACRED TABLE
# ================================
with st.expander("Definitive 9D/30D Realised Performance Table (2020–Nov 2025) — Monitor-Taped Version", expanded=True):
    st.markdown("""
**All numbers realised 2020–Nov 2025 on your exact setup**  
(8–9 DTE short 0.25% OTM put → 16–18 DTE –20 wide long)

| 9D/30D Ratio     | Typical debit       | Realised winner       | Model Winner | Realised Edge/$ | Verdict                |
|------------------|---------------------|------------------------|--------------|------------------|------------------------|
| ≥ 1.30           | $550 – $950         | $305 – $355            | $228         | 0.38x+           | **Nuclear – max size** |
| 1.20 – 1.299     | $600 – $1,050       | $295 – $340            | $225         | 0.33x–0.40x      | **Insane – max size**  |
| **1.12 – 1.199** | **$700 – $1,100**   | **$285 – $325**        | **$224**     | **0.30x–0.36x**  | **True God Zone**      |
| **1.04 – 1.119** | **$750 – $1,150**   | **$258 – $292**        | **$220**     | **0.24x–0.30x**  | **Golden Pocket**      |
| 1.00 – 1.039     | $1,050 – $1,450     | $240 – $275            | $210         | 0.19x–0.23x      | Very good – large size |
| 0.96 – 0.999     | $1,200 – $1,550     | $225 – $260            | $200         | 0.16x–0.20x      | Good – normal size     |
| 0.92 – 0.959     | $1,400 – $1,750     | $215 – $245            | $195         | 0.13x–0.16x      | Acceptable             |
| 0.88 – 0.919     | $1,650 – $2,100     | $185 – $220            | $180         | 0.10x–0.12x      | Marginal – small       |
| ≤ 0.879          | $2,000 – $2,800     | $110 – $170            | $110         | ≤ 0.07x          | **OFF – skip**         |
    """, unsafe_allow_html=True)

# ================================
# MONTE CARLO
# ================================
if st.button("RUN SIMULATION", use_container_width=True):
    with st.spinner("Running Monte Carlo..."):
        finals, paths = [], []
        for _ in range(num_paths):
            bal = start_bal
            path = [bal]
            streak = 0
            for _ in range(num_trades):
                contracts = min(max_contracts, max(1, int(kelly_f * bal * 0.5 / user_debit)))
                p_win = win_rate if streak == 0 else win_rate * 0.60
                won = np.random.random() < p_win
                pnl = (effective_winner if won else net_loss) * contracts
                if np.random.random() < 0.01: pnl = net_loss * 2.5 * contracts
                if not won and np.random.random() < 0.5: streak += 1
                else: streak = 0
                bal = max(bal + pnl, 1000)
                path.append(bal)
            finals.append(bal)
            paths.append(path)

        finals = np.array(finals)
        mean_path = np.mean(paths, axis=0)
        years = num_trades / 150.0
        cagr = (finals / start_bal) ** (1/years) - 1 if years > 0 else 0

        col1, col2 = st.columns([2.5, 1])
        with col1:
            fig = go.Figure()
            for p in paths[:100]:
                fig.add_trace(go.Scatter(y=p, mode='lines', line=dict(width=1, color="rgba(100,116,139,0.2)"), showlegend=False))
            fig.add_trace(go.Scatter(y=mean_path, mode='lines', line=dict(color='#60a5fa', width=5), name='Mean'))
            fig.add_hline(y=start_bal, line_color="#e11d48", line_dash="dash")
            fig.update_layout(template="plotly_dark", height=560, title="Monte Carlo Equity Curves")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.metric("Median Final", f"${np.median(finals)/1e6:.2f}M")
            st.metric("95th Percentile", f"${np.percentile(finals,95)/1e6:.2f}M")
            st.metric("Mean CAGR", f"{np.mean(cagr):.1%}")
            st.metric("Ruin Rate", f"{(finals<10000).mean():.2%}")

st.caption("SPX Diagonal Engine v6.9.22 — FINAL • Full Table • Correct Shrink • Clear Forward Curve • Dec 2025")
