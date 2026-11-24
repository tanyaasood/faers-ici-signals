"""Streamlit dashboard: immune checkpoint inhibitor safety signals in FDA FAERS (2025).

Run locally:   streamlit run app.py
Reads only the small files in data/processed/ (signals.csv, signals_onc.csv, summary.json),
so it deploys on Streamlit Cloud without the raw FDA data.
"""
import json
import pathlib

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = pathlib.Path(__file__).parent / "data" / "processed"

st.set_page_config(page_title="ICI Safety Signals – FAERS 2025", layout="wide")


@st.cache_data
def load():
    main = pd.read_csv(DATA / "signals.csv")
    onc = pd.read_csv(DATA / "signals_onc.csv")
    summary = json.loads((DATA / "summary.json").read_text())
    return main, onc, summary


main, onc, summary = load()

# ---------------- Sidebar ----------------
st.sidebar.title("Settings")
analysis = st.sidebar.radio(
    "Comparator (background)",
    ["All FAERS reports", "Oncology-only reports"],
    help="Oncology-only compares checkpoint inhibitor cases with other cancer patients, "
         "which reduces confounding by indication.",
)
df = main if analysis == "All FAERS reports" else onc
hide_other = st.sidebar.checkbox("Hide 'other ICI combination'", value=True)
if hide_other:
    df = df[df.regimen != "other ICI combination"]
min_a = st.sidebar.slider("Minimum cases (a) to show", 0, 20, 3)

st.sidebar.markdown(
    "**Signal** = all three agree:  \n"
    "• PRR ≥ 2, χ² ≥ 4, a ≥ 3 (Evans)  \n"
    "• ROR lower 95% CI > 1, a ≥ 3  \n"
    "• IC025 > 0 (BCPNN)"
)

# ---------------- Header ----------------
st.title("Immune checkpoint inhibitor safety signals in FDA FAERS (2025)")
st.caption(
    "Disproportionality analysis of immune-related adverse events (irAEs) across checkpoint "
    "inhibitor regimens. Spontaneous reports show reporting imbalance, not incidence or causation."
)

