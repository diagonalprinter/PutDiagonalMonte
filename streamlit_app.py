import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="DIAGONAL v5.3", layout="wide")

# === LIVE 9D/30D RATIO ===
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

# === REGIME ===
def regime_from_ratio(r):
    if r <= 0.80: return {"debit": 2700, "shrink": 82, "zone": "OFF", "color": "#dc2626", "light": "Red"}
    if r <= 0.88: return {"debit": 2200, "shrink": 70, "zone": "Tiny", "color": "#f59e0b", "light": "Yellow"}
    if r <= 0.96: return {"debit": 1600, "shrink": 50, "zone": "Normal", "color": "#10b981", "light": "Green"}
    if r <= 1.04: return {"debit": 1400, "shrink": 35, "zone": "Strong", "color": "#10b981", "light": "Green"}
    if r <= 1.12: return {"debit": 1000, "shrink": 15, "zone": "FOMC FLIP", "color": "#3b82f6", "light": "Green"}
    return {"debit": 750, "shrink": 5, "zone": "MAX SIZE", "color": "#8b5cf6", "light": "Green"}

regime = regime_from_ratio(live_ratio)
avg_debit = regime["debit"] + np.random.normal(0, 80)
shrinkage = regime["shrink"]

# === STYLE (perfect width & spacing) ===
st.markdown(f"""
<style>
    @import url('https://rsms.me/inter/inter.css');
    html, body, .stApp {{background:#0b1120; font-family:'Inter',sans-serif; line-height:1.6;}}
    .big {{font-size:82px !important; font-weight:900; text-align:center; margin:35px 0;}}
    .zone {{background:{regime['color']}22; border-left:8px solid {regime['color']}; padding:28px; border-radius:16px; text-align:center; margin:25px 0;}}
    .glass {{background:rgba(20,25,50,0.65); backdrop-filter:blur(12px); border-radius:16px; border:1px solid rgba(100,140,255,0.2); padding:32px; margin:20px 0;}}
    .stPlotlyChart {{margin:30px 0 !important;}}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;color:#e8f0ff;margin:40px 0;'>DIAGONAL v5.3</h1>", unsafe_allow_html=True)
st.markdown(f"<div class='big'>{live_ratio}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='zone'><h2>{regime['zone']}</h2><h3>Live 9D/30D Ratio — {regime['light']} Go</h3></div>", unsafe_allow_html=True)

# === INPUTS (perfect width) ===
col1, col2 = st.columns([1.1, 1.1])  # ← This is your perfect "in-between" width

with col1:
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.markdown("### Core Edge")
    win_rate = st.slider("Win Rate (%)", 0.0, 100.0, 96.0, 0.1) / 100   # ← Now 0–100%
    base_winner = st.number_input("Base Avg Winner ($)", value=230, step=10)
    avg_loser = st.number_input("Avg Loser ($)", value=-1206, step=50)
    commission = st.number_input("Commission RT ($)", value=1.3, step=0.1)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.markdown("### Simulation")
    start_bal = st.number_input("Account ($)", value=100000, step=50000)
    num_trades = st.slider("Trades", 100, 5000, 1200)
    num_paths = st.slider("Monte Carlo Paths", 50, 1000, 300)
    max_contracts = st.number_input("Contract Cap", value=10, min_value=1)
    st.markdown("</div>", unsafe_allow_html=True)

# === CALCULATIONS ===
net_win_base = base_winner - 2*commission
net_loss = avg_loser - 2*commission - 80
effective_winner = net_win_base * (1 - shrinkage/100)
edge = effective_winner / avg_debit
kelly = max(0, min((win_rate * edge - (1-win_rate)) / edge if edge>0 else 0, 0.5))
growth = kelly * (win_rate * effective_winner + (1-win_rate) * net_loss) / avg_debit
cagr = (1 + growth)**250 - 1

# === METRICS (spaced nicely) ===
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Debit", f"${avg_debit:,.0f}")
c2.metric("Winner", f"${effective_winner:+.0f}")
c3.metric("Edge/$", f"{edge:.3f}×")
c4.metric("Kelly", f"{kelly:.1%}")
c5.metric("CAGR", f"{cagr:.1%}")

# === DECISION ===
if cagr < 0.25 or edge < 0.10:
    st.error("DO NOT TRADE TODAY")
elif cagr > 1.2:
    st.success("MAXIMUM SIZE — Print mode")
else:
    st.info("Trade normally — Solid regime")

# === SIMULATION WITH PATH GRAPH ===
if st.button("RUN 500-PATH SIMULATION", type="primary"):
    with st.spinner("Running 500 paths..."):
        paths = []
        for _ in range(500):
            bal = start_bal
            path = [bal]
            streak = 0
            for _ in range(num_trades):
                contracts = min(max_contracts, max(1, int(kelly * bal * 0.5 / avg_debit)))
                p = win_rate * (0.60 if streak > 0 else 1.0)
                won = np.random.random() < p

                if np.random.random() < 1/500:
                    pnl = net_loss * np.random.choice([5, 7, 10]) * contracts
                else:
                    pnl = (effective_winner if won else net_loss) * contracts

                if not won and np.random.random() < 0.65:
                    streak += 1
                else:
                    streak = 0

                bal = max(bal + pnl, 1000)
                path.append(bal)
            paths.append(path)

        paths = np.array(paths)
        mean_path = np.mean(paths, axis=0)
        finals = paths[:, -1]
        sim_cagr = (finals / start_bal) ** (252/num_trades) - 1

        # PATH FAN
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        fig = go.Figure()
        for p in paths[:100]:
            fig.add_trace(go.Scatter(y=p, mode='lines', line=dict(width=1, color='rgba(100,180,255,0.1)'), showlegend=False))
        fig.add_trace(go.Scatter(y=mean_path, mode='lines', name='Mean Path', line=dict(color='#60a5fa', width=6)))
        fig.add_hline(y=start_bal, line_color="#e11d48", line_dash="dot")
        fig.update_layout(height=580, template="plotly_dark", title="500 Equity Paths")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        colA, colB = st.columns(2)
        with colA:
            fig2 = go.Figure(go.Histogram(x=finals/1e6, nbinsx=70, marker_color='#60a5fa'))
            fig2.update_layout(height=480, template="plotly_dark", title="Final Wealth (millions)")
            st.plotly_chart(fig2, use_container_width=True)
        with colB:
            st.metric("Median Final", f"${np.median(finals)/1e6:.2f}M")
            st.metric("95th Percentile", f"${np.percentile(finals,95)/1e6:.2f}M")
            st.metric("Avg Sim CAGR", f"{np.mean(sim_cagr):.1%}")
            st.metric("Ruin Rate", f"{(finals<10000).mean():.1%}")

st.markdown("<p style='text-align:center;color:#64748b;margin-top:120px;'>v5.3 — PERFECT WIDTH • 0–100% WIN RATE • PATH FAN • ELEGANT • 2025</p>", unsafe_allow_html=True)
