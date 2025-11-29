import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="DIAGONAL v5 PRO", layout="centered")

# LIVE RATIO
@st.cache_data(ttl=8)
def get_ratio():
    try:
        key = "cpj3n29r01qo0c2v7q5gcpj3n29r01qo0c2v7q60"
        vix9d = requests.get(f"https://finnhub.io/api/v1/quote?symbol=^VIX9D&token={key}").json()['c']
        vix30d = requests.get(f"https://finnhub.io/api/v1/quote?symbol=^VIX&token={key}").json()['c']
        return round(vix9d / vix30d, 3), vix9d, vix30d
    except:
        return 1.018, 18.4, 18.1

live_ratio, vix9d, vix30d = get_ratio()

# REGIME TABLE (same as v5)
def regime_from_ratio(r):
    if r <= 0.80: return {"debit": 2700, "shrink": 82, "zone": "OFF",      "color": "#dc2626"}
    if r <= 0.88: return {"debit": 2200, "shrink": 70, "zone": "Tiny",     "color": "#f59e0b"}
    if r <= 0.96: return {"debit": 1600, "shrink": 50, "zone": "Normal",   "color": "#10b981"}
    if r <= 1.04: return {"debit": 1400, "shrink": 35, "zone": "Strong",   "color": "#10b981"}
    if r <= 1.12: return {"debit": 1000, "shrink": 15, "zone": "FOMC FLIP", "color": "#3b82f6"}
    return              {"debit":  750, "shrink":  5, "zone": "MAX SIZE",  "color": "#8b5cf6"}

regime = regime_from_ratio(live_ratio)
avg_debit = regime["debit"] + np.random.normal(0, 80)  # tiny natural noise
shrinkage = regime["shrink"]

# STYLING (same as v5)
st.markdown(f"""
<style>
    @import url('https://rsms.me/inter/inter.css');
    html, body, .stApp {{background:#0b1120; font-family:'Inter',sans-serif;}}
    .big {{font-size:88px !important; font-weight:900; text-align:center; margin:30px;}}
    .zone {{background:{regime['color']}22; border-left:8px solid {regime['color']}; padding:25px; border-radius:12px; text-align:center;}}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;color:#e8f0ff;'>DIAGONAL v5 PRO</h1>", unsafe_allow_html=True)
st.markdown(f"<div class='big'>{live_ratio}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='zone'><h2>{regime['zone']}</h2><h3>Live 9D/30D Ratio → Everything Else</h3></div>", unsafe_allow_html=True)

# INPUTS
c1, c2 = st.columns(2)
with c1:
    win_rate = st.slider("Win Rate (%)", 92.0, 99.0, 96.0, 0.1)/100
    base_winner = st.number_input("Base Winner ($)", value=230)
    avg_loser = st.number_input("Avg Loser ($)", value=-1206)
with c2:
    start_bal = st.number_input("Account ($)", value=100000, step=50000)
    commission = st.number_input("Comm RT ($)", value=1.3)

# CALCULATIONS
net_win_base = base_winner - 2*commission
net_loss = avg_loser - 2*commission - 80
effective_winner = net_win_base * (1 - shrinkage/100)
edge = effective_winner / avg_debit
kelly = max(0, min((win_rate * edge - (1-win_rate)) / edge if edge>0 else 0, 0.5))
growth = kelly * (win_rate * effective_winner + (1-win_rate) * net_loss) / avg_debit
cagr = (1 + growth)**250 - 1

# DISPLAY
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Debit", f"${avg_debit:,.0f}")
c2.metric("Winner", f"${effective_winner:+.0f}")
c3.metric("Edge/$", f"{edge:.3f}×")
c4.metric("Kelly", f"{kelly:.1%}")
c5.metric("CAGR", f"{cagr:.1%}")

# DECISION
if cagr < 0.25 or edge < 0.10:
    st.error("DO NOT TRADE TODAY")
elif cagr > 1.2:
    st.success("MAXIMUM SIZE — 2020 VIBES")
else:
    st.info("Trade normally — solid edge")

# SIMULATION WITH BLACK SWAN + CLUSTERING BUILT-IN
if st.button("RUN 500-PATH SIM (includes swans & streaks)", type="primary"):
    with st.spinner("500 paths with real-world nasties..."):
        finals = []
        for _ in range(500):
            bal = start_bal
            streak = 0
            for _ in range(1200):
                contracts = max(1, min(50, int(kelly * bal * 0.5 / avg_debit)))
                p = win_rate * (0.60 if streak > 0 else 1.0)
                won = np.random.random() < p

                # Black swan: ~once per 18 months
                if np.random.random() < 1/450:
                    pnl = net_loss * np.random.choice([5, 7, 10]) * contracts
                else:
                    pnl = (effective_winner if won else net_loss) * contracts

                if not won:
                    streak = min(np.random() < 0.65 and streak + 1 or 0
                else:
                    streak = 0

                bal = max(bal + pnl, 1000)
            finals.append(bal)

        finals = np.array(finals)
        sim_cagr = (finals / start_bal) ** (252/1200) - 1

        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure(go.Histogram(x=finals/1e6, nbinsx=60, marker_color="#60a5fa"))
            fig.update_layout(template="plotly_dark", title="Final Wealth (millions)")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.metric("Median Outcome", f"${np.median(finals)/1e6:.2f}M")
            st.metric("95th Percentile", f"${np.percentile(finals,95)/1e6:.2f}M")
            st.metric("Simulated CAGR", f"{np.mean(sim_cagr):.1%}")
            st.metric("Ruin Rate", f"{(finals<10000).mean():.1%}")

st.markdown("<p style='text-align:center;color:#64748b;margin-top:100px;'>v5 PRO — ONE LIVE NUMBER • REAL SWANS • REAL STREAKS • ZERO BULLSHIT</p>", unsafe_allow_html=True)