log = summary["cleaning_log"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Report versions loaded", f"{log['DEMO rows loaded (report versions)']:,}")
c2.metric("Unique cases after dedup", f"{log['Cases after dedup + deletions']:,}")
c3.metric("Checkpoint inhibitor cases", f"{log['Cases with a suspect ICI']:,}")
c4.metric("Signals (current view)", f"{int(df.signal.sum())} / {len(df)}")

tab1, tab2, tab3, tab4 = st.tabs(["Signal heatmap", "Compare drugs", "Robustness", "Data"])

regimen_order = [r for r in summary["regimen_counts"] if r in set(df.regimen)]
ae_order = sorted(df.ae_group.unique())

# ---------------- Tab 1: heatmap ----------------
with tab1:
    st.subheader("ROR lower 95% confidence bound by regimen and irAE")
    st.caption("Colour = lower bound of the ROR 95% CI (log scale). ★ = signal by all three methods. "
               "Blank = fewer cases than the minimum.")
    piv = df.pivot(index="regimen", columns="ae_group", values="ror_lo").reindex(index=regimen_order, columns=ae_order)
    a_piv = df.pivot(index="regimen", columns="ae_group", values="a").reindex(index=regimen_order, columns=ae_order)
    ror_piv = df.pivot(index="regimen", columns="ae_group", values="ror").reindex(index=regimen_order, columns=ae_order)
    sig_piv = df.pivot(index="regimen", columns="ae_group", values="signal").reindex(index=regimen_order, columns=ae_order)

    z = np.log10(piv.clip(lower=0.1).where(a_piv >= min_a))
    text = ror_piv.round(1).astype(str) + np.where(sig_piv.fillna(False), " ★", "")
    text = text.where(a_piv >= min_a, "")
    hover = ("ROR " + ror_piv.round(1).astype(str) + " (lower CI " + piv.round(2).astype(str)
             + ")<br>cases: " + a_piv.astype("Int64").astype(str))

    fig = go.Figure(go.Heatmap(
        z=z.values, x=ae_order, y=regimen_order, text=text.values, texttemplate="%{text}",
        customdata=hover.values, hovertemplate="%{y} – %{x}<br>%{customdata}<extra></extra>",
        colorscale="Reds", zmin=0, zmax=2,
        colorbar=dict(title="ROR lower CI", tickvals=[0, 1, 2], ticktext=["1", "10", "100"]),
    ))
    fig.update_layout(height=480, margin=dict(l=10, r=10, t=10, b=10), yaxis_autorange="reversed")
    st.plotly_chart(fig, width="stretch")

# ---------------- Tab 2: forest plot ----------------
with tab2:
    ae = st.selectbox("Adverse event group", ae_order,
                      index=ae_order.index("Hypophysitis") if "Hypophysitis" in ae_order else 0)
    sub = df[(df.ae_group == ae) & (df.a >= min_a)].sort_values("ror")
    if sub.empty:
        st.info("No regimen has enough cases for this event at the current minimum.")
    else:
        colours = np.where(sub.signal, "#c0392b", "#7f8c8d")
        fig2 = go.Figure(go.Scatter(
            x=sub.ror, y=sub.regimen, mode="markers",
            marker=dict(size=10, color=colours),
            error_x=dict(type="data", symmetric=False,
                         array=sub.ror_hi - sub.ror, arrayminus=sub.ror - sub.ror_lo),
            customdata=np.stack([sub.a, sub.ror_lo, sub.ror_hi], axis=1),
            hovertemplate="%{y}<br>ROR %{x:.1f} (95% CI %{customdata[1]:.1f}–%{customdata[2]:.1f})"
                          "<br>cases: %{customdata[0]}<extra></extra>",
        ))
        fig2.add_vline(x=1, line_dash="dash", line_color="black")
        fig2.update_xaxes(type="log", title="Reporting odds ratio (log scale)")
        fig2.update_layout(height=60 + 45 * len(sub), margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig2, width="stretch")
        st.caption("Red = signal by all three methods. Dashed line = ROR 1 (no disproportionality).")

# ---------------- Tab 3: robustness ----------------
with tab3:
    st.subheader("All-FAERS vs oncology-only comparator")
    st.caption("Points below the diagonal shrink when compared with other cancer patients "
               "(confounding by indication). Signals that stay above ROR 1 on the y-axis are robust.")
    j = main.merge(onc, on=["regimen", "ae_group"], suffixes=("_all", "_onc"))
    j = j[(j.a_all >= min_a) & (j.ror_all > 0) & (j.ror_onc > 0)]
    if hide_other:
        j = j[j.regimen != "other ICI combination"]
    fig3 = go.Figure()
    for ae_name, g in j.groupby("ae_group"):
        fig3.add_trace(go.Scatter(
            x=g.ror_all, y=g.ror_onc, mode="markers", name=ae_name,
            text=g.regimen, marker=dict(size=9),
            hovertemplate="%{text}<br>all FAERS %{x:.1f}<br>oncology-only %{y:.1f}<extra>" + ae_name + "</extra>",
        ))
    lim = [0.5, max(j.ror_all.max(), j.ror_onc.max()) * 1.2]
    fig3.add_trace(go.Scatter(x=lim, y=lim, mode="lines", line=dict(dash="dot", color="grey"),
                              showlegend=False, hoverinfo="skip"))
    fig3.add_hline(y=1, line_dash="dash", line_color="black")
    fig3.update_xaxes(type="log", title="ROR – all FAERS background")
    fig3.update_yaxes(type="log", title="ROR – oncology-only background")
    fig3.update_layout(height=520, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig3, width="stretch")
    kept = int((j.signal_all & j.signal_onc).sum())
    lost = int((j.signal_all & ~j.signal_onc).sum())
    st.write(f"**{kept}** signals hold in both analyses; **{lost}** are lost with the oncology-only comparator.")

# ---------------- Tab 4: data ----------------
with tab4:
    cols = ["regimen", "ae_group", "a", "b", "c", "d", "prr", "chi2", "ror", "ror_lo", "ror_hi",
            "ic", "ic025", "sig_prr", "sig_ror", "sig_ic", "signal"]
    show = df[df.a >= min_a][cols].sort_values(["ae_group", "ror"], ascending=[True, False])
    st.dataframe(show.round(2), width="stretch", hide_index=True)
    st.download_button("Download CSV", show.to_csv(index=False), "faers_ici_signals.csv", "text/csv")
    st.markdown("**Cleaning log**")
    st.table(pd.DataFrame(log.items(), columns=["Step", "Count"]).set_index("Step"))

st.divider()
st.caption("Data: FDA Adverse Event Reporting System (FAERS/AEMS) quarterly extracts, 2025 Q1–Q4. "
           "Cases deduplicated by caseid (latest version) with FDA-withdrawn cases removed. "
           "Disproportionality does not establish causation.")
