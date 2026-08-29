"""Hackathon demonstration, rollout, and deployment-readiness page."""

import streamlit as st

from dashboard.components import metric_card, page_header


def render_implementation_plan(_data) -> None:
    page_header("Implementation Plan", "From Prototype to Utility Pilot", "A practical path from synthetic demonstration to field-validated inspection prioritization.")
    demo, rollout, deployment = st.tabs(["Guided Demo", "Real-world Rollout", "Deployment Readiness"])

    with demo:
        st.markdown("### Five-minute judge walkthrough")
        st.info("Lead with the problem and inspection workflow. Do not lead with model accuracy.")
        steps = [
            ("1 · Frame the problem", "Utilities cannot economically place sensors on every pipe. AquaGuard prioritizes zones using strategic flow, pressure, and consumption measurements."),
            ("2 · Show the network", "Open City Overview and move the inspection hour to 24 Jan 2026, 20:00 to reveal the sustained Z18 event."),
            ("3 · Explain the evidence", "Open Zone Intelligence for Z18. Compare supplied 15-minute flow volume with consumption, then inspect pressure and persistence."),
            ("4 · Demonstrate interaction", "Use the Command Center What-if Scenario Lab. Enter high flow, low consumption, low pressure, and sustained readings."),
            ("5 · Close honestly", "Show Model Validation, explain synthetic precision/recall, and propose a controlled utility pilot with human confirmation."),
        ]
        for title, body in steps:
            st.markdown(f"**{title}**")
            st.write(body)
        cols = st.columns(3)
        with cols[0]: metric_card("Demo event", "Z18", "24 Jan 2026 · 20:00", "HIGH RISK")
        with cols[1]: metric_card("Synthetic coverage", "6/6 events", "At least one model flag per event", "NORMAL")
        with cols[2]: metric_card("Core message", "Prioritize", "An inspection aid—not automatic diagnosis")
        st.markdown("#### Suggested what-if inputs")
        st.code("Flow rate: 250 m³/h\nConsumption: 15 m³ / 15 min\nPressure: 30 m head\nPersistence: 8 of 8 readings")

    with rollout:
        st.markdown("### Start small, validate in the field, then expand")
        phases = st.columns(4)
        phase_content = [
            ("1 · Instrument", "5–10 pilot DMAs", "Connect inlet flow, strategic pressure, and available consumption data."),
            ("2 · Baseline", "8–12 weeks", "Validate units, sensor health, time alignment, and zone-specific daily patterns."),
            ("3 · Shadow pilot", "3–6 months", "Generate recommendations alongside existing operations; require engineer review."),
            ("4 · Scale", "Evidence-led", "Expand only after measuring useful findings, false inspections, response time, and water saved."),
        ]
        for column, (title, value, body) in zip(phases, phase_content):
            with column:
                metric_card(title, value, body)
        st.markdown("### Minimum field architecture")
        st.markdown("**Strategic sensors** → **utility telemetry/SCADA** → **quality checks** → **zone baselines** → **anomaly and risk engine** → **control-room review** → **field inspection** → **confirmed-outcome feedback**")
        st.warning("Possible causes include leakage, authorized demand, firefighting, maintenance, valve changes, meter faults, and sensor drift. Human confirmation remains mandatory.")
        st.markdown("### Pilot success measures")
        st.write("Useful finding rate · unnecessary inspection rate · time to investigation · estimated water saved · sensor availability · staff time saved")

    with deployment:
        st.markdown("### Current readiness")
        checks = st.columns(4)
        with checks[0]: metric_card("Entrypoint", "app.py", "Single Streamlit application", "NORMAL")
        with checks[1]: metric_card("Dependencies", "Declared", "requirements.txt", "NORMAL")
        with checks[2]: metric_card("Secrets", "None", "No external APIs or credentials", "NORMAL")
        with checks[3]: metric_card("Data", "Bundled", "Synthetic CSV and validation JSON", "NORMAL")
        st.markdown("### Recommended hackathon deployment")
        st.write("Push the AquaGuard folder to a GitHub repository, connect that repository in Streamlit Community Cloud, and select `app.py` as the entrypoint. Deploy only after confirming the repository contains no private utility or customer data.")
        st.markdown("### Production gaps")
        st.write("Authentication · encrypted telemetry · database/storage design · sensor-health monitoring · audit logs · alert ownership · backups · data retention · privacy review · model monitoring")
        st.info("Stage 4 prepares deployment but does not publish the application or connect external accounts.")
