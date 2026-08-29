"""Command Center page."""

from datetime import timedelta

import pandas as pd
import streamlit as st

from dashboard.components import latest_by_zone, metric_card, page_header


def _scenario_score(flow_rate: float, consumption: float, pressure: float, expected: pd.Series, persistence: int) -> tuple[float, str, dict]:
    """Return a transparent what-if estimate without claiming ML inference."""
    flow_volume = flow_rate * 0.25
    unaccounted_pct = ((flow_volume - consumption) / flow_volume * 100) if flow_volume else 0.0
    flow_deviation = ((flow_volume - expected["expected_flow"]) / expected["expected_flow"] * 100) if expected["expected_flow"] else 0.0
    consumption_deviation = ((consumption - expected["expected_consumption"]) / expected["expected_consumption"] * 100) if expected["expected_consumption"] else 0.0
    pressure_deviation = ((pressure - expected["expected_pressure"]) / expected["expected_pressure"] * 100) if expected["expected_pressure"] else 0.0
    water_signal = min(1.0, max(0.0, (unaccounted_pct - 15.0) / 35.0))
    pressure_signal = min(1.0, max(0.0, -pressure_deviation / 30.0))
    flow_signal = min(1.0, abs(flow_deviation) / 75.0)
    consumption_signal = min(1.0, abs(consumption_deviation) / 75.0)
    # The saved Isolation Forest is not a live prediction service. For what-if
    # exploration only, the strongest measured signal is an explicit proxy for
    # its 35-point component. The production pipeline remains unchanged.
    anomaly_proxy = max(water_signal, pressure_signal, flow_signal, consumption_signal)
    score = min(100.0, max(0.0,
        35 * anomaly_proxy + 20 * water_signal + 15 * pressure_signal
        + 10 * flow_signal + 10 * consumption_signal + 10 * persistence / 8
    ))
    category = "HIGH RISK" if score >= 70 else "MONITOR" if score >= 40 else "NORMAL"
    details = {
        "flow_volume": flow_volume, "unaccounted_pct": unaccounted_pct,
        "flow_deviation": flow_deviation, "consumption_deviation": consumption_deviation,
        "pressure_deviation": pressure_deviation,
    }
    return score, category, details


