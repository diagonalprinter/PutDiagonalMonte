import streamlit as st
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="SPX Diagonal Engine v6.9.34 — FIXED VRP/SPX + SQUARE GRAPH", layout="wide")

# ================================
# STYLE
# ================================
st.markdown("""
<style>
    .header-card {background:#1e293b; border:1px solid #334155; border-radius:12px; padding:12px; 
                  text-align:center; height:135px; display:flex; flex-direction:column; justify-content:center;}
    .big {font-size:34px; font-weight:700; margin:4px 0; color:white;}
    .small {font-size:12px; color:#94a3b8; margin:0;}
    .nuclear {background:#7f1d1d !important; animation: pulse 1.5s infinite;}
    @keyframes pulse {0% {opacity:1} 50% {opacity:0.6} 100% {opacity:1}}
</style>
""", unsafe_allow_html=True)

# ================================
# LIVE + DAILY FORWARD + DUAL VRP (FIXED)
# ================================
@st.cache_data(ttl=60)
def get_data():
    try:
        # Implied
        vix9d = yf.Ticker("^VIX9D").info.get('regularMarketPrice', 18.4)
        vix = yf.Ticker("^VIX").info.get('regularMarketPrice', 18.1)
        spot_ratio = round(vix9d / vix, 3) if vix > 0 else 0.929

        # Forward (next month future)
        next_future = "VXZ25"  # ← UPDATE THIS ONE LINE EVERY MONTH (Jan 2026 = VXF26)
        fut_price = yf.Ticker(next_future).info.get('regularMarketPrice', vix * 1.02)
        forward_30d = round(vix / fut_price, 3)

        # Daily interpolation
        days = np.arange(0, 31)
        t = days / 30
        ratios = spot_ratio + (forward_30d - spot_ratio) * (3*t**2 - 2*t**3)
        labels = ["Today"] + [f"+{d}d" for d in range(1, 31)]

        # Realized Volatility (RV) — increased period to 90d for safety
        spx_hist = yf.download("^GSPC", period="90d", progress=False)['Close']
        returns = np.log(spx_hist / spx_hist.shift(1)).dropna()
        rv9d = np.std(returns[-9:]) * np.sqrt(252) * 100 if len(returns) >= 9 else np.nan
        rv30d = np.std(returns[-30:]) * np.sqrt(252) * 100 if len(returns) >= 30 else np.nan

        vrp_short = vix9d - rv9d if not np.isnan(rv9d) else np.nan
        vrp_long = vix - rv30d if not np.isnan(rv30d) else np.nan

        # SPX price — fallback to download if info fails
        try:
            spx = yf.Ticker("^GSPC").info.get('regularMarketPrice', np.nan)
        except:
            spx = np.nan
        if np.isnan(spx):
            spx_hist_day = yf.download("^GSPC", period="2d", progress=False)['Close']
            spx = spx_hist_day.iloc[-1] if not spx_hist_day.empty else 6000.0

        return spot_ratio, ratios.tolist(), labels, vrp_short, vrp_long, round(spx, 1)
    except:
        return 0.929, np.linspace(0.929, 0.935, 31).tolist(), ["Today"] + [f"+{d}d" for d in range(1, 31)], np.nan, np.nan, 6000.0

spot_ratio, daily_ratios, daily_labels, vrp_short, vrp_long, spx_price = get_data()
now_str = datetime.now().strftime("%b %d, %H:%M ET")

# ================================
# REGIME
# ================================
def get_regime(r):
    if r >= 1.12: return {"zone":"MAXIMUM",  "shrink":2,  "alert":True}
    if r >= 1.04: return {"zone":"ENHANCED", "shrink":5,  "alert":True}
    if r >= 0.94: return {"zone":"OPTIMAL",   "shrink":8,  "alert":False}
    if r >= 0.88: return {"zone":"ACCEPTABLE","shrink":12, "alert":False}
    if r >= 0.84: return {"zone":"MARGINAL",  "shrink":32, "alert":False}
    return                {"zone":"OFF",       "shrink":60, "alert":False}

