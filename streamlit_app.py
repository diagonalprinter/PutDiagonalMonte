import streamlit as st
import numpy as np
import plotly.graph_objects as go

# ── PRESIDENTIAL CONFIG ─────────────────────────────
st.set_page_config(page_title="DEBIT PUT DIAGONAL • EXECUTIVE", layout="wide")

# ── WHITE HOUSE / BLACKROCK AESTHETIC ───────────────
st.markdown("""
<style>
    @import url('https://rsms.me/inter/inter.css');
    html, body, .stApp {background: #0b1120; font-family: 'Inter', sans-serif;}
    h1, h2, h3, h4 {color: #e8f0ff; font-weight: 700; letter-spacing: -0.5px;}
    .stMarkdown, label, .stSelectbox > div > div, p {color: #c0d6ff !important;}
    .css-1d391kg, .css-1v0mbdj {background: transparent;}
    .glass {background: rgba(20, 25, 50, 0.65); backdrop-filter: blur(12px); border-radius: 16px; 
            border: 1px solid rgba(100, 140, 255, 0.2); padding: 24px; box-shadow: 0 8px 32px rgba(0,0,0,0.4);}
    .gold {color: #d4af37;}
    .stButton>button {
        background: linear-gradient(135deg, #1e40af, #1e3a8a); color: white; 
        border: none; border-radius: 12px; padding: 14px 40px; font-size: 1.1rem; font-weight: 600;
        box-shadow: 0 4px 20px rgba(30,64,175,0.4);}
    .stButton>button:hover {background: #1e40af; transform: translateY(-2px);}
    input, .stNumberInput > div > div > input {background: rgba(15,20,40,0.8) !important; 
        color: white !important; border: 1px solid #3b82f6 !important; border-radius: 8px;}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 style='text-align:center; color:#e8f0ff; margin-bottom:8px;'>DEBIT PUT DIAGONAL</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center; color:#94a3b8; margin-top:0; margin-bottom:40px; letter-spacing:1px;'>EXECUTIVE RISK & COMPOUNDING ENGINE</h2>", unsafe_allow_html=True)

# ── TWO WIDE, INSTITUTIONAL COLUMNS ─────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.markdown("### Core Edge Parameters")
    win_rate = st.slider("Win Rate (%)", 0.0, 100.0, 96.0, 0.1, help="Historical closed-trade win rate") / 100
    avg_winner = st.number_input("Avg Winner (gross $)", 230, step=10)
    avg_loser = st.number_input("Avg Loser (gross $)", -1206, step=50)
    debit = st.number_input("Debit per Spread ($)", 1400, step=50)
    commission = st.number_input("Commission RT ($)", 1.30, step=0.10)
    slippage = st.number_input("Slippage/Assignment Buffer ($)", 80, step=10)
    start_bal = st.number_input("Starting Capital ($)", 100000, step=10000, format="%d")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.markdown("### Simulation & Institutional Stress")
    num_trades = st.slider("Number of Trades", 100, 5000, 1200, step=100)
    num_paths = st.slider("Monte Carlo Paths", 10, 1000, 300, step=50)
    max_contracts = st.number_input("Maximum Contracts per Trade", 1, 2000, 10)
    bpr = st.slider("Buying Power Reduction (%)", 20, 90, 50, help="Margin + psychological buffer") / 100

    st.markdown("**Catastrophic Risk Controls**")
    swan = st.checkbox("Black Swan Events", True)
    if swan:
        c1, c2 = st.columns(2)
        with c1: swan_freq = st.number_input("Frequency (1 in X)", 100, 3000, 500)
        with c2: swan_mag = st.number_input("Magnitude (× loser)", 2.0, 30.0, 6.0, 0.5)

    cluster = st.checkbox("Losing Streak Clustering", True)
    if cluster:
        c3, c4 = st.columns(2)
        with c3: cluster_mult = st.slider("Win-rate multiplier in streak", 0.1, 0.9, 0.6, 0.05)
        with c4: max_streak = st.number_input("Max streak length", 1, 15, 5)
    st.markdown("</div>", unsafe_allow_html=True)

# ── Kelly Calculation
net_win = avg_winner - 2*commission
net_loss = avg_loser - 2*commission - slippage
b = abs(net_win)/debit if debit > 0 else 0
kelly_f = max(0, min((win_rate*b - (1-win_rate))/b if b>0 else 0, 0.5))

# Sidebar metrics
with st.sidebar:
    st.markdown("### Position Sizing")
    st.markdown(f"**Kelly Fraction**: {kelly_f:.1%}")
    st.markdown(f"**Net Winner**: ${net_win:,.0f}")
    st.markdown(f"**Net Loser**: ${net_loss:,.0f}")

# ── EXECUTE
if st.button("RUN EXECUTIVE SIMULATION", type="primary"):
    with st.spinner("Executing institutional-grade simulation..."):
        paths = []
        for _ in range(num_paths):
            bal = start_bal
            path = [bal]
            streak = 0
            for _ in range(num_trades):
                usable = bal * (1 - bpr)
                contracts = min(max(1, int(kelly_f * usable / debit)), max_contracts)
                current_p = win_rate * (cluster_mult if cluster and streak > 0 else 1.0)
                won = np.random.random() < current_p

                if swan and np.random.random() < 1/swan_freq:
                    pnl = net_loss * swan_mag * contracts
                else:
                    pnl = (net_win if won else net_loss) * contracts

                if cluster and not won:
                    streak = min(np.random.geometric(0.6), max_streak)
                if cluster and streak > 0: streak -= 1

                bal = max(bal + pnl, 1000)
                path.append(bal)
            paths.append(path)

        paths = np.array(paths)
        mean = np.mean(paths, axis=0)
        finals = paths[:, -1]

        # Executive charts
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        fig = go.Figure()
        for p in paths:
            fig.add_trace(go.Scatter(y=p, mode='lines', line=dict(width=1, color='rgba(100,180,255,0.08)'), showlegend=False, hoverinfo='skip'))
        fig.add_trace(go.Scatter(y=mean, mode='lines', name='Mean Path', line=dict(color='#60a5fa', width=6)))
        fig.add_hline(y=start_bal, line_color="#e11d48", line_dash="dot", annotation_text="Starting Capital")
        fig.update_layout(height=680, template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          font=dict(color="#e8f0ff", size=14), title="Compounding Equity Paths – Institutional View")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(x=finals, nbinsx=80, marker_color='#60a5fa', name='Final Balance'))
        fig2.add_vline(x=start_bal, line_color="#e11d48", annotation_text="Breakeven")
        fig2.update_layout(height=480, template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           font=dict(color="#e8f0ff"), title="Terminal Wealth Distribution")
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Average Final Capital", f"${finals.mean():,.0f}")
        with c2: st.metric("Median Final Capital", f"${np.median(finals):,.0f}")
        with c3: st.metric("Profitable Paths", f"{(finals>start_bal).mean():.1%}")
        with c4: st.metric("Ruin Probability (<$5k)", f"{(finals<=5000).mean():.2%}")

st.markdown("<p style='text-align:center; color:#64748b; margin-top:80px; font-size:0.9rem;'>"
            "CLASSIFIED • EXECUTIVE LEVEL CLEARANCE • 2025</p>", unsafe_allow_html=True)
