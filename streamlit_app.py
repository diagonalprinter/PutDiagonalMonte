import streamlit as st
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="SPX Diagonal Engine v6.9.20 — TROPHY EDITION", layout="wide")

# === STYLE ===
st.markdown("""
<style>
    .header-card {
        background:#1e293b; border:1px solid #334155; border-radius:12px; padding:12px; 
        text-align:center; height:140px; display:flex; flex-direction:column; justify-content:center;
    }
    .big {font-size:36px; font-weight:700; margin:4px 0; color:white;}
    .small {font-size:13px; color:#94a3b8; margin:0;}
    .nuclear {background:#7f1d1d !important; animation: pulse 2s infinite;}
    @keyframes pulse {0% {opacity:1} 50% {opacity:0.7} 100% {opacity:1}}
</style>
""", unsafe_allow_html=True)

# === 1. LIVE + FORWARD 9D/30D CURVE ===
@st.cache_data(ttl=60)
def get_vol_data():
    try:
        # Spot values
        vix9d = yf.Ticker("^VIX9D").info.get('regularMarketPrice', 18.4)
        vix30d = yf.Ticker("^VIX").info.get('regularMarketPrice', 18.1)
        spot_ratio = round(vix9d / vix30d, 3) if vix30d > 0 else 1.018

        # VIX Futures for forward ratio (front month vs next)
        vix_tickers = ["^VIX", "VXZ25", "VXF26", "VXH26", "VXM26", "VXN26"]
        data = yf.download(vix_tickers, period="5d", progress=False)['Close'].iloc[-1]
        front = data.get('^VIX', data.dropna().iloc[0])
        second = data.dropna().iloc[1] if len(data.dropna()) > 1 else front
        forward_ratio = round(front / second, 3) if second > 0 else spot_ratio

        spx = yf.Ticker("^GSPC").info.get('regularMarketPrice', 6000.0)
        return spot_ratio, forward_ratio, vix9d, vix30d, round(spx, 1)
    except:
        return 1.018, 1.012, 18.4, 18.1, 6000.0

spot_ratio, forward_ratio, vix9d, vix30d, spx_price = get_vol_data()
now_str = datetime.now().strftime("%H:%M:%S ET")

# === 2. DYNAMIC REALIZED TABLE (Your Personal Truth) ===
default_table = pd.DataFrame({
    "ratio_range": ["≥1.30", "1.20-1.299", "1.12-1.199", "1.04-1.119", "1.00-1.039", "0.96-0.999", "0.92-0.959", "0.88-0.919", "≤0.879"],
    "debit": [750, 850, 950, 1050, 1250, 1400, 1600, 1850, 2400],
    "realized_winner": [330, 315, 305, 275, 255, 240, 225, 200, 140],
    "effective_winner": [228, 225, 224, 220, 210, 200, 195, 180, 110],
    "realized_edge": [0.38, 0.35, 0.32, 0.26, 0.21, 0.17, 0.14, 0.11, 0.06],
    "shrink": [2, 4, 6, 10, 14, 18, 22, 30, 55]
})

if "user_table" not in st.session_state:
    st.session_state.user_table = default_table.copy()

with st.expander("Dynamic Realized Performance Table — YOUR TRUTH (Edit & Own It)", expanded=True):
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("Reset to Original", use_container_width=True):
            st.session_state.user_table = default_table.copy()
            st.success("Reset complete!")
    with col1:
        edited_table = st.data_editor(
            st.session_state.user_table,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "ratio_range": st.column_config.TextColumn("9D/30D Range"),
                "debit": st.column_config.NumberColumn("Avg Debit $", format="$%.0f"),
                "realized_winner": st.column_config.NumberColumn("Realized $", format="$%.0f"),
                "effective_winner": st.column_config.NumberColumn("Model Winner $", format="$%.0f"),
                "realized_edge": st.column_config.NumberColumn("Realized Edge", format="%.3f×"),
                "shrink": st.column_config.NumberColumn("Shrink %", format="%d%%")
            },
            hide_index=False
        )
    st.session_state.user_table = edited_table

# Find current shrink from your live ratio
def get_current_shrink(ratio, table):
    for _, row in table.iterrows():
        rng = row['ratio_range']
        if '≥' in rng and ratio >= float(rng.replace('≥', '')):
            return row['shrink']
        if '≤' in rng and ratio <= float(rng.replace('≤', '')):
            return row['shrink']
        if '-' in rng:
            low, high = map(float, rng.split('-'))
            if low <= ratio <= high:
                return row['shrink']
    return 12  # fallback

shrink_pct = get_current_shrink(spot_ratio, edited_table)

# === REGIME + NUCLEAR ALERT ===
def get_regime(r):
    if r >= 1.30: return {"zone":"NUCLEAR",     "color":"#dc2626", "size":"3.0×", "alert":True}
    if r >= 1.20: return {"zone":"INSANE",      "color":"#7c3aed", "size":"2.5×", "alert":True}
    if r >= 1.12: return {"zone":"GOD ZONE",    "color":"#8b5cf6", "size":"2.0×", "alert":True}
    if r >= 1.04: return {"zone":"GOLDEN",      "color":"#3b82f6", "size":"1.8×", "alert":False}
    if r >= 1.00: return {"zone":"OPTIMAL",     "color":"#10b981", "size":"1.5×", "alert":False}
    if r >= 0.94: return {"zone":"NORMAL",      "color":"#84cc16", "size":"1.0×", "alert":False}
    if r >= 0.88: return {"zone":"MARGINAL",    "color":"#f59e0b", "size":"0.5×", "alert":False}
    return                {"zone":"RATIO MODE",  "color":"#ef4444", "size":"0×",   "alert":False}

