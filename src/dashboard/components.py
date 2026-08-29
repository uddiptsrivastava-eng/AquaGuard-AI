"""Shared data, styling, and UI helpers for the AquaGuard dashboard."""

import json
from datetime import timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed_water_network.csv"
VALIDATION_PATH = PROJECT_ROOT / "data" / "synthetic_validation.json"
STATUS_COLORS = {"NORMAL": "#2dd4a8", "MONITOR": "#f4bf4f", "HIGH RISK": "#f16464"}
PAGE_NAMES = ["Command Center", "City Overview", "Network Map", "Zone Intelligence", "Alerts", "Model Validation"]
TIME_WINDOWS = {
    "Last 24 hours": timedelta(hours=24), "Last 3 days": timedelta(days=3),
    "Last 7 days": timedelta(days=7), "All available data": None,
}


@st.cache_data(show_spinner="Loading network observations…")
def load_processed_data(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path, parse_dates=["timestamp"])
    required = {
        "timestamp", "zone_id", "flow_m3_per_hour", "flow_volume_m3", "consumption_m3",
        "pressure_m_head", "unaccounted_water_m3", "unaccounted_water_pct",
        "flow_deviation_pct", "consumption_deviation_pct", "pressure_deviation_pct",
        "risk_score", "risk_category", "explanation",
    }
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"required columns are missing: {sorted(missing)}")
    if data["timestamp"].isna().any():
        raise ValueError("one or more timestamps are invalid")
    return data.sort_values(["timestamp", "zone_id"], ignore_index=True)


@st.cache_data(show_spinner=False)
def load_validation(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def latest_by_zone(data: pd.DataFrame) -> pd.DataFrame:
    return data.sort_values("timestamp").groupby("zone_id", as_index=False).tail(1).sort_values("zone_id")


def filter_time_window(data: pd.DataFrame, label: str) -> pd.DataFrame:
    duration = TIME_WINDOWS[label]
    if duration is None or data.empty:
        return data
    return data.loc[data["timestamp"] >= data["timestamp"].max() - duration]


def render_sidebar_context(data: pd.DataFrame) -> str:
    st.sidebar.markdown('<div class="side-brand">AquaGuard <span>AI</span></div>', unsafe_allow_html=True)
    st.sidebar.caption("Urban Water Intelligence Platform")
    page = st.sidebar.radio("Navigation", PAGE_NAMES, label_visibility="collapsed")
    st.sidebar.divider()
    st.sidebar.markdown("**CURRENT DATASET**")
    st.sidebar.caption("Synthetic 30-day urban network simulation")
    left, right = st.sidebar.columns(2)
    left.metric("Zones", f"{data['zone_id'].nunique():,}")
    right.metric("Observations", f"{len(data):,}")
    st.sidebar.divider()
    st.sidebar.caption("AI ENGINE")
    st.sidebar.markdown("**Isolation Forest**")
    st.sidebar.caption("RISK ENGINE")
    st.sidebar.markdown("**AquaGuard Prototype Score**")
    st.sidebar.info("Prototype · Synthetic Data", icon="ℹ️")
    return page


def page_header(title: str, eyebrow: str, description: str) -> None:
    st.markdown(f'<div class="eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.title(title)
    st.caption(description)


def metric_card(label: str, value: str, detail: str = "", status: str | None = None) -> None:
    color = STATUS_COLORS.get(status or "", "#6dc7e8")
    st.markdown(
        f'<div class="metric-card" style="--accent:{color}"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-detail">{detail}</div></div>',
        unsafe_allow_html=True,
    )


def chart_style(figure: go.Figure, height: int = 330) -> go.Figure:
    figure.update_layout(
        height=height, margin=dict(l=18, r=18, t=45, b=20), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(7,17,27,0.35)", font=dict(color="#dce8f1", family="Inter, Segoe UI, sans-serif"),
        legend=dict(orientation="h", y=1.12, x=0), hoverlabel=dict(bgcolor="#122230", font_color="#f4f8fb"),
    )
    figure.update_xaxes(gridcolor="rgba(150,180,200,0.10)", zeroline=False)
    figure.update_yaxes(gridcolor="rgba(150,180,200,0.10)", zeroline=False)
    return figure


def apply_theme() -> None:
    st.markdown("""<style>
    :root{--border:#1b3344}.stApp{background:radial-gradient(circle at 80% 0%,#102b39 0,#07111b 34%,#050c13 100%);color:#eaf2f7}
    html,body,[class*="css"]{font-family:'Segoe UI',Arial,sans-serif}[data-testid="stSidebar"]{background:#08131d;border-right:1px solid var(--border)}
    [data-testid="stSidebar"] [data-testid="stMetric"]{background:#0c1a26;border:1px solid var(--border);padding:.55rem;border-radius:10px}
    [data-testid="stSidebar"] [data-testid="stMetricValue"]{font-size:1.15rem}.block-container{padding-top:2.2rem;padding-bottom:4rem;max-width:1500px}
    h1{letter-spacing:-.045em;font-weight:700!important}h2,h3{letter-spacing:-.025em}.side-brand{font-size:1.45rem;font-weight:700;letter-spacing:-.04em;padding-top:.3rem}.side-brand span{color:#62c8e8}
    .eyebrow{color:#62c8e8;font-size:.74rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;margin-bottom:-.5rem}
    .metric-card{background:linear-gradient(145deg,rgba(16,35,48,.96),rgba(9,23,34,.96));border:1px solid var(--border);border-top:2px solid var(--accent);border-radius:14px;padding:1rem 1.05rem;min-height:132px;box-shadow:0 12px 35px rgba(0,0,0,.16)}
    .metric-label{color:#9eb3c1;font-size:.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase}.metric-value{color:#f4f8fb;font-size:1.72rem;font-weight:700;margin:.35rem 0}.metric-detail{color:#7892a3;font-size:.78rem;line-height:1.35}
    [data-testid="stDataFrame"]{border:1px solid var(--border);border-radius:12px;overflow:hidden}[data-testid="stPlotlyChart"]{background:rgba(12,26,38,.75);border:1px solid var(--border);border-radius:14px;padding:.25rem}
    .alert-card{background:rgba(12,26,38,.85);border:1px solid var(--border);border-left:3px solid #f16464;border-radius:10px;padding:.8rem 1rem;margin:.45rem 0}.alert-card strong{color:#f5f8fa}.alert-card small{color:#89a3b5}
    </style>""", unsafe_allow_html=True)
