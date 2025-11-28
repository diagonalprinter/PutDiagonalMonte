import streamlit as st
import numpy as np
import plotly.graph_objects as go

# ── MATRIX RAIN HEADER (animated!) ─────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@900&display=swap');
    .matrix-header {
        font-family: 'Orbitron', 'Courier New', monospace;
        color: #00ff41;
        font-size: 3.2rem;
        text-align: center;
        text-shadow: 0 0 10px #00ff41;
        letter-spacing: 8px;
        margin-bottom: 0;
    }
    .rain {
        background: #000;
        padding: 20px 0;
        overflow: hidden;
        position: relative;
    }
    .css-1d391kg {padding: 1rem 0 !important;}
    body, .stApp {background-color: #000 !important; color: #00ff41;}
    .stSlider > div > div > div > div {background: #003300;}
    h1, h2, h3, h4 {color: #00ff41 !important; font-family: 'Courier New', monospace;}
    .stButton>button {background:#000; color:#00ff41; border:2px solid #00ff41; font-weight:bold;}
    .stTextInput>div>div>input {background:#000; color:#00ff41; border:1px solid #00ff41;}
    .stNumberInput>div>div>input {background:#000; color:#00ff41; border:1px solid #00ff41;}
</style>

<div class="rain">
<div class="matrix-header">MATRIX DIAGONAL v∞</div>
<div style="text-align:center; color:#00ff41; font-size:1.1rem; letter-spacing:4px;">
    COMPOUNDING KELLY • BLACK SWAN • STRESS TEST ENGINE
</div>
</div>
""", unsafe_allow_html=True)

st.set_page_config(page_title="MATRIX DIAGONAL", layout="wide")

# ── NARROW INPUTS (perfect on ultrawide) ───────────────
left, mid, right = st.columns([1, 1.8, 1])

with mid:
    st.markdown("### EDGE PARAMETERS")
    win_rate = st.slider("Win Rate (%)", 0.0, 100.0, 96.0, 0.1) / 100
    avg_winner = st.number_input("Avg Winner (gross $)", 230, step=10)
    avg_loser = st.number_input("Avg Loser (gross $)", -1206, step=50)
    debit = st.number_input("Debit per Spread ($)", 1400, step=50)
    commission = st.number_input("Commission round-trip ($)", 1.30, step=0.10)
    slippage = st.number_input("Slippage Buffer ($)", 80, step=10)
    start_bal = st.number_input("Starting Balance ($)", 100000, step=10000)

    st.markdown("### REALITY DISTORTIONS")
    max_contracts = st.number_input("Max Contracts per Trade", 1, 500, 10, step=5)
    bpr = st.slider("Buying Power Reduction (%)", 20, 90, 50)/100

    # Black Swan
    swan_on = st.checkbox("Enable Black Swan Events", True)
    if swan_on:
        swan_freq = st.number_input("Black Swan Frequency (1 in X trades)", 100, 2000, 500)
        swan_mag = st.number_input("Black Swan Magnitude (× normal loser)", 2.0, 20.0, 6.0, 0.5)

    # Losing Streaks
    streak_on = st.checkbox("Enable Losing-Streak Clustering", True)
    if streak_on:
        streak_mult = st.slider("Win-rate multiplier during streak", 0.3, 0.9, 0.6, 0.05)
        max_streak = st.number_input("Max streak length", 1, 10, 4)

    num_trades = st.slider("Number of Trades", 100, 5000, 1200, step=100)
    num_paths = st.slider("Monte Carlo Paths", 10, 1000, 300, step=50)
    seed = st.checkbox("Fixed random seed", True)

if seed:
    np.random.seed(42)

# ── KELLY & NET EDGE ───────────────────────────────────
net_win = avg_winner - 2*commission
net_loss = avg_loser - 2*commission - slippage
p = win_rate
b = abs(net_win)/debit
kelly_f = max(0, min((p*b - (1-p))/b if b>0 else 0, 0.5))

st.sidebar.markdown(f"**KELLY f = {kelly_f:.1%}**")
st.sidebar.markdown(f"**Net win ${net_win:.0f} | Net loss ${net_loss:.0f}**")

# ── SIMULATION ────────────────────────────────────────
if st.button(">> BREACH THE MATRIX", type="primary"):
    with st.spinner("Simulating alternate realities..."):
        all_paths = []

        for _ in range(num_paths):
            bal = start_bal
            path = [bal]
            streak = 0

            for t in range(num_trades):
                usable = bal * (1 - bpr)
                contracts = min(max(1, int(kelly_f * usable / debit)), max_contracts)

                # Win probability
                current_p = win_rate
                if streak_on and streak > 0:
                    current_p *= streak_mult
                    streak -= 1

                won = np.random.random() < current_p

                # Black swan?
                if swan_on and np.random.random() < (1/swan_freq):
                    pnl = net_loss * swan_mag * contracts
                else:
                    pnl = (net_win if won else net_loss) * contracts

                if not won and streak_on:
                    streak = np.random.geometric(0.7) if np.random.random() < 0.4 else 0
                    streak = min(streak, max_streak)

                bal = max(bal + pnl, 1000)
                path.append(bal)

            all_paths.append(path)

        all_paths = np.array(all_paths)
        mean_path = np.mean(all_paths, axis=0)
        finals = all_paths[:, -1]

        # ── PLOT ───────────────────────────────────────
        fig = go.Figure()
        for p in all_paths:
            fig.add_trace(go.Scatter(y=p, mode='lines', line=dict(width=1, color='rgba(0,255,65,0.06)'),
                                     showlegend=False, hoverinfo='skip'))
        fig.add_trace(go.Scatter(y=mean_path, mode='lines', name='MEAN PATH',
                                 line=dict(color='#00ff41', width=6)))
        fig.add_hline(y=start_bal, line_color="#001100", line_dash="dot")
        fig.update_layout(height=500, template="plotly_dark",
                          plot_bgcolor="#000", paper_bgcolor="#000",
                          font=dict(color="#00ff41", size=11),
                          title="COMPOUNDING REALITIES (Stress-Tested)")
        st.plotly_chart(fig, use_container_width=True)

        # Stats
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg Final", f"${finals.mean():,.0f}")
        c2.metric("Median", f"${np.median(finals):,.0f}")
        c3.metric("Win Paths", f"{(finals>start_bal).mean()*100:.1f}%")
        c4.metric("Ruin Risk", f"{(finals<=5000).mean()*100:.2f}%")

        st.success("REALITY BREACHED — All limits tested")

st.markdown("<p style='text-align:center; color:#00ff41; font-size:0.9rem;'>"
            "There is no spoon. Only edge.</p>", unsafe_allow_html=True)