regime = get_regime(spot_ratio)
forward_regime = get_regime(forward_ratio)

# === HEADER ===
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f'<div class="header-card"><p class="small">Spot 9D/30D</p><p class="big">{spot_ratio}</p></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="header-card"><p class="small">Forward 9D/30D</p><p class="big">{forward_ratio}</p></div>', unsafe_allow_html=True)
with c3:
    alert_class = 'nuclear' if regime["alert"] else ''
    st.markdown(f'<div class="header-card {alert_class}"><p class="small">Regime</p><p class="big">{regime["zone"]}</p><p class="small">SIZE: {regime["size"]}</p></div>', unsafe_allow_html=True)
with c4:
    if regime["alert"]:
        st.error("NUCLEAR ALERT — MAX SIZE DIAGONALS NOW")
    elif forward_ratio > spot_ratio + 0.05:
        st.success("Forward curve rising → GET READY")
    elif forward_ratio < spot_ratio - 0.05:
        st.warning("Forward curve falling → prepare for ratio mode")
    else:
        st.info("Normal regime")
with c5:
    st.markdown(f'<div class="header-card"><p class="small">SPX Live</p><p class="big">{spx_price:,.0f}</p><p class="small">{now_str}</p></div>', unsafe_allow_html=True)

st.markdown("---")

# === INPUTS & CALCULATIONS ===
left, right = st.columns(2)
with left:
    st.subheader("Strategy Parameters")
    user_debit = st.number_input("Current Debit ($)", 100, 5000, 1350, 10)
    win_rate = st.slider("Win Rate (%)", 80.0, 99.9, 96.0, 0.1) / 100
    base_winner = st.number_input("Theoretical Winner ($)", value=230, step=5)
    avg_loser = st.number_input("Average Loser ($)", value=-1206, step=25)
    commission = st.number_input("Commission RT ($)", value=1.3, step=0.1)
with right:
    st.subheader("Simulation Controls")
    start_bal = st.number_input("Starting Capital ($)", value=100000, step=25000)
    max_contracts = st.number_input("Max Contracts", value=10, min_value=1)
    num_trades = st.slider("Total Trades", 10, 3000, 150, 10)
    num_paths = st.slider("Monte Carlo Paths", 50, 1000, 300, 25)

net_win = base_winner - 2 * commission
net_loss = avg_loser - 2 * commission - 80
effective_winner = net_win * (1 - shrink_pct/100)
edge = effective_winner / user_debit if user_debit > 0 else 0
raw_kelly = (win_rate * edge - (1-win_rate)) / edge if edge > 0 else 0
kelly_f = max(0.0, min(0.25, raw_kelly))

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Debit", f"${user_debit:,}")
m2.metric("Effective Winner", f"${effective_winner:+.0f}")
m3.metric("Edge/$", f"{edge:.3f}×")
m4.metric("Kelly Fraction", f"{kelly_f:.1%}")
m5.metric("Shrink Applied", f"{shrink_pct}%")

# === MONTE CARLO ===
if st.button("RUN SIMULATION", use_container_width=True):
    if num_trades < 1:
        st.warning("Set Total Trades ≥ 1")
    else:
        with st.spinner(f"Running {num_paths:,} paths × {num_trades:,} trades..."):
            finals, paths = [], []
            for _ in range(num_paths):
                bal = start_bal
                path = [bal]
                streak = 0
                for _ in range(num_trades):
                    contracts = min(max_contracts, max(1, int(kelly_f * bal * 0.5 / user_debit)))
                    p_win = win_rate if streak == 0 else win_rate * 0.60
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
            years = num_trades / 150.0
            cagr = (finals / start_bal) ** (1/years) - 1 if years > 0 else 0

            col1, col2 = st.columns([2.5, 1])
            with col1:
                fig = go.Figure()
                for p in paths[:100]:
                    fig.add_trace(go.Scatter(y=p, mode='lines', line=dict(width=1, color="rgba(100,116,139,0.2)"), showlegend=False))
                fig.add_trace(go.Scatter(y=mean_path, mode='lines', line=dict(color='#60a5fa', width=5), name='Mean Path'))
                fig.add_hline(y=start_bal, line_color="#e11d48", line_dash="dash", annotation_text="Starting Capital")
                fig.update_layout(template="plotly_dark", height=560, title="Monte Carlo Equity Curves")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.metric("Median Final", f"${np.median(finals)/1e6:.2f}M")
                st.metric("95th Percentile", f"${np.percentile(finals,95)/1e6:.2f}M")
                st.metric("Mean CAGR", f"{np.mean(cagr):.1%}")
                st.metric("Ruin Rate (<$10k)", f"{(finals<10000).mean():.2%}")

st.caption("SPX Diagonal Engine v6.9.20 — TROPHY EDITION • Forward Curve • Dynamic Truth • Nuclear Alert • Dec 2025")
