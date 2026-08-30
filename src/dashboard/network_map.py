"""Conceptual topology for the anonymized real DMA measurement sites."""

import plotly.graph_objects as go
import streamlit as st

from dashboard.components import chart_style, load_meter_data, metric_card, page_header


def render_network_map(data) -> None:
    page_header("Conceptual DMA Sensor Network", "Network Map",
                "An anonymized inspection topology for real meter sites—not the utility's pipe map.")
    meters = load_meter_data()
    latest_time = meters["timestamp"].max()
    latest = meters.loc[meters["timestamp"] == latest_time].sort_values("meter_id").reset_index(drop=True)
    coordinates = {row.meter_id: ((index % 5) * 2.1, 5.5 - (index // 5) * 2.0)
                   for index, row in enumerate(latest.itertuples())}
    names = list(coordinates)
    edges = [(names[index], names[index + 1]) for index in range(len(names) - 1)]
    edge_x, edge_y = [], []
    for start, end in edges:
        edge_x += [coordinates[start][0], coordinates[end][0], None]
        edge_y += [coordinates[start][1], coordinates[end][1], None]
    figure = go.Figure(go.Scatter(x=edge_x, y=edge_y, mode="lines",
                                  line=dict(color="#23485c", width=2), hoverinfo="skip"))
    figure.add_trace(go.Scatter(
        x=[coordinates[name][0] for name in names], y=[coordinates[name][1] for name in names],
        mode="markers+text", text=names, textposition="top center", name="Meter sites",
        marker=dict(size=24, color=latest["pressure_m_head"], colorscale="Tealgrn", showscale=True,
                    colorbar=dict(title="Pressure<br>(m head)"), line=dict(color="#d8edf5", width=1)),
        customdata=latest[["pressure_bar", "pressure_m_head", "consumption_m3"]],
        hovertemplate="<b>%{text}</b><br>Pressure %{customdata[0]:.2f} bar (%{customdata[1]:.1f} m head)<br>Consumption %{customdata[2]:.3f} m³<extra></extra>",
    ))
    figure.update_layout(showlegend=False, xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(chart_style(figure, 520), width="stretch", config={"displayModeBar": False})
    st.warning("Connections and positions are conceptual because the public release anonymizes operational geography.")

    meter = st.selectbox("Inspect meter site", names, key="map_meter")
    row = latest.loc[latest["meter_id"] == meter].iloc[0]
    cols = st.columns(3)
    with cols[0]: metric_card("Selected site", meter, f"Latest: {latest_time:%d %b %H:%M}")
    with cols[1]: metric_card("Pressure", f"{row['pressure_m_head']:.1f} m", f"{row['pressure_bar']:.2f} bar")
    with cols[2]: metric_card("Metered use", f"{row['consumption_m3']:.3f} m³", "Latest hourly cumulative difference")
