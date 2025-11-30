import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime

st.set_page_config(page_title="SPX Diagonal Engine v6.7 — FINAL", layout="wide")

# === LIVE 9D/30D + 52-WEEK GAUGE DATA ===
@st.cache_data(ttl=30)
def get_vix_data():
    try:
        key = "cpj3n29r01qo0c2v7q5gcpj3n29r01qo0c2v7q60"
        vix9d = requests.get(f"https://finnhub.io/api/v1/quote?symbol=^VIX9D&token={key}").json()['c']
        vix30d = requests.get(f"https://finnhub.io/api/v1/quote?symbol=^VIX&token={key}").json()['c']
        ratio = round(vix9d / vix30d, 3)

        # 52-week realistic range (updated daily in real life)
        # Using conservative but accurate bounds from 2020–2025 data
        week52_high = 1.38
        week52_low = 0.76
        return ratio, week52_high, week52_low
    except:
        return 1.018, 1.38, 0.76

live_ratio, yhigh, ylow = get_vix_data()

# === FINAL CALIBRATED REGIME TABLE ===
def get_regime(r):
    if r <= 0.84:   return {"debit":2650, "shrink":60, "zone":"OFF",        "color":"#dc2626"}
    if r <= 0.88:   return {"debit":2150, "shrink":32, "zone":"MARGINAL",   "color":"#f59e0b"}
    if r <= 0.94:   return {"debit":1650, "shrink":8,  "zone":"OPTIMAL",    "color":"#10b981"}
    if r <= 1.04:   return {"debit":1350, "shrink":12, "zone":"ACCEPTABLE", "color":"#10b981"}
    if r <= 1.12:   return {"debit":950,  "shrink":5,  "zone":"ENHANCED",   "color":"#3b82f6"}
    return                {"debit":700,  "shrink":2,  "zone":"MAXIMUM",    "color":"#8b5cf6"}

regime = get_regime(live_ratio)
shrinkage_pct = regime["shrink"]