def render_command_center(data: pd.DataFrame) -> None:
    page_header("AquaGuard AI", "Urban Water Intelligence Platform", "Network-wide anomaly prioritization for human inspection.")
    st.markdown("`Prototype · Synthetic Data`")
    hourly_timestamps = pd.DatetimeIndex(data["timestamp"].dt.floor("h").unique()).sort_values()
    latest_hour = hourly_timestamps[-1]
    high_risk_hour = data.loc[data["risk_score"].idxmax(), "timestamp"].floor("h")
    if "command_snapshot_hour" not in st.session_state:
        st.session_state.command_snapshot_hour = latest_hour
    quick_left, quick_right = st.columns([1, 4])
    if quick_left.button("Show high-risk example", width="stretch"):
        st.session_state.command_snapshot_hour = high_risk_hour
    if quick_right.button("Return to latest hour"):
        st.session_state.command_snapshot_hour = latest_hour
    selected_hour = st.select_slider(
        "Network snapshot hour",
        options=hourly_timestamps,
        key="command_snapshot_hour",
        format_func=lambda value: value.strftime("%d %b %Y · %H:00"),
        help="Each position summarizes four 15-minute readings for the selected hour.",
    )
    snapshot_label = "Latest available hour" if selected_hour == latest_hour else "Historical simulation snapshot"
    st.caption(f"{snapshot_label} · values below are recalculated for {selected_hour:%d %b %Y, %H:00–%H:59}.")
    hour_data = data.loc[
        (data["timestamp"] >= selected_hour)
        & (data["timestamp"] < selected_hour + timedelta(hours=1))
    ]
    latest = latest_by_zone(hour_data)
    counts = latest["risk_category"].value_counts()
    total_input_volume = hour_data["flow_volume_m3"].sum()
    total_consumption = hour_data["consumption_m3"].sum()
    positive_unaccounted = hour_data["unaccounted_water_m3"].clip(lower=0).sum()
    # Transparent prototype indicator: a lower average current risk produces a
    # higher health score. This is not an industry-standard water metric.
    health_score = max(0.0, 100.0 - latest["risk_score"].mean())

    cards = st.columns(4)
    with cards[0]:
        metric_card("Zones monitored", f"{len(latest)}", f"{len(data):,} readings analyzed")
    with cards[1]:
        metric_card("Current high risk", f"{counts.get('HIGH RISK', 0)} zones", "Latest reading per zone", "HIGH RISK")
    with cards[2]:
        metric_card("Current monitor", f"{counts.get('MONITOR', 0)} zones", f"{counts.get('NORMAL', 0)} zones normal", "MONITOR")
    with cards[3]:
        metric_card("Network health", f"{health_score:.1f}/100", "Prototype: 100 − mean current risk score", "NORMAL")

    volumes = st.columns(3)
    with volumes[0]:
        metric_card("Total input flow", f"{total_input_volume:,.1f} m³", "Supplied volume across all zones during selected hour")
    with volumes[1]:
        metric_card("Total consumption", f"{total_consumption:,.1f} m³", "Recorded consumption across all zones during selected hour")
    with volumes[2]:
        metric_card("Potential imbalance", f"{positive_unaccounted:,.1f} m³", "Positive interval differences during selected hour")

    st.markdown("#### Current network state")
    left, right = st.columns([2.2, 1])
    with left:
        display = latest[["zone_id", "risk_score", "risk_category"]].rename(
            columns={"zone_id": "Zone", "risk_score": "Risk score", "risk_category": "Status"}
        )
        st.dataframe(
            display, hide_index=True, width="stretch", height=390,
            column_config={"Risk score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f")},
        )
    with right:
        metric_card("Selected snapshot", selected_hour.strftime("%H:00"), selected_hour.strftime("%d %b %Y"))
        st.markdown("##### Inspect a zone")
        zone = st.selectbox("Zone", latest["zone_id"].tolist(), label_visibility="collapsed")
        current = latest.loc[latest["zone_id"] == zone].iloc[0]
        st.markdown(f"**{zone} · {current['risk_category']} · {current['risk_score']:.1f}/100**")
        st.caption(current["explanation"])

    st.markdown("#### Priority alerts")
    recent_high = data.loc[data["risk_category"] == "HIGH RISK"].nlargest(6, "risk_score")
    if recent_high.empty:
        st.success("No HIGH RISK observations are present in this dataset.")
    else:
        for row in recent_high.itertuples():
            st.markdown(
                f'<div class="alert-card"><strong>{row.zone_id} · {row.risk_score:.1f}/100</strong> '
                f'<small>{row.timestamp:%d %b %Y, %H:%M}</small><br>{row.explanation}<br>'
                f'<small>Imbalance {row.unaccounted_water_m3:+.2f} m³ · Pressure deviation {row.pressure_deviation_pct:+.1f}%</small></div>',
                unsafe_allow_html=True,
            )

    st.markdown("#### What-if Scenario Lab")
    st.caption("Enter hypothetical measurements to explore the transparent risk rules. This estimate does not rerun Isolation Forest and is not a confirmed leak assessment.")
    scenario_zone = st.selectbox("Scenario zone", latest["zone_id"].tolist(), key="scenario_zone")
    baseline = latest.loc[latest["zone_id"] == scenario_zone].iloc[0]
    inputs = st.columns(4)
    flow_rate = inputs[0].number_input("Input flow rate (m³/h)", min_value=0.0, value=float(baseline["flow_m3_per_hour"]), step=1.0)
    consumption = inputs[1].number_input("Consumption (m³ / 15 min)", min_value=0.0, value=float(baseline["consumption_m3"]), step=0.5)
    pressure = inputs[2].number_input("Pressure (m head)", min_value=0.0, value=float(baseline["pressure_m_head"]), step=1.0)
    persistence = inputs[3].slider("Elevated readings in last 8", 0, 8, int(baseline["persistence_count_8"]))
    score, category, details = _scenario_score(flow_rate, consumption, pressure, baseline, persistence)
    results = st.columns(4)
    with results[0]: metric_card("Estimated scenario risk", f"{score:.1f}/100", "Rule-based what-if estimate", category)
    with results[1]: metric_card("Estimated category", category, "NORMAL <40 · MONITOR <70", category)
    with results[2]: metric_card("Input volume", f"{details['flow_volume']:.2f} m³", "Converted from hourly rate")
    with results[3]: metric_card("Water imbalance", f"{details['unaccounted_pct']:+.1f}%", f"Pressure deviation {details['pressure_deviation']:+.1f}%")
    st.caption(
        f"Scenario deviations — flow {details['flow_deviation']:+.1f}%, consumption "
        f"{details['consumption_deviation']:+.1f}%, pressure {details['pressure_deviation']:+.1f}%."
    )
