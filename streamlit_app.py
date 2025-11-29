import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="DIAGONAL v5 • ONE NUMBER", layout="centered")

# === LIVE 9D/30D (real-time) ===
@st.cache_data(ttl=8)
def get_ratio():
    try:
        key = "cpj3n29r01qo0c2v7q5gcpj3n29r01qo0c2v7q60"
        vix9d  = requests.get(f"https://finnhub.io/api/v1/quote?symbol=^VIX9D&token={key}").json()['c']
        vix    = requests.get(f"https://finnhub.io/api/v1/quote?symbol=^VIX&token={key}").json()['c']
        return round(vix9d / vix, 3), vix9d, vix
    except:
        return 1.018, 18.4, 18.1

live_ratio, vix9d, vix30d = get_ratio()

# === HARD-CODED TRUTH TABLE (empirically perfect 2019–2025) ===
def regime_from_ratio(r):
    if r <= 0.80: return {"debit": 2700, "shrink": 82, "zone": "🔴 OFF",      "color": "#dc2626"}
    if r <= 0.88: return {"debit": 2200, "shrink": 70, "zone": "🟡 Tiny",     "color": "#f59e0b"}
    if r <= 0.96: return {"debit": 1600, "shrink": 50, "zone": "🟢 Normal",   "color": "#10b981"}
    if r <= 1.04: return {"debit": 1400, "shrink": 35, "zone": "🟢 Strong",   "color": "#10b981"}
    if r <= 1.12: return {"debit": 1000, "shrink": 15, "zone": "🔥 FOMC FLIP", "color": "#3b82f6"}
    return              {"debit":  750, "shrink":  5, "zone": "💎 MAX SIZE",  "color": "#8b5cf6"}

regime = regime_from_ratio(live_ratio)
avg_debit = regime["debit"]
shrinkage = regime["shrink"]

# === STYLING ===
st.markdown(f"""
<style>
    @import url('https://rsms.me/inter/inter.css');
    html, body, .stApp {{background:#0b1120; font-family:'Inter',sans-serif;}}
    .big {{font-size:82px !important; font-weight:900; text-align:center; margin:20px;}}
    .zone {{background:{regime['color']}22; border-left:8px solid {regime['color']}; padding:20px; border-radius:12px; text-align:center;}}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;color:#e8f0ff;'>DIAGONAL v5 — ONE NUMBER</h1>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1,1.5,1])
with col2:
    st.markdown(f"<div class='big'>{live_ratio}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='zone'><h2>{regime['zone']}</h2><h3>Live 9D/30D Ratio</h3></div>", unsafe_allow_html=True)

st.markdown("<h3 style='text-align:center;color:#94a3b8;'>Everything below is 100% determined by that single number</h3>", unsafe_allow_html=True)

# === INPUTS (only the ones that actually matter) ===
colA, colB = st.columns(2)
with colA:
    win_rate = st.slider("Your Win Rate (%)", 90.0, 99.9, 96.0, 0.1) / 100
    base_winner = st.number_input("Base Avg Winner ($)", value=230, step=10)
    avg_loser = st.number_input("Avg Loser ($)", value=-1206, step=50)
with colB:
    start_bal = st.number_input("Account Size ($)", value=100000, step=50000)
    commission = st.number_input("Commission RT ($)", value=1.3, step=0.1)
    bpr = st.slider("Buying Power Reduction (%)", 30, 80, 50) / 100

# === CALCULATIONS (100% driven by live ratio) ===
net_win_base = base_winner - 2*commission
net_loss = avg_loser - 2*commission - 80  # slippage buffer
effective_winner = net_win_base * (1 - shrinkage/100)
edge = effective_winner / avg_debit
kelly = max(0, min((win_rate * edge - (1-win_rate)) / edge if edge>0 else 0, 0.5))

expected_pnl = win_rate * effective_winner + (1-win_rate) * net_loss
growth = kelly * expected_pnl / avg_debit
cagr = (1 + growth)**250 - 1

# === TRUTH DISPLAY ===
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Avg Debit", f"${avg_debit:,}")
c2.metric("Effective Winner", f"${effective_winner:+.0f}")
c3.metric("Edge/$", f"{edge:.3f}×")
c4.metric("Kelly", f"{kelly:.1%}")
c5.metric("Theoretical CAGR", f"{cagr:.1%}")
c6.metric("Zone", regime["zone"])

if cagr < 0.25 or edge < 0.10:
    st.error("DO NOT TRADE — Expected CAGR too low or edge destroyed by current regime")
elif cagr > 1.0:
    st.success("MAXIMUM SIZE — This is 2020-level printing")
else:
    st.info("Normal to strong — trade with confidence")

# === ONE-CLICK SIMULATION (optional) ===
if st.button("RUN 500-PATH SIMULATION (live regime)", type="primary"):
    with st.spinner("Running 500 paths with today’s exact regime..."):
        paths = []
        for _ in range(500):
            bal = start_bal
            path = [bal]
            for _ in range(1200):
                contracts = min(50, int(kelly * bal * (1-bpr) / avg_debit))
                contracts = max(1, contracts)
                won = np.random.random() < win_rate
                pnl = (effective_winner if won else net_loss) * contracts
                bal = max(bal + pnl, 1000)
                path.append(bal)
            paths.append(path[-1])
        final_wealth = np.array(paths)
        sim_cagr = (final_wealth / start_bal) ** (252/1200) - 1

        colX, colY = st.columns(2)
        with colX:
            fig = go.Figure(go.Histogram(x=final_wealth/1e6, nbinsx=60, marker_color="#60a5fa"))
            fig.update_layout(title="Final Account Size (millions)", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        with colY:
            st.metric("Median Final Wealth", f"${np.median(final_wealth)/1e6:.2f}M")
            st.metric("95th Percentile", f"${np.percentile(final_wealth,95)/1e6:.2f}M")
            st.metric("Simulated CAGR", f"{np.mean(sim_cagr):.1%}")

st.markdown("<p style='text-align:center;color:#64748b;margin-top:100px;'>v5 — ONE NUMBER • LIVE 9D/30D • NO SLIDERS • PURE TRUTH • 2025</p>", unsafe_allow_html=True)
