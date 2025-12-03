import streamlit as st
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="SPX Diagonal Engine v6.9.26 — FINAL FOREVER", layout="wide")

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
# LIVE + FORWARD 9D/30D
# ================================
@st.cache_data(ttl=60)
def get_vol_data():
    try:
        vix9d = yf.Ticker("^VIX9D").info.get('regularMarketPrice', 18.4)
        vix = yf.Ticker("^VIX").info.get('regularMarketPrice', 18.1)
        spot = round(vix9d / vix, 3)

        next_ticker = "VXF26"  # Change monthly (Jan=VXF26, Feb=VXG26, etc.)
        next_price = yf.Ticker(next_ticker).info.get('regularMarketPrice', vix * 1.015)
        forward = round(vix / next_price, 3)

        spx = yf.Ticker("^GSPC").info.get('regularMarketPrice', 6000.0)
        return spot, forward, round(spx, 1)
    except:
        return 0.929, 0.935, 6000.0

spot_ratio, forward_ratio, spx_price = get_vol_data()
now_str = datetime.now().strftime("%H:%M:%S ET")

# ================================
# REGIME + SHRINKAGE (LOCKED FOREVER)
# ================================
def get_regime(r):
    if r >= 1.12: return {"zone":"MAXIMUM",   "shrink":2,   "alert":True}   # Nuclear
    if r >= 1.04: return {"zone":"ENHANCED",  "shrink":5,   "alert":True}
    if r >= 0.94: return {"zone":"OPTIMAL",   "shrink":8,   "alert":False}
    if r >= 0.88: return {"zone":"ACCEPTABLE","shrink":12,  "alert":False}
    if r >= 0.84: return {"zone":"MARGINAL",  "shrink":32,  "alert":False}
    return                {"zone":"OFF",       "shrink":60,  "alert":False}

regime = get_regime(spot_ratio)

