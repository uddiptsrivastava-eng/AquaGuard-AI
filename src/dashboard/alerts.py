"""Searchable alert-review page."""

import pandas as pd
import streamlit as st

from dashboard.components import TIME_WINDOWS, filter_time_window, metric_card, page_header


def render_alerts(data: pd.DataFrame) -> None:
    page_header("Alerts", "Investigation Queue", "Filter calculated observations for review; alerts are not confirmed leak reports.")
    controls = st.columns([1.2, 1.4, 1.2, 1.4])
    zones = controls[0].multiselect("Zone", sorted(data["zone_id"].unique()), placeholder="All zones")
    categories = controls[1].multiselect("Risk category", ["MONITOR", "HIGH RISK", "NORMAL"], default=["MONITOR", "HIGH RISK"])
    window = controls[2].selectbox("Time period", list(TIME_WINDOWS), index=3)
    minimum = controls[3].slider("Minimum risk score", 0, 100, 40)

    filtered = filter_time_window(data, window)
    if zones:
        filtered = filtered.loc[filtered["zone_id"].isin(zones)]
    if categories:
        filtered = filtered.loc[filtered["risk_category"].isin(categories)]
    else:
        filtered = filtered.iloc[0:0]
    filtered = filtered.loc[filtered["risk_score"] >= minimum].sort_values(["risk_score", "timestamp"], ascending=False)

    high_all = data.loc[data["risk_category"] == "HIGH RISK"]
    cards = st.columns(3)
    with cards[0]: metric_card("High-risk readings", f"{len(high_all):,}", "Across all available data", "HIGH RISK")
    with cards[1]: metric_card("Affected zones", f"{high_all['zone_id'].nunique()}", "Zones with high-risk activity", "MONITOR")
    with cards[2]: metric_card("Highest observed risk", f"{data['risk_score'].max():.1f}/100", "Prototype prioritization score", "HIGH RISK")

    st.markdown(f"#### Alert observations · {len(filtered):,} results")
    table = filtered[["timestamp", "zone_id", "risk_score", "risk_category", "unaccounted_water_pct", "pressure_deviation_pct", "explanation"]].rename(columns={
        "timestamp": "Timestamp", "zone_id": "Zone", "risk_score": "Risk score", "risk_category": "Category",
        "unaccounted_water_pct": "Unaccounted water (%)", "pressure_deviation_pct": "Pressure deviation (%)", "explanation": "Explanation",
    })
    st.dataframe(
        table, hide_index=True, width="stretch", height=540,
        column_config={
            "Timestamp": st.column_config.DatetimeColumn(format="DD MMM YYYY, HH:mm"),
            "Risk score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
            "Unaccounted water (%)": st.column_config.NumberColumn(format="%+.1f%%"),
            "Pressure deviation (%)": st.column_config.NumberColumn(format="%+.1f%%"),
            "Explanation": st.column_config.TextColumn(width="large"),
        },
    )
    st.caption("MONITOR and HIGH RISK are emphasized by default. Use the controls above to broaden or narrow the inspection queue.")
