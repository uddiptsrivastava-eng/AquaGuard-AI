"""Interactive overview of real smart-meter sites within the monitored DMA."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components import chart_style, load_meter_data, metric_card, page_header


def render_city_overview(data: pd.DataFrame) -> None:
    page_header("Meter Site Overview", "One Real Monitored DMA",
                "Inspect 15 anonymized smart-meter locations. Positions are conceptual, not geographic.")
    meters = load_meter_data()
    hours = pd.DatetimeIndex(data["timestamp"].unique()).sort_values()
    selected = st.select_slider("Site inspection hour", options=hours, value=hours[-1],
                                format_func=lambda value: value.strftime("%d %b %Y · %H:00"))
    site = meters.loc[meters["timestamp"] == selected].copy()
    network = data.loc[data["timestamp"] == selected].iloc[0]
    site["x"] = [(index % 5) * 2.0 + 1 for index in range(len(site))]
    site["y"] = [6 - (index // 5) * 2 for index in range(len(site))]

    cards = st.columns(4)
    with cards[0]: metric_card("Meter locations", f"{len(site)}", "SWM1 excluded as publisher-documented faulty")
    with cards[1]: metric_card("Median pressure", f"{site['pressure_m_head'].median():.1f} m", "Across available sites")
    with cards[2]: metric_card("Metered use", f"{site['consumption_m3'].sum():.2f} m³", "Cumulative-difference method")
    with cards[3]: metric_card("Controlled test", "ACTIVE" if network["is_controlled_leak"] else "Not active", network["leak_event_ids"])

    map_col, inspect_col = st.columns([2.1, 1])
    with map_col:
        figure = go.Figure(go.Scatter(
            x=site["x"], y=site["y"], mode="markers+text", text=site["meter_id"], textposition="top center",
            marker=dict(size=24, color=site["pressure_m_head"], colorscale="Tealgrn", showscale=True,
                        colorbar=dict(title="Pressure<br>(m head)"), line=dict(color="#d8edf5", width=1)),
            customdata=site[["meter_id", "pressure_bar", "pressure_m_head", "consumption_m3"]],
            hovertemplate="<b>%{customdata[0]}</b><br>Pressure %{customdata[1]:.2f} bar (%{customdata[2]:.1f} m head)<br>Consumption %{customdata[3]:.3f} m³<extra></extra>",
        ))
        figure.update_layout(xaxis=dict(visible=False, range=[0, 10]), yaxis=dict(visible=False, range=[0, 7]))
        st.plotly_chart(chart_style(figure, 500), width="stretch", config={"displayModeBar": False})
        st.caption("The layout is a deterministic inspection diagram; the public archive anonymizes real geographic positions.")
    with inspect_col:
        selected_meter = st.selectbox("Meter location", site["meter_id"].tolist())
        row = site.loc[site["meter_id"] == selected_meter].iloc[0]
        metric_card("Selected meter", selected_meter, selected.strftime("%d %b %Y · %H:00"))
        st.write(f"**Pressure:** {row['pressure_bar']:.2f} bar ({row['pressure_m_head']:.1f} m head)")
        st.write(f"**Hourly consumption:** {row['consumption_m3']:.3f} m³")
        st.info("This is a measurement location, not a separately risk-scored city zone.")

    st.markdown("#### Site measurements")
    table = site[["meter_id", "pressure_bar", "pressure_m_head", "consumption_m3"]].rename(columns={
        "meter_id": "Meter", "pressure_bar": "Pressure (bar)",
        "pressure_m_head": "Pressure (m head)", "consumption_m3": "Consumption (m³/hour)"})
    st.dataframe(table, hide_index=True, width="stretch")
