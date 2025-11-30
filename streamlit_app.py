import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="SPX Diagonal Engine v6.9.2", layout="wide")

# === LIVE DATA ===
@st.cache_data(ttl=15)
def get_market_data():
    try:
        key = "cpj3n29r01qo0c2v7q5gcpj3n29r01qo0c2v7q60"
        vix9d = requests.get(f"https://finnhub.io/api/v1/quote?symbol=^VIX9D&token={key}").json()['c']
        vix30d = requests.get(f"https://finnhub.io/api/v1/quote?symbol=^VIX&token={key}").json()['c']
        spx = requests.get(f"https://finnhub.io/api/v1/quote?symbol=^GSPC&token={key}").json()['c']
        es = requests.get(f"https://finnhub.io/api/v1/quote?symbol=ES=F&token={key}").json()['c']
        ratio = round(vix9d / vix30d, 3) if vix30d > 0 else 1.018
        return ratio, round(spx, 1), round(es, 1)
    except:
        return 1.018, 6000.0, 6015.0

live_ratio, spx_price, es_price = get_market_data()
update_time = datetime.now().strftime("%H:%M:%S ET")

# === REGIME ===
def get_regime(r):
    if r <= 0.84:   return {"shrink":60, "zone":"OFF",        "color":"#dc2626"}
    if r <= 0.88:   return {"shrink":32, "zone":"MARGINAL",   "color":"#f59e0b"}
    if r <= 0.94:   return {"shrink":8,  "zone":"OPTIMAL",    "color":"#10b981"}
    if r <= 1.04:   return {"shrink":12, "zone":"ACCEPTABLE", "color":"#10b981"}
    if r <= 1.12:   return {"shrink":5,  "zone":"ENHANCED",   "color":"#3b82f6"}
    return                {"shrink":2,  "zone":"MAXIMUM",    "color":"#8b5cf6"}

regime = get_regime(live_ratio)
shrinkage_pct = regime["shrink"]
light = "Red" if live_ratio <= 0.84 else "Amber" if live_ratio <= 0.88 else "Green"