regime = get_regime(spot_ratio)

# ================================
# HEADER + DAILY FORWARD + VRP METRICS (SAFE DISPLAY)
# ================================
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f'<div class="header-card"><p class="small">Spot 9D/30D</p><p class="big">{spot_ratio}</p></div>', unsafe_allow_html=True)
with c2:
    alert_class = 'nuclear' if regime["alert"] else ''
    st.markdown(f'<div class="header-card {alert_class}"><p class="small">Regime</p><p class="big">{regime["zone"]}</p></div>', unsafe_allow_html=True)
with c3:
    vrp_short_str = f"{vrp_short:+.1f}" if not np.isnan(vrp_short) else "N/A"
    st.markdown(f'<div class="header-card"><p class="small">Short VRP</p><p class="big">{vrp_short_str}</p><p class="small">VIX9D - 9d RV</p></div>', unsafe_allow_html=True)
with c4:
    vrp_long_str = f"{vrp_long:+.1f}" if not np.isnan(vrp_long) else "N/A"
    st.markdown(f'<div class="header-card"><p class="small">Long VRP</p><p class="big">{vrp_long_str}</p><p class="small">VIX - 30d RV</p></div>', unsafe_allow_html=True)
with c5:
    st.markdown(f'<div class="header-card"><p class="small">SPX Live</p><p class="big">{spx_price:,.0f}</p><p class="small">{now_str}</p></div>', unsafe_allow_html=True)

# Daily forward graph (more square, spaced ticks)
ymin, ymax = min(daily_ratios) - 0.03, max(daily_ratios) + 0.03
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=daily_labels, y=daily_ratios,
    mode='lines+markers',
    line=dict(color='#60a5fa', width=5),  # Slightly thinner line
    marker=dict(size=10),                 # Smaller markers
    hovertemplate='%{x}: %{y:.3f}<extra></extra>'
))
fig.add_hline(y=1.0, line_dash="dash", line_color="#e11d48", annotation_text="1.00")
fig.update_layout(
    title="Daily Forward 9D/30D Curve — Next 30 Days",
    height=420,  # Taller for more square shape
    margin=dict(l=40, r=40, t=60, b=40),
    paper_bgcolor="#1e293b", plot_bgcolor="#1e293b",
    font_color="#e2e8f0",
    yaxis=dict(range=[ymin, ymax], dtick=0.01, gridcolor="#334155"),
    xaxis=dict(
        tickangle=45,
        showgrid=False,
        tickmode='array',
        tickvals=daily_labels[::5],      # Every 5 days for spacing
        ticktext=daily_labels[::5]
    )
)
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ================================
# ALERTS (enhanced with VRP)
# ================================
if regime["alert"]:
    st.error("NUCLEAR ALERT — MAX SIZE DIAGONALS RIGHT NOW")
elif not np.isnan(vrp_short) and vrp_short > 8:
    st.success("High Short VRP — Strong crush expected on short leg")
elif not np.isnan(vrp_short) and vrp_short < 2:
    st.warning("Low Short VRP — Crush weak, consider skipping")
else:
    st.info("Normal VRP — Trade as usual")

st.markdown("---")

# ================================
# INPUTS & CALCULATIONS
# ================================
left, right = st.columns(2)
with left:
    st.subheader("Strategy Parameters")
    debit = st.number_input("Current Debit ($)", 100, 5000, 1350, 10)
    winrate_pct = st.slider("Win Rate (%)", 0, 100, 96, 1)
    winrate = winrate_pct / 100
    winner = st.number_input("Theoretical Winner ($)", value=230, step=5)
    loser = st.number_input("Average Loser ($)", value=-1206, step=25)
    comm = st.number_input("Commission RT ($)", value=1.3, step=0.1)
with right:
    st.subheader("Monte Carlo Simulation")
    start_bal = st.number_input("Starting Capital ($)", value=100000, step=25000)
    max_cont = st.number_input("Max Contracts", value=10, min_value=1)
    trades = st.slider("Total Trades", 10, 3000, 150, 10)
    paths = st.slider("Monte Carlo Paths", 50, 1000, 300, 25)

