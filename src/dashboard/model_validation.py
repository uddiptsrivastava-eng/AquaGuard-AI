"""Synthetic validation results page."""

import streamlit as st

from dashboard.components import metric_card, page_header


def render_model_validation(report: dict | None) -> None:
    page_header("Synthetic Prototype Validation", "Model Validation", "Transparent evaluation against deliberately injected patterns.")
    st.warning("These metrics are measured against deliberately injected synthetic anomaly patterns and must not be interpreted as real-world leak-detection accuracy.")
    if report is None:
        st.error("The validation report is missing. Run `python src/run_pipeline.py`, then refresh this page.")
        return

    top = st.columns(4)
    with top[0]: metric_card("Known anomalies", f"{report['known_anomalous_readings']:,}", "Injected synthetic readings")
    with top[1]: metric_card("Model flags", f"{report['isolation_forest_anomalies']:,}", "Isolation Forest observations")
    with top[2]: metric_card("Known detected", f"{report['known_anomalous_readings_flagged_by_isolation_forest']:,}", "Matched injected readings", "NORMAL")
    with top[3]: metric_card("Normal flagged", f"{report['normal_readings_incorrectly_flagged_by_isolation_forest']:,}", "False-positive inspection candidates", "MONITOR")

    scores = st.columns(4)
    with scores[0]: metric_card("Synthetic precision", f"{report['precision']:.1%}", "Share of flags matching injected anomalies")
    with scores[1]: metric_card("Synthetic recall", f"{report['recall']:.1%}", "Share of injected readings detected")
    with scores[2]: metric_card("Synthetic F1", f"{report['f1']:.1%}", "Balance of precision and recall")
    with scores[3]: metric_card("Event detection", f"{report['events_detected_by_isolation_forest']}/{report['total_anomaly_events']}", "Events with at least one model flag", "NORMAL")

    st.markdown("### How to read these results")
    columns = st.columns(3)
    with columns[0]:
        st.markdown("**PRECISION**")
        st.write("Of the readings the model flagged, how many matched an injected synthetic anomaly.")
    with columns[1]:
        st.markdown("**RECALL**")
        st.write("Of all deliberately injected anomaly readings, how many the model detected.")
    with columns[2]:
        st.markdown("**EVENT DETECTION**")
        st.write("Whether AquaGuard found at least one reading within each simulated abnormal event.")

    st.markdown("### Synthetic event coverage")
    st.dataframe(report["event_details"], hide_index=True, width="stretch")
    st.info("AquaGuard is designed to prioritize zones and incidents for inspection. A flag is evidence of unusual behaviour—not proof of leakage or unauthorized consumption.")
