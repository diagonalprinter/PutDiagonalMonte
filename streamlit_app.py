# === ONLY CHANGE NEEDED IN THE SIMULATION SECTION ===
# Replace the old simulation block with this one (everything else stays identical)

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

                    if np.random.random() < 0.01:                    # 1 % black swan
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
                # ← FIXED LINE BELOW (added the #)
                for p in paths[:100]:
                    fig.add_trace(go.Scatter(y=p, mode='lines',
                                           line=dict(width=1, color='#64748b33'),
                                           showlegend=False))
                fig.add_trace(go.Scatter(y=mean_path, mode='lines',
                                        line=dict(color='#60a5fa', width=5),
                                        name='Mean Path'))
                fig.add_hline(y=start_bal, line_color="#e11d48", line_dash="dash",
                             annotation_text="Starting Capital")
                fig.update_layout(template="plotly_dark", height=560,
                                 title="Monte Carlo Equity Curves")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.metric("Median Final Balance", f"${np.median(finals)/1e6:.2f}M")
                st.metric("95th Percentile", f"${np.percentile(finals,95)/1e6:.2f}M")
                st.metric("Mean CAGR", f"{np.mean(cagr):.1%}")
                st.metric("Ruin Rate (<$10k)", f"{(finals<10000).mean():.2%}")
