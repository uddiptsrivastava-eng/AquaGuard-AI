"""Conceptual district-metered-area network page."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components import STATUS_COLORS, chart_style, latest_by_zone, metric_card, page_header


COORDINATES = {f"Z{i + 1:02d}": ((i % 5) * 2.2 + (i // 5) * 0.25, 6.0 - (i // 5) * 1.7) for i in range(20)}
EDGES = [(f"Z{i:02d}", f"Z{i + 1:02d}") for i in range(1, 20) if i % 5 != 0]
EDGES += [(f"Z{i:02d}", f"Z{i + 5:02d}") for i in range(1, 16)]


def render_network_map(data: pd.DataFrame) -> None:
    page_header("Conceptual DMA Network", "Network Map", "Deterministic simulated topology—not real municipal infrastructure.")
    latest = latest_by_zone(data).set_index("zone_id")

    edge_x, edge_y = [], []
    for start, end in EDGES:
        edge_x += [COORDINATES[start][0], COORDINATES[end][0], None]
        edge_y += [COORDINATES[start][1], COORDINATES[end][1], None]
    figure = go.Figure(go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(color="#23485c", width=2), hoverinfo="skip"))
    for category, color in STATUS_COLORS.items():
        zones = [zone for zone in COORDINATES if latest.loc[zone, "risk_category"] == category]
        figure.add_trace(go.Scatter(
            x=[COORDINATES[z][0] for z in zones], y=[COORDINATES[z][1] for z in zones], mode="markers+text",
            text=zones, textposition="top center", name=category,
            marker=dict(size=[18 + latest.loc[z, "risk_score"] * 0.22 for z in zones], color=color, line=dict(color="#d8edf5", width=1)),
            customdata=[[latest.loc[z, "risk_score"], latest.loc[z, "risk_category"]] for z in zones],
            hovertemplate="<b>%{text}</b><br>Risk %{customdata[0]:.1f}/100<br>%{customdata[1]}<extra></extra>",
        ))
    figure.update_layout(showlegend=True, xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(chart_style(figure, 520), width="stretch", config={"displayModeBar": False})

    zone = st.selectbox("Inspect network zone", sorted(COORDINATES), key="map_zone")
    row = latest.loc[zone]
    cols = st.columns(4)
    with cols[0]: metric_card("Selected zone", zone, f"Latest: {row['timestamp']:%d %b %H:%M}")
    with cols[1]: metric_card("Risk", f"{row['risk_score']:.1f}/100", row["risk_category"], row["risk_category"])
    with cols[2]: metric_card("Pressure", f"{row['pressure_m_head']:.1f} m", f"{row['pressure_deviation_pct']:+.1f}% vs baseline")
    with cols[3]: metric_card("Water balance", f"{row['unaccounted_water_m3']:+.2f} m³", "Latest 15-minute interval")
    st.info(row["explanation"])
