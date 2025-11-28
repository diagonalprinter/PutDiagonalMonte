import streamlit as st
import numpy as np
import plotly.graph_objects as go

# ── MATRIX THEME ─────────────────────────────────────
st.set_page_config(page_title="MATRIX DIAGONAL", layout="wide")
st.markdown(
    """
    <style>
    .css-1d391kg {padding-top: 1rem; padding-bottom: 2rem;}
    .css-1v0mbdj {font-size: 0.9rem !important;}
    .css-1cpxl2t {font-size: 1.4rem !important; color: #00ff41;}
    .stPlotlyChart {margin: 0.5rem 0;}
    h1, h2, h3 {color: #00ff41 !important; font-family: 'Courier New', monospace;}
    .stButton>button {background: #001100; color: #00ff41; border: 1px solid #00ff41;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("┌── MATRIX : DEBIT PUT DIAGONAL v9")
st.markdown("##### True compounding Kelly • Real-world stress tests • Black swans enabled")

# ── INPUTS (compact & clean) ─────────────────────────────
c1, c2 = st.columns([1, 1])

with c1:
    st.subheader("Edge Parameters")
    win_rate = st.slider("Win Rate (%)", 80.0, 99.9, 96.0, 0.1, help="Historical win rate") / 100
    avg_winner_raw = st.number_input("Avg Winner (gross $)", 230, step=10)
    avg_loser_raw = st.number_input("Avg Loser (gross $)", -1206, step=50)
    debit_per_spread = st.number_input("Debit per Spread ($)", 1400, step=50)
    commission = st.number_input("Commission round-trip ($)", 1.30, step=0.10)
    slippage_buffer = st.number_input("Slippage/Assignment Buffer ($)", 80, step=10)
    starting_balance = st.number_input("Starting Balance ($)", 100000, step=10000)

with c2:
    st.subheader("Simulation & Reality Checks")
    num_trades = st.slider("Number of Trades", 100, 5000, 1200, step=100)
    num_paths = st.slider("Monte Carlo Paths", 10, 1000, 300, step=50)
    max_contract_cap = st.number_input("Max Contracts per Trade", 1, 200, 10, step=5)
    lose_streaks = st.checkbox("Losing-streak clustering", True)
    black_swans = st.checkbox("1-in-500 black-swan loser (-4×)", True)
    bpr = st.slider("Buying Power Reduction %", 20, 80, 50)/100
    seed = st.checkbox("Fixed seed", True)

if seed:
    np.random.seed(42)

# ── NET EDGE & KELLY ─────────────────────────────────────
net_win = avg_winner_raw - 2*commission
net_loss = avg_loser_raw - 2*commission - slippage_buffer
p, q = win_rate, 1-win_rate
b = abs(net_win) / debit_per_spread
kelly_f = max(0, min((p*b - q)/b, 0.5))

st.sidebar.markdown(f"**KELLY f = {kelly_f:.1%}**")
st.sidebar.markdown(f"**Net win ${net_win:.0f} | Net loss ${net_loss:.0f}**")

# ── RUN SIMULATION ───────────────────────────────────────
if st.button(">> EXECUTE SIMULATION", type="primary"):
    with st.spinner("Running matrix simulation..."):
        all_equity = []

        for _ in range(num_paths):
            balance = starting_balance
            path = [balance]
            streak = 0

            for _ in range(num_trades):
                usable = balance * (1 - bpr)
                contracts = min(max(1, int(kelly_f * usable / debit_per_spread)), max_contract_cap)

                # Real-world win probability
                prob = win_rate * (0.6 if lose_streaks and streak > 0 else 1.0)

                won = np.random.random() < prob

                # Black swan
                if black_swans and np.random.random() < 1/500:
                    pnl = net_loss * 4 * contracts
                else:
                    pnl = (net_win if won else net_loss) * contracts

                if not won:
                    streak = np.random.choice([0,1,2,3,4], p=[0.6,0.2,0.1,0.06,0.04])

                balance = max(balance + pnl, 1000)
                path.append(balance)

            all_equity.append(path)

        all_equity = np.array(all_equity)
        mean_path = np.mean(all_equity, axis=0)
        finals = all_equity[:, -1]

        # ── MATRIX GRAPH ─────────────────────────────────────
        fig = go.Figure()
        for path in all_equity:
            fig.add_trace(go.Scatter(y=path, mode='lines',
                                     line=dict(width=1, color='rgba(0,255,65,0.07)'),
                                     showlegend=False, hoverinfo='skip'))

        fig.add_trace(go.Scatter(y=mean_path, mode='lines', name='MEAN PATH',
                                 line=dict(color='#00ff41', width=5)))

        fig.add_hline(y=starting_balance, line_color="#003300", line_dash="dash")
        fig.update_layout(
            title="COMPOUNDING EQUITY PATHS (Real-World Mode)",
            xaxis_title="Trade", yaxis_title="Balance ($)",
            template="plotly_dark", height=480,
            plot_bgcolor="#000000", paper_bgcolor="#000000",
            font=dict(color="#00ff41", size=11)
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── STATS ───────────────────────────────────────────
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Avg Final", f"${finals.mean():,.0f}")
        col2.metric("Median Final", f"${np.median(finals):,.0f}")
        col3.metric("Profitable Paths", f"{(finals>starting_balance).mean()*100:.1f}%")
        col4.metric("Ruin Risk", f"{(finals<=5000).mean()*100:.2f}%")

        # Distribution
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(x=finals, nbinsx=70, marker_color='#00ff41'))
        fig2.add_vline(x=starting_balance, line_color="#003300", line_dash="dash")
        fig2.update_layout(title="Final Balance Distribution", height=340,
                           template="plotly_dark", plot_bgcolor="#000000",
                           paper_bgcolor="#000000", font=dict(color="#00ff41", size=11))
        st.plotly_chart(fig2, use_container_width=True)

        st.success("SIMULATION COMPLETE – Reality checks applied")

st.markdown("##### © 2025 – Built in the Matrix with Grok")
