import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Debit Put Diagonal – COMPOUNDING KELLY", layout="wide")
st.title("Debit Put Diagonal – True Compounding Kelly + Multi-Path")
st.markdown("#### Now with **real geometric compounding** — contracts grow with your account")

# ── INPUTS ─────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Strategy Edge")
    win_rate = st.slider("Win Rate (%)", 80.0, 99.9, 96.0, 0.1) / 100
    avg_winner_raw = st.number_input("Avg Winner BEFORE costs ($)", value=230, step=10)
    avg_loser_raw = st.number_input("Avg Loser BEFORE costs ($)", value=-1206, step=50)
    debit_per_spread = st.number_input("Debit Cost per Spread ($)", value=1400, step=50)
    commission_per_contract = st.number_input("Commission round-trip ($)", value=1.30, step=0.10)
    slippage_buffer = st.number_input("Slippage/Assignment Buffer ($ per loser)", value=80, step=10)
    starting_balance = st.number_input("Starting Balance ($)", value=100000, step=10000)

with col2:
    st.subheader("Simulation")
    num_trades = st.slider("Number of Trades", 100, 5000, 1200, step=100)
    num_paths = st.slider("Monte Carlo Paths", 10, 1000, 300, step=50)
    max_contract_cap = st.number_input("Max Contracts per Trade (optional cap)", min_value=1, value=1000, step=50)
    seed = st.checkbox("Fix random seed", value=True)

if seed:
    np.random.seed(42)

# Net P&L after all costs
net_winner = avg_winner_raw - 2 * commission_per_contract
net_loser = avg_loser_raw - 2 * commission_per_contract - slippage_buffer

# Kelly fraction (same every time — edge doesn't change)
p, q = win_rate, 1 - win_rate
b = abs(net_winner) / debit_per_spread
kelly_f = (p * b - q) / b if b > 0 else 0
kelly_f = max(0, min(kelly_f, 0.5))  # cap at 50% for sanity

st.sidebar.success(f"**True Kelly f = {kelly_f:.1%}** (recalculated every trade)")
st.sidebar.caption(f"Debit per spread: ${debit_per_spread:,} | Net winner: ${net_winner:.0f} | Net loser: ${net_loser:.0f}")

# ── RUN COMPOUNDING SIMULATION ────────────────────────────────
if st.button("Run Compounding Kelly Monte Carlo", type="primary"):
    with st.spinner(f"Simulating {num_paths:,} compounding paths..."):
        all_equity = []

        for _ in range(num_paths):
            balance = starting_balance
            equity_path = [balance]

            for _ in range(num_trades):
                # ← RECALCULATE Kelly size based on CURRENT balance
                contracts_raw = int((kelly_f * balance) / debit_per_spread)
                contracts = min(contracts_raw, max_contract_cap)
                contracts = max(1, contracts)  # never go to 0

                # Random outcome
                won = np.random.random() < win_rate
                pnl = (net_winner if won else net_loser) * contracts

                balance += pnl
                balance = max(balance, 0)  # no negative balance
                equity_path.append(balance)

            all_equity.append(equity_path)

        all_equity = np.array(all_equity)
        final_balances = all_equity[:, -1]
        mean_path = np.mean(all_equity, axis=0)

        # ── PLOT: COMPOUNDING CURVES ─────────────────────────────
        fig = go.Figure()

        # Faint paths
        for path in all_equity:
            fig.add_trace(go.Scatter(y=path, mode='lines',
                                     line=dict(width=1, color='rgba(0,255,136,0.08)'),
                                     showlegend=False, hoverinfo='skip'))

        # BRIGHT WHITE MEAN PATH
        fig.add_trace(go.Scatter(y=mean_path, mode='lines', name='MEAN COMPOUNDING PATH',
                                 line=dict(color='white', width=5)))

        fig.add_hline(y=starting_balance, line_color="gray", line_dash="dash")
        fig.update_layout(
            title=f"{num_paths:,} Compounding Paths | Kelly f={kelly_f:.1%} | Max {max_contract_cap:,} contracts",
            xaxis_title="Trade #", yaxis_title="Account Balance ($)",
            template="plotly_dark", height=520, hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── STATS ───────────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg Final Balance", f"${final_balances.mean():,.0f}")
        c2.metric("Median Final", f"${np.median(final_balances):,.0f}")
        c3.metric("Profitable Paths", f"{(final_balances > starting_balance).mean()*100:.1f}%")
        c4.metric("Ruin Risk", f"{(final_balances <= 1000).mean()*100:.2f}%")

        # Distribution
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(x=final_balances, nbinsx=70, marker_color='#00ccff'))
        fig2.add_vline(x=starting_balance, line_color="white", line_dash="dash")
        fig2.update_layout(title="Final Balance Distribution (Compounding Kelly)", height=380,
                           template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)

        st.success(f"""
        **TRUE COMPOUNDING KELLY COMPLETE**  
        Started: ${starting_balance:,} → Average final: **${final_balances.mean():,.0f}**  
        Geometric growth activated. This is how legends are built.
        """)
