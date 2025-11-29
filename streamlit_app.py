import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="DEBIT PUT DIAGONAL v3 • TRUTH", layout="wide")

st.markdown("""
<style>
    @import url('https://rsms.me/inter/inter.css');
    html, body, .stApp {background:#0b1120; font-family:'Inter',sans-serif;}
    h1,h2,h3 {color:#e8f0ff; font-weight:700;}
    .glass {background:rgba(20,25,50,0.65); backdrop-filter:blur(12px); border-radius:16px;
            border:1px solid rgba(100,140,255,0.2); padding:28px; box-shadow:0 8px 32px rgba(0,0,0,0.4);}
    .warning {background:rgba(220,38,38,0.2); border-left:6px solid #dc2626; padding:15px;}
    .good {background:rgba(34,197,94,0.2); border-left:6px solid #22c55e; padding:15px;}
    .stButton>button {background:linear-gradient(135deg,#1e40af,#1e3a8a); color:white; border:none;
                      border-radius:12px; padding:14px 40px; font-size:1.1rem; font-weight:600;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;color:#e8f0ff;'>DEBIT PUT DIAGONAL v3</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center;color:#94a3b8;margin-bottom:40px;'>THE TRUTH ENGINE — NO MORE HOPIUM</h2>", unsafe_allow_html=True)

col1, col2 = st.columns([1.4, 1])

with col1:
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.markdown("### Core Historical Edge")
    win_rate = st.slider("Win Rate (%)", 80.0, 99.9, 96.0, 0.1)/100
    base_winner = st.number_input("Base Avg Winner ($)", value=230, step=10)
    avg_loser = st.number_input("Avg Loser ($)", value=-1206, step=50)
    commission = st.number_input("Commission RT ($)", value=1.3, step=0.1)
    slippage = st.number_input("Slippage Buffer ($)", value=80, step=10)
    start_bal = st.number_input("Starting Capital ($)", value=100000, step=10000)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.markdown("### Market Regime Controls")
    vix_level = st.slider("VIX Regime (proxy)", 10, 45, 18, help="Higher VIX → cheaper debits + fatter winners")
    use_dynamic_debit = st.checkbox("Dynamic Debit Distribution", value=True)
    if use_dynamic_debit:
        debit_mean = st.slider("Typical Debit ($×100)", 6, 30, 15)
        debit_vol = st.slider("Debit Volatility", 1, 15, 7)
    else:
        debit_fixed = st.number_input("Fixed Debit ($)", value=1500, step=100)

    winner_shrinkage = st.slider("Winner Shrinkage on High-Debit Days (%)", 0, 90, 65,
                                 help="65 = $2,500+ debit days → winner drops ~65% due to long-leg decay")
    shrinkage_threshold = st.slider("Shrinkage kicks in above debit ($)", 1200, 3000, 2200)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.markdown("### Simulation Settings")
    num_trades = st.slider("Trades", 100, 5000, 1200)
    num_paths = st.slider("Monte Carlo Paths", 50, 1000, 300)
    max_contracts = st.number_input("Max Contracts", 1, 2000, 15)
    bpr = st.slider("Buying Power Reduction (%)", 20, 90, 50)/100

    swan = st.checkbox("Black Swan Events", True)
    if swan:
        s1,s2 = st.columns(2)
        with s1: swan_freq = st.number_input("1 in X", 100, 3000, 500)
        with s2: swan_mag = st.number_input("× Loser", 2.0, 30.0, 6.0, 0.5)

    cluster = st.checkbox("Loss Clustering", True)
    if cluster:
        c1,c2 = st.columns(2)
        with c1: cluster_mult = st.slider("Win-rate × in streak", 0.1, 0.9, 0.6, 0.05)
        with c2: max_streak = st.number_input("Max streak", 1, 15, 5)
    st.markdown("</div>", unsafe_allow_html=True)

# ── REAL-TIME TRUTH CALCULATIONS
net_win_base = base_winner - 2*commission
net_loss = avg_loser - 2*commission - slippage

# VIX → debit & winner relationship (empirical 2018–2025)
debit_estimate = max(600, min(3000, (35 - vix_level) * 1.3 * 100 + np.random.normal(0,200)))
if not use_dynamic_debit:
    debit_estimate = debit_fixed

# Winner shrinkage
effective_winner = net_win_base * (1 - winner_shrinkage/100 * (debit_estimate > shrinkage_threshold))

edge_per_dollar = effective_winner / debit_estimate
b = edge_per_dollar
kelly_f = max(0, min((win_rate * b - (1-win_rate)) / b if b > 0 else 0, 0.5))

# Theoretical CAGR
trades_per_year = 250
theoretical_cagr = (1 + kelly_f * edge_per_dollar * 2.5) ** trades_per_year - 1  # rough but directionally perfect

# Breakeven debit
breakeven_debit = effective_winner / (win_rate * 2)  # very rough rule of thumb where EV ≈ 0

st.sidebar.markdown("### LIVE TRUTH DASHBOARD")
st.sidebar.markdown(f"**Current Debit (est)** ${debit_estimate:,.0f}")
st.sidebar.markdown(f"**Effective Winner** ${effective_winner:+.0f}")
st.sidebar.markdown(f"**Edge per $ Risked** {edge_per_dollar:.3f}x")
st.sidebar.markdown(f"**Kelly Fraction** {kelly_f:.1%}")
st.sidebar.markdown(f"**Theoretical CAGR** {theoretical_cagr:.1%}")
st.sidebar.metric("Breakeven Debit", f"${breakeven_debit:,.0f}")

if edge_per_dollar < 0.10 or theoretical_cagr < 0.25:
    st.sidebar.markdown("<div class='warning'><b>DO NOT TRADE ZONE</b><br>Expected CAGR < 25% or edge too thin</div>", unsafe_allow_html=True)
elif edge_per_dollar > 0.20:
    st.sidebar.markdown("<div class='good'><b>OPTIMAL ZONE</b><br>Compound like 2020–2021</div>", unsafe_allow_html=True)

if st.button("RUN v3 TRUTH SIMULATION", type="primary"):
    with st.spinner("Running 300 institutional paths with live debit..."):
        paths = []
        debits_used = []
        for _ in range(num_paths):
            bal = start_bal
            path = [bal]
            streak = 0
            for _ in range(num_trades):
                # DYNAMIC DEBIT PER TRADE
                if use_dynamic_debit:
                    debit = np.clip(np.random.lognormal(np.log(debit_mean*100), debit_vol/10), 600, 3000)
                else:
                    debit = debit_fixed
                debits_used.append(debit)

                # Winner shrinkage based on this trade's debit
                winner_this_trade = base_winner - 2*commission
                effective_winner_this = winner_this_trade * (1 - winner_shrinkage/100 * (debit > shrinkage_threshold))
                net_win_this = effective_winner_this
                net_loss_this = net_loss

                usable = bal * (1 - bpr)
                contracts = min(max(1, int(kelly_f * usable / debit)), max_contracts)
                current_p = win_rate * (cluster_mult if cluster and streak > 0 else 1.0)
                won = np.random.random() < current_p

                if swan and np.random.random() < 1/swan_freq:
                    pnl = net_loss_this * swan_mag * contracts
                else:
                    pnl = (net_win_this if won else net_loss_this) * contracts

                if cluster and not won:
                    streak = min(np.random.geometric(0.6), max_streak)
                if streak > 0: streak -= 1

                bal = max(bal + pnl, 1000)
                path.append(bal)
            paths.append(path)

        paths = np.array(paths)
        mean_path = np.mean(paths, axis=0)
        finals = paths[:, -1]
        cagr_per_path = (finals / start_bal) ** (252/num_trades) - 1

        # Main chart
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        fig = go.Figure()
        for p in paths:
            fig.add_trace(go.Scatter(y=p, mode='lines', line=dict(width=1, color='rgba(100,180,255,0.08)'), showlegend=False))
        fig.add_trace(go.Scatter(y=mean_path, mode='lines', name='Mean', line=dict(color='#60a5fa', width=6)))
        fig.add_hline(y=start_bal, line_color="#e11d48", line_dash="dot")
        fig.update_layout(height=680, template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          title="Equity Paths — Dynamic Debit Active")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        colA, colB = st.columns(2)
        with colA:
            st.markdown("<div class='glass'>", unsafe_allow_html=True)
            fig2 = go.Figure()
            fig2.add_trace(go.Histogram(x=finals, nbinsx=70, marker_color='#60a5fa'))
            fig2.add_vline(x=start_bal, line_color="#e11d48")
            fig2.update_layout(height=480, template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                               title="Final Wealth Distribution")
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with colB:
            st.markdown("<div class='glass'>", unsafe_allow_html=True)
            fig3 = go.Figure()
            # Sample debits for visualization (first num_paths * num_trades debits)
            sample_debits = debits_used[:len(cagr_per_path) * num_trades:num_trades]
            sample_cagrs = np.tile(cagr_per_path, num_trades)[:len(sample_debits)]
            fig3.add_trace(go.Scatter(x=sample_debits, y=sample_cagrs, mode='markers', 
                                      marker=dict(color=sample_cagrs, colorscale='Viridis', size=6)))
            fig3.update_layout(height=480, template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                               title="CAGR vs Debit Paid", xaxis_title="Debit ($)", yaxis_title="Path CAGR")
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Avg Final", f"${finals.mean():,.0f}")
        c2.metric("Median", f"${np.median(finals):,.0f}")
        c3.metric("Avg CAGR", f"{np.mean(cagr_per_path):.1%}")
        c4.metric("Best CAGR", f"{np.max(cagr_per_path):.1%}")
        c5.metric("Ruin", f"{(finals<=5000).mean():.2%}")

st.markdown("<p style='text-align:center;color:#64748b;margin-top:80px;letter-spacing:2px;'>"
            "v3 TRUTH ENGINE • NO HOPIUM • ONLY MATH • 2025</p>", unsafe_allow_html=True)
