"""AquaGuard AI Streamlit dashboard entry point."""

import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dashboard.alerts import render_alerts  # noqa: E402
from dashboard.command_center import render_command_center  # noqa: E402
from dashboard.city_overview import render_city_overview  # noqa: E402
from dashboard.components import (  # noqa: E402
    PROCESSED_DATA_PATH, VALIDATION_PATH, apply_theme, load_processed_data,
    load_validation, render_sidebar_context,
)
from dashboard.model_validation import render_model_validation  # noqa: E402
from dashboard.network_map import render_network_map  # noqa: E402
from dashboard.zone_intelligence import render_zone_intelligence  # noqa: E402


st.set_page_config(page_title="AquaGuard AI", page_icon="💧", layout="wide", initial_sidebar_state="expanded")
apply_theme()

if not PROCESSED_DATA_PATH.exists():
    st.error("The processed dataset is missing. Run `python src/run_pipeline.py` from the AquaGuard folder, then refresh.")
    st.stop()

try:
    data = load_processed_data(PROCESSED_DATA_PATH)
except Exception as error:
    st.error(f"The processed dataset could not be loaded: {error}")
    st.stop()

validation = None
if VALIDATION_PATH.exists():
    try:
        validation = load_validation(VALIDATION_PATH)
    except Exception as error:
        st.sidebar.warning(f"Validation summary unavailable: {error}")

page = render_sidebar_context(data)
pages = {
    "Command Center": render_command_center,
    "Meter Sites": render_city_overview,
    "Network Map": render_network_map,
    "DMA Intelligence": render_zone_intelligence,
    "Alerts": render_alerts,
    "Model Validation": render_model_validation,
}
pages[page](validation if page == "Model Validation" else data)