net_win = winner - 2 * comm
eff_winner = net_win * (1 - regime["shrink"]/100)
edge = eff_winner / debit if debit > 0 else 0
kelly = (winrate * edge - (1-winrate)) / edge if edge > 0 else 0
kelly_f = max(0.0, min(0.25, kelly))

m1,m2,m3,m4,m5 = st.columns(5)
m1.metric("Debit", f"${debit:,}")
m2.metric("Effective Winner", f"${eff_winner:+.0f}")
m3.metric("Edge/$", f"{edge:.3f}×")
m4.metric("Kelly", f"{kelly_f:.1%}")
m5.metric("Shrink", f"{regime['shrink']}%")

# ================================
# SACRED TABLE
# ================================
with st.expander("Sacred 9D/30D Performance Table (2020–Nov 2025)", expanded=True):
    st.markdown("""
**Realised | 8–9 DTE short 0.25% OTM put → 16–18 DTE –20 wide long**

| 9D/30D Ratio     | Typical debit       | Realised winner       | Model Winner | Realised Edge/$ | Verdict                |
|------------------|---------------------|------------------------|--------------|------------------|------------------------|
| ≥ 1.12           | $550 – $1,100       | $285 – $355            | $224+        | 0.30x+           | **MAXIMUM / NUCLEAR**  |
| 1.04 – 1.119     | $750 – $1,150       | $258 – $292            | $220         | 0.24x–0.30x      | **ENHANCED**           |
| 0.94 – 1.039     | $1,050 – $1,550     | $225 – $275            | $208         | 0.19x–0.23x      | **OPTIMAL**            |
| 0.88 – 0.939     | $1,400 – $1,750     | $215 – $245            | $195         | 0.13x–0.16x      | **ACCEPTABLE**         |
| 0.84 – 0.879     | $1,650 – $2,100     | $185 – $220            | $180         | 0.10x–0.12x      | **MARGINAL**           |
| ≤ 0.839          | $2,000 – $2,800     | $110 – $170            | $110         | ≤ 0.07x          | **OFF**                |
    """, unsafe_allow_html=True)

# ================================
# MONTE CARLO
# ================================
if st.button("RUN MONTE CARLO", use_container_width=True):
    with st.spinner(f"Running {paths} paths × {trades} trades..."):
        np.random.seed(42)
        finals = []
        all_paths = []
        for _ in range(paths):
            bal = start_bal
            path = [bal]
            streak = 0
            for _ in range(trades):
                contracts = min(max_cont, max(1, int(kelly_f * bal * 0.5 / debit)))
                won = np.random.random() < (winrate if streak == 0 else winrate * 0.6)
                pnl = (eff_winner if won else loser) * contracts
                if np.random.random() < 0.01: pnl = loser * 2.5 * contracts
                streak = streak + 1 if not won and np.random.random() < 0.5 else 0
                bal = max(bal + pnl, 1000)
                path.append(bal)
            finals.append(bal)
            all_paths.append(path)
        
        finals = np.array(finals)
        mean_path = np.mean(all_paths, axis=0)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            fig = go.Figure()
            for p in all_paths[:100]:
                fig.add_trace(go.Scatter(y=p, mode='lines', line=dict(width=1, color="#475569"), showlegend=False))
            fig.add_trace(go.Scatter(y=mean_path, mode='lines', line=dict(color='#60a5fa', width=5), name='Mean Path'))
            fig.add_hline(y=start_bal, line_color="#e11d48", line_dash="dash")
            fig.update_layout(height=560, template="plotly_dark", title="Monte Carlo Equity Curves")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.metric("Median Final", f"${np.median(finals)/1e6:.2f}M")
            st.metric("95th Percentile", f"${np.percentile(finals,95)/1e6:.2f}M")
            st.metric("Ruin Rate", f"{(finals<10000).mean():.2%}")

st.caption("SPX Diagonal Engine v6.9.35 — CLEAN GRAPH + VRP + DAILY Forward • Dec 2025")
