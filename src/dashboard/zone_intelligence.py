"""Detailed per-zone intelligence page."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components import STATUS_COLORS, TIME_WINDOWS, chart_style, filter_time_window, metric_card, page_header


def _line_chart(frame: pd.DataFrame, series: list[tuple[str, str, str]], title: str, y_title: str) -> go.Figure:
    figure = go.Figure()
    for column, label, color in series:
        figure.add_trace(go.Scatter(x=frame["timestamp"], y=frame[column], name=label, mode="lines", line=dict(color=color, width=2)))
    high = frame["risk_category"] == "HIGH RISK"
    if high.any():
        marker_column = series[0][0]
        figure.add_trace(go.Scatter(x=frame.loc[high, "timestamp"], y=frame.loc[high, marker_column], name="High risk", mode="markers", marker=dict(color="#f16464", size=7, symbol="diamond")))
    figure.update_layout(title=title, yaxis_title=y_title, xaxis_title=None)
    return chart_style(figure)


def render_zone_intelligence(data: pd.DataFrame) -> None:
    page_header("DMA Intelligence", "Detailed Investigation", "Inspect real hourly measurements and past-only historical deviations for the monitored DMA.")
    controls = st.columns([1, 1, 2])
    zone = controls[0].selectbox("DMA", sorted(data["zone_id"].unique()))
    window = controls[1].selectbox("Time window", list(TIME_WINDOWS))
    zone_data = data.loc[data["zone_id"] == zone].sort_values("timestamp")
    view = filter_time_window(zone_data, window)
    current = zone_data.iloc[-1]

    gauge_col, detail_col = st.columns([1, 2])
    with gauge_col:
        gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=current["risk_score"], number={"suffix": "/100"}, title={"text": f"{zone} current risk"},
            gauge={"axis": {"range": [0, 100]}, "bar": {"color": STATUS_COLORS[current["risk_category"]]},
                   "steps": [{"range": [0, 40], "color": "#12352f"}, {"range": [40, 70], "color": "#4a3d1c"}, {"range": [70, 100], "color": "#4b2428"}]},
        ))
        st.plotly_chart(chart_style(gauge, 285), width="stretch", config={"displayModeBar": False})
    with detail_col:
        cols = st.columns(3)
        with cols[0]: metric_card("Inlet flow", f"{current['flow_m3_per_hour']:.1f} m³/h", f"Outlet: {current['outflow_m3h']:.1f} m³/h")
        with cols[1]: metric_card("Consumption", f"{current['consumption_m3']:.2f} m³", f"{current['consumption_deviation_pct']:+.1f}% vs baseline")
        with cols[2]: metric_card("Pressure", f"{current['pressure_m_head']:.1f} m", f"{current['pressure_deviation_pct']:+.1f}% vs baseline")
        st.markdown("### Why was this DMA prioritized?")
        st.info(current["explanation"])
        st.caption(f"Latest unaccounted water: {current['unaccounted_water_m3']:+.2f} m³ ({current['unaccounted_water_pct']:+.1f}%). This may indicate anomalous network behaviour, not a confirmed leak.")

    st.plotly_chart(_line_chart(view, [("flow_volume_m3", "Inlet volume", "#5cc8e8"), ("outflow_volume_m3", "Outlet volume", "#9b8bea"), ("consumption_m3", "Metered consumption", "#a5de73")], "DMA hourly water balance", "m³ per hour"), width="stretch")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(_line_chart(view, [("pressure_m_head", "Pressure", "#9b8bea")], "Network pressure", "Metres of water head"), width="stretch")
    with right:
        st.plotly_chart(_line_chart(view, [("risk_score", "Risk score", "#f4bf4f")], "Prototype risk score", "Score (0–100)"), width="stretch")

    st.markdown("### DMA observation history")
    history = view.copy().sort_values("timestamp", ascending=False)
    history.insert(0, "Date", history["timestamp"].dt.strftime("%d %b %Y"))
    history.insert(1, "Time", history["timestamp"].dt.strftime("%H:%M"))
    history = history[["Date", "Time", "flow_volume_m3", "outflow_volume_m3", "consumption_m3", "pressure_m_head", "risk_score", "risk_category", "is_controlled_leak", "explanation"]].rename(columns={
        "flow_volume_m3": "Inlet volume (m³/hour)", "outflow_volume_m3": "Outlet volume (m³/hour)", "consumption_m3": "Consumption (m³/hour)",
        "pressure_m_head": "Pressure (m head)", "risk_score": "Risk score", "risk_category": "Category", "explanation": "Explanation",
        "is_controlled_leak": "Controlled test active",
    })
    st.dataframe(
        history, hide_index=True, width="stretch", height=430,
        column_config={"Risk score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"), "Explanation": st.column_config.TextColumn(width="large")},
    )