# ================================
# HEADER + LEGIBLE FORWARD GRAPH
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
    values = [spot_ratio, forward_ratio]
    ymin, ymax = min(values)-0.04, max(values)+0.04
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=["Today", "+30 Days"], y=values,
                             mode='lines+markers+text',
                             line=dict(color='#60a5fa', width=8),
                             marker=dict(size=20),
                             text=[str(spot_ratio), str(forward_ratio)],
                             textposition="top center",
                             textfont=dict(size=18, color="white")))
    fig.add_hline(y=1.0, line_dash="dash", line_color="#e11d48", annotation_text="1.00")
    fig.update_layout(title="Forward 9D/30D Curve — Next 30 Days", height=260,
                      margin=dict(l=20,r=20,t=50,b=20), paper_bgcolor="#1e293b", plot_bgcolor="#1e293b",
                      yaxis=dict(range=[ymin, ymax], dtick=0.01, gridcolor="#334155"),
                      xaxis=dict(showgrid=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ================================
# ALERTS
# ================================
if regime["alert"]:
    st.error("NUCLEAR ALERT — MAX SIZE DIAGONALS RIGHT NOW")
elif forward_ratio > spot_ratio + 0.05:
    st.success("Forward rising fast → GOD ZONE INCOMING — START SCALING HARD")
elif forward_ratio > spot_ratio + 0.02:
    st.success("Forward rising → Begin scaling up")
elif forward_ratio < spot_ratio - 0.04:
    st.warning("Forward falling → Prepare for ratio mode")
else:
    st.info("Regime stable — trade normal size")

st.markdown("---")

# ================================
# USER INPUTS
# ================================
left, right = st.columns(2)
with left:
    st.subheader("Strategy Parameters")
    debit = st.number_input("Current Debit ($)", 100, 5000, 1350, 10)
    winrate = st.slider("Win Rate (%)", 80.0, 99.9, 96.0, 0.1) / 100
    winner = st.number_input("Theoretical Winner ($)", value=230, step=5)
    loser = st.number_input("Average Loser ($)", value=-1206, step=25)
    comm = st.number_input("Commission RT ($)", value=1.3, step=0.1)
with right:
    st.subheader("Monte Carlo Simulation")
    start_bal = st.number_input("Starting Capital ($)", value=100000, step=25000)
    max_cont = st.number_input("Max Contracts", value=10, min_value=1)
    trades = st.slider("Total Trades", 10, 3000, 150, 10)
    paths = st.slider("Monte Carlo Paths", 50, 1000, 300, 25)

# Calculations
net_win = winner - 2 * comm
net_loss = loser - 2 * comm - 80
eff_winner = net_win * (1 - regime["shrink"]/100)
edge = eff_winner / debit if debit > 0 else 0
kelly = (winrate * edge - (1-winrate)) / edge if edge > 0 else 0
kelly_f = max(0.0, min(0.25, kelly))

m1,m2,m3,m4,m5 = st.columns(5)
m1.metric("Debit", f"${debit:,}")
m2.metric("Effective Winner", f"${eff_winner:+.0f}")
m3.metric("Edge/$", f"{edge:.3f}×")
m4.metric("Kelly", f"{kelly_f:.1%}")
m5.metric("Shrink Applied", f"{regime['shrink']}%")

# ================================
# SACRED TABLE
# ================================
with st.expander("Definitive 9D/30D Realised Performance Table (2020–Nov 2025)", expanded=True):
    st.markdown("""
**Realised 2020–Nov 2025 | 8–9 DTE short 0.25% OTM put → 16–18 DTE –20 wide long**

| 9D/30D Ratio     | Typical Debit       | Realised Winner       | Shrinkage | Verdict                |
|------------------|---------------------|------------------------|-----------|------------------------|
| ≥ 1.12           | $550 – $1,100       | $285 – $355            | 2%        | **MAXIMUM / NUCLEAR**  |
| 1.04 – 1.119     | $750 – $1,150       | $258 – $292            | 5%        | **ENHANCED**           |
| 0.94 – 1.039     | $1,050 – $1,550     | $225 – $275            | 8%        | **OPTIMAL**            |
| 0.88 – 0.939     | $1,400 – $1,750     | $215 – $245            | 12%       | **ACCEPTABLE**         |
| 0.84 – 0.879     | $1,650 – $2,100     | $185 – $220            | 32%       | **MARGINAL**           |
| ≤ 0.839          | $2,000 – $2,800     | $110 – $170            | 60%       | **OFF**                |
    """, unsafe_allow_html=True)

# ================================
# MONTE CARLO SIMULATION
# ================================
if st.button("RUN MONTE CARLO SIMULATION", use_container_width=True):
    with st.spinner(f"Running {paths:,} paths × {trades:,} trades..."):
        finals = []
        all_paths = []
        for _ in range(paths):
            bal = start_bal
            path = [bal]
            streak = 0
            for _ in range(trades):
                contracts = min(max_cont, max(1, int(kelly_f * bal * 0.5 / debit)))
                p_win = winrate if streak == 0 else winrate * 0.60
                won = np.random.random() < p_win
                pnl = (eff_winner if won else net_loss) * contracts
                if np.random.random() < 0.01: pnl = net_loss * 2.5 * contracts  # black swan
                streak = streak + 1 if not won and np.random.random() < 0.5 else 0
                bal = max(bal + pnl, 1000)
                path.append(bal)
            finals.append(bal)
            all_paths.append(path)

        finals = np.array(finals)
        mean_path = np.mean(all_paths, axis=0)
        years = trades / 150.0
        cagr = (finals / start_bal) ** (1/years) - 1 if years > 0 else 0

        col1, col2 = st.columns([2.5, 1])
        with col1:
            fig = go.Figure()
            for p in all_paths[:100]:
                fig.add_trace(go.Scatter(y=p, mode='lines', line=dict(width=1, color="rgba(100,116,139,0.2)"), showlegend=False))
            fig.add_trace(go.Scatter(y=mean_path, mode='lines', line=dict(color='#60a5fa', width=5), name='Mean Path'))
            fig.add_hline(y=start_bal, line_color="#e11d48", line_dash="dash")
            fig.update_layout(template="plotly_dark", height=560, title="Monte Carlo Equity Curves")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.metric("Median Final", f"${np.median(finals)/1e6:.2f}M")
            st.metric("95th Percentile", f"${np.percentile(finals,95)/1e6:.2f}M")
            st.metric("Mean CAGR", f"{np.mean(cagr):.1%}")
            st.metric("Ruin Rate (<$10k)", f"{(finals<10000).mean():.2%}")

st.caption("SPX Diagonal Engine v6.9.26 — FINAL FOREVER • Forward Curve • Nuclear Alerts • Correct Shrinkage • Monte Carlo Only • Dec 2025")
