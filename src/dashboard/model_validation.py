"""Validation against documented controlled hydrant tests."""

import streamlit as st

from dashboard.components import metric_card, page_header


def render_model_validation(report: dict | None) -> None:
    page_header("Controlled-Test Validation", "Model Validation",
                "Evaluation against documented leak-test periods in one public field dataset.")
    st.warning("These results are from one experimental DMA with controlled hydrant tests. They are not city-wide or production leak-detection accuracy.")
    if report is None:
        st.error("The validation report is missing. Run `python src/run_pipeline.py`, then refresh.")
        return

    top = st.columns(4)
    with top[0]: metric_card("Hourly observations", f"{report['total_hourly_observations']:,}", "September 2023 field data")
    with top[1]: metric_card("Controlled-test hours", f"{report['controlled_test_hours']:,}", "Hours overlapping documented tests")
    with top[2]: metric_card("Model flags", f"{report['isolation_forest_anomalies']:,}", "Isolation Forest observations")
    with top[3]: metric_card("Test hours flagged", f"{report['controlled_test_hours_flagged']:,}", "Direct hourly overlap", "MONITOR")

    scores = st.columns(4)
    with scores[0]: metric_card("Precision", f"{report['precision']:.1%}", "Flags overlapping controlled-test hours")
    with scores[1]: metric_card("Recall", f"{report['recall']:.1%}", "Controlled-test hours model flagged")
    with scores[2]: metric_card("F1", f"{report['f1']:.1%}", "Precision/recall balance")
    with scores[3]: metric_card("Test coverage", f"{report['tests_detected_by_isolation_forest']}/{report['total_controlled_leak_tests']}", "Tests with at least one model flag")

    st.markdown("### Honest interpretation")
    st.write(
        "Isolation Forest alone detected only a small share of these short controlled tests after the source was aggregated to hourly intervals. "
        "The transparent risk rules identified more tests as MONITOR or HIGH RISK, but this remains an exploratory result. "
        "The low model metrics are retained rather than hidden or replaced with fabricated accuracy."
    )
    st.markdown("### Controlled leak-test coverage")
    st.dataframe(report["event_details"], hide_index=True, width="stretch")
    st.info("AquaGuard prioritizes unusual measurements for human review. A flag does not confirm a physical leak or unauthorized consumption.")
