import streamlit as st
import numpy as np
import plotly.graph_objects as go
import yfinance as yf  # Requires requirements.txt entry
from datetime import datetime, timedelta

st.set_page_config(page_title="SPX Diagonal Engine v6.6", layout="wide")

# === LIVE DEBIT CALC ===
@st.cache_data(ttl=30)
def get_live_debit():
    try:
        spx = yf.Ticker("^GSPC")
        current_spx = spx.history(period="1d")['Close'].iloc[-1]
        
        # Find ~8DTE and ~16DTE expirations
        today = datetime.now()
        exp8 = today + timedelta(days=8)
        exp16 = today + timedelta(days=16)
        opts = spx.options
        
        exp8_str = min(opts, key=lambda x: abs(datetime.strptime(x, '%Y-%m-%d') - exp8))
        exp16_str = min(opts, key=lambda x: abs(datetime.strptime(x, '%Y-%m-%d') - exp16))
        
        # Get puts chains
        puts8 = spx.option_chain(exp8_str).puts
        puts16 = spx.option_chain(exp16_str).puts
        
        # Your exact strikes: short 0.25% OTM, long 20 wide
        short_strike = current_spx * (1 - 0.0025)
        long_strike = short_strike - 20
        
        # Closest puts (last price for reliability)
        short_row = puts8.iloc[(puts8['strike'] - short_strike).abs().argsort()[:1]]
        long_row = puts16.iloc[(puts16['strike'] - long_strike).abs().argsort()[:1]]
        
        short_premium = short_row['lastPrice'].values[0]
        long_premium = long_row['lastPrice'].values[0]
        debit_per_share = max(0.50, short_premium - long_premium)
        debit = debit_per_share * 100  # SPX multiplier
        
        return {
            "current_spx": current_spx,
            "short_strike": round(short_strike),
            "long_strike": round(long_strike),
            "short_premium": short_premium,
            "long_premium": long_premium,
            "debit": debit
        }
    except Exception as e:
        st.error(f"Live data error: {e}. Using fallback.")
        return {
            "current_spx": 6000,
            "short_strike": 5985,
            "long_strike": 5965,
            "short_premium": 12.5,
            "long_premium": 11.2,
            "debit": 130.0  # $1.30 per share × 100 = $130
        }

live_data = get_live_debit()

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

# === HEADER ===
st.markdown(f"<h1 style='text-align:center; color:#e2e8f0; margin:40px 0;'>SPX Debit Put Diagonal v6.6 — LIVE DEBIT</h1>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    st.metric("SPX Price", f"${live_data['current_spx']:.0f}")
with col2:
    st.markdown(f"<h2 style='text-align:center; color:#e2e8f0;'>{live_data['debit']:.0f} DEBIT</h2>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<h2 style='text-align:center; color:#e2e8f0;'>Short: {live_data['short_strike']}P | Long: {live_data['long_strike']}P</h2>", unsafe_allow_html=True)

# === INPUTS ===
c1, c2 = st.columns([1,1])
with c1:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.subheader("Strategy Parameters")
    win_rate = st.slider("Win Rate (%)", 0.0, 100.0, 96.0, 0.1) / 100
    base_winner = st.number_input("Theoretical Winner ($)", value=230, step=5)
    avg_loser = st.number_input("Average Loser ($)", value=-1206, step=25)
    commission = st.number_input("Commission RT ($)", value=1.3, step=0.1)
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.subheader("Simulation Controls")
    start_bal = st.number_input("Starting Capital ($)", value=100000, step=25000)
    max_contracts = st.number_input("Max Contracts per Trade", value=10, min_value=1)
    num_trades = st.slider("Total Trades in Simulation", 0, 3000, 150, 10)
    num_paths = st.slider("Monte Carlo Paths", 50, 1000, 300, 25)
    st.markdown("</div>", unsafe_allow_html=True)

# === CALCULATIONS (using live debit) ===
debit = live_data['debit']
net_win = base_winner - 2 * commission
net_loss = avg_loser - 2 * commission - 80
effective_winner = net_win * 0.88  # Default shrinkage — adjust based on live data if needed
edge_per_dollar = effective_winner / debit
raw_kelly = (win_rate * edge_per_dollar - (1 - win_rate)) / edge_per_dollar if edge_per_dollar > 0 else 0
kelly_f = max(0.0, min(0.25, raw_kelly))
expected_growth = kelly_f * (win_rate * effective_winner + (1 - win_rate) * net_loss) / debit
theoretical_cagr = (1 + expected_growth) ** 250 - 1

# === METRICS ===
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Live Debit", f"${debit:,.0f}")
m2.metric("Effective Winner", f"${effective_winner:+.0f}")
m3.metric("Edge/$", f"{edge_per_dollar:.3f}×")
m4.metric("Kelly Fraction", f"{kelly_f:.1%}")
m5.metric("Theoretical CAGR", f"{theoretical_cagr:.1%}")
m6.metric("Regime", "LIVE")

# === SIMULATION ===
if st.button("RUN SIMULATION"):
    if num_trades == 0:
        st.info("Set number of trades > 0 to run simulation.")
    else:
        with st.spinner(f"Running {num_paths} paths over {num_trades} trades..."):
            finals = []
            paths = []
            for _ in range(num_paths):
                bal = start_bal
                path = [bal]
                streak = 0
                for _ in range(num_trades):
                    contracts = min(max_contracts, max(1, int(kelly_f * bal * 0.5 / debit)))
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
                st.metric("Median Terminal Wealth", f"${np.median(finals)/1e6:.2f}M")
                st.metric("95th Percentile", f"${np.percentile(finals,95)/1e6:.2f}M")
                st.metric("Mean CAGR", f"{np.mean(sim_cagr):.1%}")
                st.metric("Ruin Probability", f"{(finals<10_000).mean():.2%}")

st.markdown("<p style='text-align:center;color:#475569;margin-top:100px;font-size:14px;'>SPX Debit Put Diagonal Engine v6.6 — Live Debit • 2025</p>", unsafe_allow_html=True)
