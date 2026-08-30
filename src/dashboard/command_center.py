"""Command Center for the public single-DMA field dataset."""

import pandas as pd
import streamlit as st

from dashboard.components import metric_card, page_header


def _scenario_score(inflow: float, outflow: float, consumption: float, pressure: float,
                    expected: pd.Series, persistence: int) -> tuple[float, str, dict]:
    imbalance = inflow - outflow - consumption
    imbalance_pct = imbalance / inflow * 100 if inflow else 0.0
    flow_dev = (inflow - expected["expected_flow"]) / expected["expected_flow"] * 100 if expected["expected_flow"] else 0.0
    use_dev = (consumption - expected["expected_consumption"]) / expected["expected_consumption"] * 100 if expected["expected_consumption"] else 0.0
    pressure_dev = (pressure - expected["expected_pressure"]) / expected["expected_pressure"] * 100 if expected["expected_pressure"] else 0.0
    water = min(1.0, max(0.0, (imbalance_pct - 15) / 35))
    low_pressure = min(1.0, max(0.0, -pressure_dev / 30))
    flow_signal = min(1.0, abs(flow_dev) / 75)
    consumption_signal = min(1.0, abs(use_dev) / 75)
    proxy = max(water, low_pressure, flow_signal, consumption_signal)
    score = min(100.0, 35 * proxy + 20 * water + 15 * low_pressure + 10 * flow_signal
                + 10 * consumption_signal + 10 * persistence / 8)
    category = "HIGH RISK" if score >= 70 else "MONITOR" if score >= 40 else "NORMAL"
    return score, category, {"imbalance": imbalance, "imbalance_pct": imbalance_pct,
                             "flow_dev": flow_dev, "use_dev": use_dev, "pressure_dev": pressure_dev}


def render_command_center(data: pd.DataFrame) -> None:
    page_header("AquaGuard AI", "Real DMA Command Center",
                "Anomaly prioritization using public field measurements from one monitored water-distribution area.")
    st.markdown("`Prototype · Public NTNU/SINTEF field dataset · Controlled leak tests`")
    hours = pd.DatetimeIndex(data["timestamp"].unique()).sort_values()
    latest_hour = hours[-1]
    example_hour = data.loc[data["risk_score"].idxmax(), "timestamp"]
    if "command_snapshot_hour" not in st.session_state:
        st.session_state.command_snapshot_hour = latest_hour
    left_button, right_button = st.columns([1, 4])
    if left_button.button("Show highest-risk hour", width="stretch"):
        st.session_state.command_snapshot_hour = example_hour
    if right_button.button("Return to latest hour"):
        st.session_state.command_snapshot_hour = latest_hour
    selected = st.select_slider("DMA snapshot hour", options=hours, key="command_snapshot_hour",
                                format_func=lambda value: value.strftime("%d %b %Y · %H:00"))
    row = data.loc[data["timestamp"] == selected].iloc[0]
    health = max(0.0, 100.0 - row["risk_score"])

    cards = st.columns(4)
    with cards[0]: metric_card("Monitored area", "1 DMA", "15 usable smart-meter sites")
    with cards[1]: metric_card("Inspection status", row["risk_category"], f"Risk {row['risk_score']:.1f}/100", row["risk_category"])
    with cards[2]: metric_card("Controlled test", "ACTIVE" if row["is_controlled_leak"] else "Not active", row["leak_event_ids"])
    with cards[3]: metric_card("DMA health", f"{health:.1f}/100", "Prototype: 100 − selected risk", "NORMAL")

    volumes = st.columns(4)
    with volumes[0]: metric_card("Inlet volume", f"{row['flow_volume_m3']:.2f} m³", "Measured during selected hour")
    with volumes[1]: metric_card("Outlet volume", f"{row['outflow_volume_m3']:.2f} m³", "Measured during selected hour")
    with volumes[2]: metric_card("Metered consumption", f"{row['consumption_m3']:.2f} m³", f"{int(row['meter_coverage'])}/15 meter sites")
    with volumes[3]: metric_card("Unaccounted balance", f"{row['unaccounted_water_m3']:+.2f} m³", "Inlet − outlet − metered use")

    st.markdown("#### Selected DMA observation")
    display = pd.DataFrame([{
        "Date": selected.strftime("%d %b %Y"), "Time": selected.strftime("%H:%M"),
        "Inlet (m³/h)": row["flow_m3_per_hour"], "Outlet (m³/h)": row["outflow_m3h"],
        "Consumption (m³)": row["consumption_m3"], "Pressure (m head)": row["pressure_m_head"],
        "Risk score": row["risk_score"], "Category": row["risk_category"],
    }])
    st.dataframe(display, hide_index=True, width="stretch")
    st.info(row["explanation"])

    st.markdown("#### Priority alerts")
    alerts = data.loc[data["risk_category"] == "HIGH RISK"].nlargest(6, "risk_score")
    for alert in alerts.itertuples():
        st.markdown(
            f'<div class="alert-card"><strong>{alert.zone_id} · {alert.risk_score:.1f}/100</strong> '
            f'<small>{alert.timestamp:%d %b %Y, %H:%M}</small><br>{alert.explanation}<br>'
            f'<small>Balance {alert.unaccounted_water_m3:+.2f} m³ · Controlled test: '
            f'{"yes" if alert.is_controlled_leak else "no"}</small></div>', unsafe_allow_html=True)

    st.markdown("#### What-if Scenario Lab")
    st.caption("A transparent rule-based estimate. It does not rerun Isolation Forest and does not confirm a leak.")
    inputs = st.columns(5)
    inlet = inputs[0].number_input("Inlet flow (m³/h)", min_value=0.0, value=float(row["flow_m3_per_hour"]), step=1.0)
    outlet = inputs[1].number_input("Outlet flow (m³/h)", min_value=0.0, value=float(row["outflow_m3h"]), step=1.0)
    consumption = inputs[2].number_input("Metered use (m³/hour)", min_value=0.0, value=float(row["consumption_m3"]), step=0.1)
    pressure = inputs[3].number_input("Pressure (m head)", min_value=0.0, value=float(row["pressure_m_head"]), step=1.0)
    persistence = inputs[4].slider("Elevated hours in last 8", 0, 8, int(row["persistence_count_8"]))
    score, category, details = _scenario_score(inlet, outlet, consumption, pressure, row, persistence)
    results = st.columns(3)
    with results[0]: metric_card("Estimated risk", f"{score:.1f}/100", "Rule-based what-if", category)
    with results[1]: metric_card("Estimated category", category, "NORMAL <40 · MONITOR <70", category)
    with results[2]: metric_card("Estimated balance", f"{details['imbalance']:+.2f} m³", f"{details['imbalance_pct']:+.1f}% of inlet")
