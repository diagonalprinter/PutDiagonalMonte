import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time

# ── 2-SECOND MATRIX RAIN INTRO ───────────────────────
placeholder = st.empty()
with placeholder.container():
    st.markdown("""
    <style>
    @keyframes rain {
      0% { transform: translateY(-100vh); }
      100% { transform: translateY(100vh); }
    }
    .rain-char { 
      color: #00ff41; 
      font-family: 'Courier New'; 
      font-size: 18px; 
      position: absolute; 
      animation: rain 8s linear infinite;
      opacity: 0.8;
    }
    </style>
    <div style="background:#000; height:100vh; overflow:hidden; position:relative;">
    <h1 style="color:#00ff41; text-align:center; padding-top:20vh; font-family:'Courier New';">
      ACCESSING SECURE SYSTEM...<br><br>
      <span style="font-size:2rem;">DEBIT PUT DIAGONAL v13</span>
    </h1>
    """ + "".join([f"<div class='rain-char' style='left:{i*3}%; animation-delay:{j}s;'>{chr(65+np.random.randint(26))}</div>" 
                   for i in range(40) for j in [np.random.random()*3]]) + "</div>", 
    unsafe_allow_html=True)
    time.sleep(2.2)
placeholder.empty()

# ── RETRO DOS THEME ───────────────────────────────────
st.markdown("""
<style>
    .css-2trqyj {background:#000 !important;}
    .stApp {background:#000; color:#00ff41; font-family:'Lucida Console', 'Courier New', monospace;}
    h1, h2, h3 {color:#00ff41 !important; text-align:center;}
    .stButton>button {background:#000; color:#00ff41; border:2px solid #ff0000; font-weight:bold;}
    .stTextInput>div>div>input, .stNumberInput>div>div>input {background:#000; color:#00ff41; border:2px solid #00ff41;}
    .stSlider > div > div > div > div {background:#003300;}
    .red-border {border: 3px solid #ff0000; padding: 10px; margin: 10px 0; background:#001100;}
    .section-title {color:#00ff41; font-size:1.4rem; border-bottom:2px solid #ff0000; padding-bottom:5px;}
</style>
""", unsafe_allow_html=True)

st.title("DEBIT PUT DIAGONAL v13")
st.markdown("<h3 style='text-align:center; color:#00ff41;'>COMPOUNDING KELLY • BLACK SWAN ENGINE • 1987 EDITION</h3>", unsafe_allow_html=True)

# ── TWO COLUMN LAYOUT (narrow & clean) ───────────────
col1, col2 = st.columns(2)

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

    # Black Swan
    swan = st.checkbox("Black Swan Events", True)
    if swan:
        swan_freq = st.number_input("Frequency (1 in X)", 100, 2000, 500)
        swan_mag = st.number_input("Magnitude (× loser)", 2.0, 20.0, 6.0, 0.5)

    # Loss Clustering
    cluster = st.checkbox("Losing Streak Clustering", True)
    if cluster:
        cluster_mult = st.slider("Win rate multiplier in streak", 0.2, 0.9, 0.6, 0.05)
        max_streak = st.number_input("Max streak length", 1, 12, 5)

    st.markdown("</div>", unsafe_allow_html=True)

# ── CALCULATIONS ─────────────────────────────────────
net_win = avg_winner - 2*commission
net_loss = avg_loser - 2*commission - slippage
p = win_rate
b = abs(net_win)/debit if debit > 0 else 0
kelly_f = max(0, min((p*b - (1-p))/b if b>0 else 0, 0.5))

st.sidebar.markdown(f"**KELLY f = {kelly_f:.1%}**")
st.sidebar.markdown(f"**Net Win ${net_win:.0f} | Net Loss ${net_loss:.0f}**")

# ── RUN ─────────────────────────────────────────────
if st.button("EXECUTE SIMULATION", type="primary"):
    with st.spinner("LOADING..."):
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

                bal = max(bal + pnl, 1000)
                path.append(bal)
                if cluster and streak > 0: streak -= 1

            paths.append(path)

        paths = np.array(paths)
        mean = np.mean(paths, axis=0)
        finals = paths[:, -1]

        # Main Graph
        fig = go.Figure()
        for p in paths:
            fig.add_trace(go.Scatter(y=p, mode='lines', line=dict(width=1, color='rgba(0,255,65,0.06)'), showlegend=False, hoverinfo='skip'))
        fig.add_trace(go.Scatter(y=mean, mode='lines', name='MEAN', line=dict(color='#00ff41', width=6)))
        fig.add_hline(y=start_bal, line_color="#ff0000", line_dash="dot")
        fig.update_layout(height=500, template="plotly_dark", plot_bgcolor="#000", paper_bgcolor="#000",
                          font=dict(color="#00ff41", size=11), title="COMPOUNDING PATHS")
        st.plotly_chart(fig, use_container_width=True)

        # Distribution (BACK!)
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(x=finals, nbinsx=70, marker_color='#00ff41'))
        fig2.add_vline(x=start_bal, line_color="#ff0000")
        fig2.update_layout(height=380, template="plotly_dark", plot_bgcolor="#000", paper_bgcolor="#000",
                           font=dict(color="#00ff41", size=11), title="FINAL BALANCE DISTRIBUTION")
        st.plotly_chart(fig2, use_container_width=True)

        # Stats
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("AVG FINAL", f"${finals.mean():,.0f}")
        c2.metric("MEDIAN", f"${np.median(finals):,.0f}")
        c3.metric("WIN PATHS", f"{(finals>start_bal).mean()*100:.1f}%")
        c4.metric("RUIN", f"{(finals<=5000).mean()*100:.2f}%")

st.markdown("<p style='text-align:center; color:#ff0000; font-size:0.9rem; margin-top:30px;'>"
            "NO SPOON • ONLY EDGE • 1987-2025</p>", unsafe_allow_html=True)