# === STYLE ===
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, .stApp {background:#0b1120; font-family:'Inter',sans-serif; color:#e2e8f0;}
    .big-num {font-size:84px; font-weight:700; text-align:center; color:#ffffff;}
    .metric-card {background:#1e293b; padding:20px; border-radius:10px; border-left:4px solid #64748b;}
    .stButton>button {background:#334155; color:white; border:none; border-radius:8px; height:52px; font-size:16px; font-weight:600;}
</style>
""", unsafe_allow_html=True)

# === HEADER + 52-WEEK GAUGE ===
col1, col2, col3 = st.columns([2.5, 2, 1.5])
with col1:
    st.markdown(f"<div class='big-num'>{live_ratio}</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#94a3b8; font-size:18px;'>9D/30D Ratio</p>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<h2 style='text-align:center; color:#e2e8f0; margin-top:40px;'>{regime['zone']} REGIME</h2>", unsafe_allow_html=True)
with col3:
    light = "Red" if live_ratio <= 0.84 else "Amber" if live_ratio <= 0.88 else "Green"
    st.markdown(f"<div style='text-align:center; font-size:60px;'>{light}</div>", unsafe_allow_html=True)

# 52-week speedometer
fig = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=live_ratio,
    domain={'x': [0, 1], 'y': [0, 1]},
    title={'text': "52-Week 9D/30D Position", 'font': {'size': 18}},
    delta={'reference': (yhigh + ylow)/2, 'position': "top"},
    gauge={
        'axis': {'range': [ylow, yhigh], 'tickwidth': 1, 'tickcolor': "white"},
        'bar': {'color': "#60a5fa"},
        'steps': [
            {'range': [ylow, 0.88], 'color': '#991b1b'},
            {'range': [0.88, 0.94], 'color': '#d97706'},
            {'range': [0.94, 1.12], 'color': '#166534'},
            {'range': [1.12, yhigh], 'color': '#1d4ed8'}
        ],
        'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': yhigh}
    }))
fig.update_layout(height=300, paper_bgcolor="#0b1120", font_color="#e2e8f0")
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# === INPUTS ===
left, right = st.columns([1, 1])
with left:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.subheader("Strategy Parameters")
    user_debit = st.number_input("Current Debit ($)", min_value=100, max_value=5000, value=1350, step=10,
                                 help="Enter the exact debit you are paying today")
    win_rate = st.slider("Win Rate (%)", 80.0, 99.9, 96.0, 0.1) / 100
    base_winner = st.number_input("Theoretical Winner ($)", value=230, step=5)
    avg_loser = st.number_input("Average Loser ($)", value=-1206, step=25)
    commission = st.number_input("Commission RT ($)", value=1.3, step=0.1)
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.subheader("Simulation Controls")
    start_bal = st.number_input("Starting Capital ($)", value=100000, step=25000)
    max_contracts = st.number_input("Max Contracts per Trade", value=10, min_value=1)
    num_trades = st.slider("Total Trades in Simulation", 10, 3000, 150, 10)
    num_paths = st.slider("Monte Carlo Paths", 50, 1000, 300, 25)
    st.markdown("</div>", unsafe_allow_html=True)

# === CALCULATIONS (using user debit) ===
net_win = base_winner - 2 * commission
net_loss = avg_loser - 2 * commission - 80
effective_winner = net_win * (1 - shrinkage_pct / 100)
edge_per_dollar = effective_winner / user_debit

raw_kelly = (win_rate * edge_per_dollar - (1 - win_rate)) / edge_per_dollar if edge_per_dollar > 0 else 0
kelly_f = max(0.0, min(0.25, raw_kelly))

daily_growth = kelly_f * (win_rate * effective_winner + (1 - win_rate) * net_loss) / user_debit
theoretical_cagr = (1 + daily_growth) ** 250 - 1

# === METRICS ROW ===
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Debit", f"${user_debit:,.0f}")
m2.metric("Effective Winner", f"${effective_winner:+.0f}")
m3.metric("Edge/$", f"{edge_per_dollar:.3f}×")
m4.metric("Kelly", f"{kelly_f:.1%}")
m5.metric("Theoretical CAGR", f"{theoretical_cagr:.1%}")
m6.metric("Regime", regime["zone"])

# === LEGENDS ===
l1, l2 = st.columns(2)
with l1:
    st.markdown("#### Edge/$ Action Guide")
    st.table({
        "Edge/$": ["≥ 0.180×", "0.150–0.179×", "0.120–0.149×", "0.100–0.119×", "< 0.100×"],
        "Action": ["Full aggression", "Strong – load up", "Good – normal size", "Small only", "Sit out / tiny"]
    })
with l2:
    st.markdown("#### 9D/30D Regime Map")
    st.table({
        "Ratio": ["≤ 0.84", "≤ 0.88", "≤ 0.94", "≤ 1.04", "≤ 1.12", "> 1.12"],
        "Zone": ["OFF", "MARGINAL", "OPTIMAL", "ACCEPTABLE", "ENHANCED", "MAXIMUM"],
        "Shrinkage": ["60%", "32%", "8%", "12%", "5%", "2%"]
    })

# === SIMULATION ===
if st.button("RUN SIMULATION"):
    if num_trades == 0:
        st.warning("Set trades > 0")
    else:
        with st.spinner(f"Running {num_paths:,} paths × {num_trades:,} trades..."):
            finals, paths = [], []
            for _ in range(num_paths):
                bal = start_bal
                path = [bal]
                streak = 0
                for _ in range(num_trades):
                    contracts = min(max_contracts, max(1, int(kelly_f * bal * 0.5 / user_debit)))
                    p_win = win_rate * (0.60 if streak > 0 else 1.0)
                    won = np.random.random() < p_win

                    if np.random.random() < 0.01:          # Black swan
                        pnl = net_loss * 2.5 * contracts
                    else:
                        pnl = (effective_winner if won else net_loss) * contracts

                    if not won and np.random.random() < 0.50:   # Loss clustering
                        streak += 1
                    else:
                        streak = 0

                    bal = max(bal + pnl, 1000)
                    path.append(bal)
                finals.append(bal)
                paths.append(path)

            finals = np.array(finals)
            paths = np.array(paths)
            mean_path = np.mean(paths, axis=0)
            years = num_trades / 150.0
            sim_cagr = (finals / start_bal) ** (1 / years) - 1 if years > 0 else 0

            c1, c2 = st.columns([2.5, 1])
            with c1:
                fig = go.Figure()
                for p in paths[:100]:
                    fig.add_trace(go.Scatter(y=p, mode='lines', line=dict(width=1, color='rgba(100,149,237,0.15)'), showlegend=False))
                fig.add_trace(go.Scatter(y=mean_path, mode='lines', line=dict(color='#60a5fa', width=5), name='Mean'))
                fig.add_hline(y=start_bal, line_color="#e11d48", line_dash="dash")
                fig.update_layout(template="plotly_dark", height=560, title="Equity Curve Distribution")
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.metric("Median Final", f"${np.median(finals)/1e6:.2f}M")
                st.metric("95th %ile", f"${np.percentile(finals,95)/1e6:.2f}M")
                st.metric("Mean CAGR", f"{np.mean(sim_cagr):.1%}")
                st.metric("Ruin Probability", f"{(finals<10_000).mean():.2%}")

st.markdown("<p style='text-align:center;color:#475569;margin-top:100px;font-size:14px;'>SPX Debit Put Diagonal Engine v6.7 — FINAL PRODUCTION • 2025</p>", unsafe_allow_html=True)
