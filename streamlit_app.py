import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time

# ── 3-SECOND MATRIX RAIN + SMOOTH FADE-IN TUNNEL ─────
placeholder = st.empty()
with placeholder.container():
    st.markdown("""
    <style>
    @keyframes fall {
        0% { transform: translateY(-100vh); opacity: 0; }
        20% { opacity: 1; }
        80% { opacity: 1; }
        100% { transform: translateY(100vh); opacity: 0; }
    }
    .matrix-char {
        color: #00ff41;
        font-family: 'Courier New', monospace;
        font-weight: bold;
        position: absolute;
        animation: fall 10s linear infinite;
        font-size: 20px;
    }
    .tunnel {
        background: #000;
        height: 100vh;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
    }
    </style>
    <div class="tunnel">
        <h1 style="color:#00ff41; font-family:'Courier New', monospace; font-size:4rem; text-shadow: 0 0 20px #00ff41;">
            ACCESSING CONSTRUCT...
        </h1>
        <p style="color:#00ff41; font-size:2rem; margin-top:30px;">DEBIT PUT DIAGONAL vFINAL</p>
    """ + "".join(
        f"<div class='matrix-char' style='left:{i*2.3}%; animation-delay:{j*0.2}s; top:-50px;'>"
        f"{np.random.choice(list('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#*$&'))}</div>"
        for i in range(44) for j in range(15)
    ) + "</div>", unsafe_allow_html=True)
    time.sleep(3.0)
    placeholder.empty()

# ── FULL MATRIX FONT + RETRO DOS THEME ───────────────
st.markdown("""
<style>
    .stApp {background:#000 !important; font-family:'Courier New', monospace !important;}
    h1, h2, h3, .stMarkdown, .stSlider label, .stNumberInput label, 
    .stTextInput label, .stSelectbox label, div, span, p {
        font-family:'Courier New', monospace !important;
        color:#00ff41 !important;
        font-weight:bold !important;
    }
    .stButton>button {background:#000; color:#00ff41; border:3px solid #ff0000; font-size:1.2rem;}
    input, .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background:#000 !important; color:#00ff41 !important; border:2px solid #00ff41 !important;
        font-family:'Courier New' !important; font-weight:bold !important;
    }
    .red-border {border: 3px solid #ff0000; padding: 15px; margin: 10px 0; background:#001100;}
    .section-title {color:#00ff41; font-size:1.6rem; border-bottom:3px solid #ff0000; padding-bottom:8px; text-align:left;}
</style>
""", unsafe_allow_html=True)

st.title("DEBIT PUT DIAGONAL vFINAL")
st.markdown("<h2 style='text-align:center; color:#00ff41; margin:20px;'>COMPOUNDING KELLY • BLACK SWAN • 1987 TERMINAL EDITION</h2>", 
            unsafe_allow_html=True)

# ── TWO WIDER, LEFT-ALIGNED COLUMNS ───────────────────
col1, col2 = st.columns([1.2, 1.2])

with col1:
    st.markdown("<div class='red-border'><div class='section-title'>EDGE PARAMETERS</div>", unsafe_allow_html=True)
    win_rate = st.slider("Win Rate (%)", 0.0, 100.0, 96.0, 0.1)/100
    avg_winner = st.number_input("Avg Winner (gross)", 230, step=10)
    avg_loser = st.number_input("Avg Loser (gross)", -1206, step=50)
    debit = st.number_input("Debit per Spread ($)", 1400, step=50)
    commission = st.number_input("Commission RT ($)", 1.30, step=0.10)
    slippage = st.number_input("Slippage Buffer ($)", 80, step=10)
    start_bal = st.number_input("Starting Balance ($)", 100000, step=10000)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='red-border'><div class='section-title'>SIMULATION & STRESS TEST</div>", unsafe_allow_html=True)
    num_trades = st.slider("Trades", 100, 5000, 1200)
    num_paths = st.slider("Monte Carlo Paths", 10, 1000, 300)
    max_contracts = st.number_input("Max Contracts", 1, 500, 10)
    bpr = st.slider("Buying Power Reduction (%)", 20, 90, 50)/100

    swan = st.checkbox("Black Swan Events", True)
    if swan:
        swan_freq = st.number_input("Frequency (1 in X)", 100, 2000, 500)
        swan_mag = st.number_input("Magnitude (× loser)", 2.0, 20.0, 6.0, 0.5)

    cluster = st.checkbox("Losing Streak Clustering", True)
    if cluster:
        cluster_mult = st.slider("Win rate multiplier in streak", 0.2, 0.9, 0.6, 0.05)
        max_streak = st.number_input("Max streak length", 1, 12, 5)

    st.markdown("</div>", unsafe_allow_html=True)

# ── KELLY & SIMULATION ───────────────────────────────
net_win = avg_winner - 2*commission
net_loss = avg_loser - 2*commission - slippage
p = win_rate
b = abs(net_win)/debit if debit > 0 else 0
kelly_f = max(0, min((p*b - (1-p))/b if b>0 else 0, 0.5))

st.sidebar.markdown(f"**KELLY f = {kelly_f:.1%}**")
st.sidebar.markdown(f"**Net Win ${net_win:.0f} | Net Loss ${net_loss:.0f}**")

if st.button("EXECUTE SIMULATION", type="primary"):
    with st.spinner("INITIALIZING..."):
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

        # BIG GRAPHS
        fig = go.Figure()
        for p in paths:
            fig.add_trace(go.Scatter(y=p, mode='lines', line=dict(width=1, color='rgba(0,255,65,0.06)'), showlegend=False, hoverinfo='skip'))
        fig.add_trace(go.Scatter(y=mean, mode='lines', name='MEAN', line=dict(color='#00ff41', width=7)))
        fig.add_hline(y=start_bal, line_color="#ff0000", line_dash="dot")
        fig.update_layout(height=650, template="plotly_dark", plot_bgcolor="#000", paper_bgcolor="#000",
                          font=dict(color="#00ff41", size=13), title="COMPOUNDING EQUITY PATHS")
        st.plotly_chart(fig, use_container_width=True)

        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(x=finals, nbinsx=80, marker_color='#00ff41'))
        fig2.add_vline(x=start_bal, line_color="#ff0000")
        fig2.update_layout(height=480, template="plotly_dark", plot_bgcolor="#000", paper_bgcolor="#000",
                           font=dict(color="#00ff41", size=13), title="FINAL BALANCE DISTRIBUTION")
        st.plotly_chart(fig2, use_container_width=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("AVG FINAL", f"${finals.mean():,.0f}")
        c2.metric("MEDIAN", f"${np.median(finals):,.0f}")
        c3.metric("WIN PATHS", f"{(finals>start_bal).mean()*100:.1f}%")
        c4.metric("RUIN RISK", f"{(finals<=5000).mean()*100:.2f}%")

# FIXED FINAL LINE
st.markdown("<p style='text-align:center; color:#ff0000; font-size:1.1rem; margin-top:40px;'>"
            "THERE IS NO SPOON • ONLY EDGE • 1987-2025</p>", unsafe_allow_html=True)