# === STYLE (smaller elements + grid borders) ===
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, .stApp {background:#0b1120; font-family:'Inter',sans-serif; color:#e2e8f0;}
    .big-num {font-size:36px; font-weight:700; text-align:center; color:#ffffff; margin:10px 0;}
    .metric-card {background:#1e293b; padding:12px; border-radius:8px; border:1px solid #334155; border-left:3px solid #64748b;}
    .stButton>button {background:#334155; color:white; border:none; border-radius:8px; height:44px; font-size:14px; font-weight:600;}
    .gauge-container {height:140px; margin:5px 0;}
</style>
""", unsafe_allow_html=True)

# === HEADER GRID (smaller, bordered, no cut-off) ===
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown("""
    <div class="metric-card">
        <p style="font-size:12px; color:#94a3b8; margin:0;">9D/30D Ratio</p>
        <p class="big-num">{}</p>
    </div>
    """.format(live_ratio), unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="metric-card">
        <p style="font-size:12px; color:#94a3b8; margin:0;">Current Regime</p>
        <p class="big-num">{}</p>
    </div>
    """.format(regime["zone"]), unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="metric-card">
        <p style="font-size:12px; color:#94a3b8; margin:0;">Market Light</p>
        <p class="big-num">{}</p>
    </div>
    """.format(light), unsafe_allow_html=True)

with c4:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=live_ratio,
        number={'font': {'size': 24, 'color': '#60a5fa'}},
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
        title={'text': "52-Week Position", 'font': {'size': 10}}
    ))
    fig.update_layout(height=140, margin=dict(t=0, b=5, l=5, r=5), paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
    st.plotly_chart(fig, use_container_width=True)

with c5:
    st.markdown("""
    <div class="metric-card">
        <p style="font-size:12px; color:#94a3b8; margin:0;">SPX • ES Futures</p>
        <p class="big-num">{spx:.0f} • {es:.0f}</p>
        <p style="font-size:10px; color:#94a3b8; margin:0;">Updated {time}</p>
    </div>
    """.format(spx=spx_price, es=es_price, time=datetime.now().strftime("%H:%M ET")), unsafe_allow_html=True)

# === VIX NOTE ===
st.markdown(f"<p style='text-align:center; color:#94a3b8; font-size:12px; margin:10px 0;'>9D/30D live during 9:30 AM–4 PM ET | Futures 24/7 | Last update: {datetime.now().strftime('%H:%M ET')}</p>", unsafe_allow_html=True)

st.markdown("---")

# === INPUTS ===
left, right = st.columns([1, 1])
with left:
    st.subheader("Strategy Parameters")
    user_debit = st.number_input("Current Debit ($)", 100, 5000, 1350, 10)
    win_rate = st.slider("Win Rate (%)", 0.0, 100.0, 96.0, 0.1) / 100
    base_winner = st.number_input("Theoretical Winner ($)", value=230, step=5)
    avg_loser = st.number_input("Average Loser ($)", value=-1206, step=25)
    commission = st.number_input("Commission RT ($)", value=1.3, step=0.1)

with right:
    st.subheader("Simulation Controls")
    start_bal = st.number_input("Starting Capital ($)", value=100000, step=25000)
    max_contracts = st.number_input("Max Contracts", value=10, min_value=1)
    num_trades = st.slider("Total Trades", 0, 3000, 150, 10)
    num_paths = st.slider("Monte Carlo Paths", 50, 1000, 300, 25)

# === CALCULATIONS ===
net_win = base_winner - 2 * commission
net_loss = avg_loser - 2 * commission - 80
effective_winner = net_win * (1 - shrinkage_pct / 100)
edge_per_dollar = effective_winner / user_debit
raw_kelly = (win_rate * edge_per_dollar - (1 - win_rate)) / edge_per_dollar if edge_per_dollar > 0 else 0
kelly_f = max(0.0, min(0.25, raw_kelly))
daily_growth = kelly_f * (win_rate * effective_winner + (1 - win_rate) * net_loss) / user_debit
theoretical_cagr = (1 + daily_growth) ** 250 - 1

# === METRICS ===
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Debit", f"${user_debit:,}")
m2.metric("Effective Winner", f"${effective_winner:+.0f}")
m3.metric("Edge/$", f"{edge_per_dollar:.3f}×")
m4.metric("Kelly", f"{kelly_f:.1%}")
m5.metric("Theoretical CAGR", f"{theoretical_cagr:.1%}")

# === LEGENDS ===
l1, l2 = st.columns(2)
with l1:
    st.markdown("#### Edge/$ Guide")
    st.table({"Edge/$": [">=0.180", "0.150-0.179", "0.120-0.149", "0.100-0.119", "<0.100"], "Action": ["Full aggression", "Strong", "Good", "Small only", "Skip"]})
with l2:
    st.markdown("#### Regime Map")
    st.table({"Ratio": ["<=0.84", "<=0.88", "<=0.94", "<=1.04", "<=1.12", ">1.12"], "Zone": ["OFF", "MARGINAL", "OPTIMAL", "ACCEPTABLE", "ENHANCED", "MAXIMUM"], "Shrinkage": ["60%", "32%", "8%", "12%", "5%", "2%"]})

# === SIMULATION ===
if st.button("RUN SIMULATION", use_container_width=True):
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

                    if np.random.random() < 0.01:
                        pnl = net_loss * 2.5 * contracts
                    else:
                        pnl = (effective_winner if won else net_loss) * contracts

                    if not won and np.random.random() < 0.50:
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
            years_sim = num_trades / 150.0
            sim_cagr = (finals / start_bal) ** (1 / years_sim) - 1 if years_sim > 0 else 0

            col_chart, col_stats = st.columns([2.5, 1])
            with col_chart:
                fig = go.Figure()
                for p in paths[:100]:
                    fig.add_trace(go.Scatter(y=p, mode='lines', line=dict(width=1, color='rgba(100,149,237,0.15)'), showlegend=False))
                fig.add_trace(go.Scatter(y=mean_path, mode='lines', line=dict(color='#60a5fa', width=5), name='Mean Path'))
                fig.add_hline(y=start_bal, line_color="#e11d48", line_dash="dash")
                fig.update_layout(template="plotly_dark", height=560, title="Equity Curve Distribution")
                st.plotly_chart(fig, use_container_width=True)

            with col_stats:
                st.metric("Median Final", f"${np.median(finals)/1e6:.2f}M")
                st.metric("95th %ile", f"${np.percentile(finals,95)/1e6:.2f}M")
                st.metric("Mean CAGR", f"{np.mean(sim_cagr):.1%}")
                st.metric("Ruin Probability", f"{(finals<10_000).mean():.2%}")

st.markdown("<p style='text-align:center;color:#475569;margin-top:100px;font-size:14px;'>SPX Debit Put Diagonal Engine v6.9.2 — Live Data • 2025</p>", unsafe_allow_html=True)
