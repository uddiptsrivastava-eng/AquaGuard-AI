"""Interactive conceptual city-level inspection overview."""

from datetime import timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dashboard.components import STATUS_COLORS, chart_style, latest_by_zone, metric_card, page_header


DISTRICTS = {
    "North District": ["Z01", "Z02", "Z03", "Z04"], "East District": ["Z05", "Z06", "Z07", "Z08"],
    "Central District": ["Z09", "Z10", "Z11", "Z12"], "West District": ["Z13", "Z14", "Z15", "Z16"],
    "South District": ["Z17", "Z18", "Z19", "Z20"],
}
COORDINATES = {
    "Z01": (3.0, 8.4), "Z02": (4.4, 8.8), "Z03": (5.8, 8.3), "Z04": (7.1, 8.7),
    "Z05": (8.2, 6.7), "Z06": (8.8, 5.5), "Z07": (8.3, 4.2), "Z08": (8.9, 3.0),
    "Z09": (4.3, 6.3), "Z10": (5.7, 6.5), "Z11": (4.5, 4.9), "Z12": (6.0, 4.8),
    "Z13": (2.0, 6.7), "Z14": (1.3, 5.5), "Z15": (2.0, 4.1), "Z16": (1.2, 3.0),
    "Z17": (3.0, 1.8), "Z18": (4.4, 1.2), "Z19": (5.9, 1.6), "Z20": (7.2, 1.1),
}


def _district_for(zone: str) -> str:
    return next(name for name, zones in DISTRICTS.items() if zone in zones)


def render_city_overview(data: pd.DataFrame) -> None:
    page_header("City Overview", "Conceptual Urban Operations", "Explore simulated districts and select zones for inspection. This is not a real geographic map.")
    hours = pd.DatetimeIndex(data["timestamp"].dt.floor("h").unique()).sort_values()
    selected_hour = st.select_slider("City inspection hour", options=hours, value=hours[-1], format_func=lambda value: value.strftime("%d %b %Y · %H:00"))
    hour_data = data.loc[(data["timestamp"] >= selected_hour) & (data["timestamp"] < selected_hour + timedelta(hours=1))]
    snapshot = latest_by_zone(hour_data).copy()
    snapshot["district"] = snapshot["zone_id"].map(_district_for)
    district_summary = snapshot.groupby("district", as_index=False).agg(
        zones=("zone_id", "size"), average_risk=("risk_score", "mean"), highest_risk=("risk_score", "max"),
        high_risk_zones=("risk_category", lambda values: int((values == "HIGH RISK").sum())),
    )
    status_counts = snapshot["risk_category"].value_counts()
    cards = st.columns(4)
    with cards[0]: metric_card("City districts", f"{len(DISTRICTS)}", "20 simulated distribution zones")
    with cards[1]: metric_card("High-risk zones", f"{status_counts.get('HIGH RISK', 0)}", "Within selected hour", "HIGH RISK")
    with cards[2]: metric_card("Monitor zones", f"{status_counts.get('MONITOR', 0)}", "Within selected hour", "MONITOR")
    with cards[3]: metric_card("Highest zone risk", f"{snapshot['risk_score'].max():.1f}/100", f"{selected_hour:%d %b · %H:00}")

    map_col, inspect_col = st.columns([2.15, 1])
    with map_col:
        st.markdown("##### Conceptual city inspection view")
        figure = go.Figure()
        for x_values, y_values in [([0.5, 9.5], [5.5, 5.5]), ([5.1, 5.1], [0.4, 9.5]), ([1.0, 8.8], [2.4, 7.7])]:
            figure.add_trace(go.Scatter(x=x_values, y=y_values, mode="lines", line=dict(color="#18394b", width=8), hoverinfo="skip", showlegend=False))
            figure.add_trace(go.Scatter(x=x_values, y=y_values, mode="lines", line=dict(color="#3b6173", width=1, dash="dot"), hoverinfo="skip", showlegend=False))
        for category, color in STATUS_COLORS.items():
            rows = snapshot.loc[snapshot["risk_category"] == category]
            figure.add_trace(go.Scatter(
                x=[COORDINATES[z][0] for z in rows["zone_id"]], y=[COORDINATES[z][1] for z in rows["zone_id"]], mode="markers+text",
                text=rows["zone_id"], textposition="top center", name=category, marker=dict(size=25, color=color, line=dict(color="#e1f1f7", width=1)),
                customdata=[[row.zone_id, row.district, row.risk_score, row.pressure_m_head, row.unaccounted_water_m3] for row in rows.itertuples()],
                hovertemplate="<b>%{customdata[0]}</b> · %{customdata[1]}<br>Risk %{customdata[2]:.1f}/100<br>Pressure %{customdata[3]:.1f} m<br>Imbalance %{customdata[4]:+.2f} m³<extra></extra>",
            ))
        figure.update_layout(xaxis=dict(visible=False, range=[0, 10]), yaxis=dict(visible=False, range=[0, 10]))
        st.plotly_chart(chart_style(figure, 550), width="stretch", config={"displayModeBar": False})
    with inspect_col:
        district = st.selectbox("District", ["All districts", *DISTRICTS])
        eligible = snapshot if district == "All districts" else snapshot.loc[snapshot["district"] == district]
        zone = st.selectbox("Zone to inspect", eligible["zone_id"].tolist())
        row = snapshot.loc[snapshot["zone_id"] == zone].iloc[0]
        metric_card("Inspection priority", f"{row['risk_score']:.1f}/100", f"{row['risk_category']} · {row['district']}", row["risk_category"])
        st.markdown("##### Selected measurements")
        st.write(f"**Date and time:** {row['timestamp']:%d %b %Y, %H:%M}")
        st.write(f"**Input flow:** {row['flow_m3_per_hour']:.1f} m³/h")
        st.write(f"**Consumption:** {row['consumption_m3']:.2f} m³ / 15 min")
        st.write(f"**Pressure:** {row['pressure_m_head']:.1f} m head")
        st.write(f"**Water imbalance:** {row['unaccounted_water_m3']:+.2f} m³")
        st.info(row["explanation"])
        st.caption("Use Zone Intelligence for the selected zone’s complete time-series investigation.")
    st.markdown("#### District inspection summary")
    display = district_summary.rename(columns={"district": "District", "zones": "Zones", "average_risk": "Average risk", "highest_risk": "Highest risk", "high_risk_zones": "High-risk zones"})
    st.dataframe(display, hide_index=True, width="stretch", column_config={"Average risk": st.column_config.NumberColumn(format="%.1f"), "Highest risk": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f")})
