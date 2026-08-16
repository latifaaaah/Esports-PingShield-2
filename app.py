"""Esports-PingShield Enterprise Dashboard -- main application."""

import sys
from pathlib import Path

# Defensive path guard: makes sure the repo root (this file's folder)
# is importable as a package root even if Streamlit Cloud's working
# directory ever differs from the repo root. This does NOT fix a
# missing src/ folder in the repo itself -- see the deployment note
# in README.md for that.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from src.config import (
    DEFAULT_REFRESH,
    DISASTER_SCENARIOS,
    REFRESH_MAX,
    REFRESH_MIN,
    STATUS_CRITICAL,
    STATUS_UNREACHABLE,
    ZONES,
)
from src.engine import ScenarioError, process_scenario
from src.ui import apply_custom_css, render_kpi_cards, render_latency_chart, render_topology_grid

st.set_page_config(page_title="Esports-PingShield Operations Center", page_icon="\U0001f3ae", layout="wide")
apply_custom_css()

# --- Sidebar -------------------------------------------------------------
with st.sidebar:
    st.title("Incident Injector")
    st.caption("Simulate real tournament network failures to test mitigation protocols.")

    scenario_key = st.selectbox(
        "Select Disaster Scenario",
        options=list(DISASTER_SCENARIOS.keys()),
        format_func=lambda key: DISASTER_SCENARIOS[key],
    )

    st.subheader("Operational Filters")
    selected_zones = st.multiselect("Filter Arena Zones", ZONES, default=ZONES)

    st.subheader("Live Feed Controls")
    refresh_rate = st.slider("Telemetry Refresh Rate (sec)", REFRESH_MIN, REFRESH_MAX, DEFAULT_REFRESH)
    auto_refresh = st.toggle("Auto Refresh", value=True)

    st.divider()
    st.caption(
        "\U0001f6f0\ufe0f Simulated telemetry only. No real network devices, "
        "switches, or live tournament traffic are involved."
    )


@st.fragment(run_every=refresh_rate if auto_refresh else None)
def render_dashboard(active_scenario_key: str, active_zones: list[str]) -> None:
    """Fragment-scoped render: only this block reruns on auto-refresh.

    st.fragment(run_every=...) reruns just this function on the given
    interval instead of blocking the whole script with time.sleep() +
    st.rerun() -- so the "LIVE" badge below is actually backed by data
    that moves, not a static snapshot sitting behind a live-sounding label.
    """
    try:
        df = process_scenario(active_scenario_key, active_zones)
    except ScenarioError as exc:
        st.error(f"Simulation error: {exc}")
        return

    critical_df = df[df["status"].isin([STATUS_CRITICAL, STATUS_UNREACHABLE])] if not df.empty else df

    st.markdown(
        """
    <div class="main-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 style="margin:0; font-size:26px;">Esports-PingShield | Enterprise Operations Center</h1>
                <p style="margin:0; color:#94a3b8; font-size:13px;">LAN Arena Infrastructure Health & Real-Time Incident Response Protocol</p>
            </div>
            <div class="live-badge">\u25cf LIVE SIMULATED TELEMETRY</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    render_kpi_cards(df)
    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1.3])
    with col_left:
        render_topology_grid(df)
    with col_right:
        render_latency_chart(df)

    if not critical_df.empty:
        affected_ids = ", ".join(critical_df["id"].tolist())
        st.markdown(
            f"""
        <div class="playbook-card">
            <h3 style="color:#ef4444; margin-top:0;">Automated Incident Mitigation Playbook (SOP-09)</h3>
            <p><strong>Affected System(s):</strong> {affected_ids}</p>
            <p><strong>Root Cause Analysis:</strong> High ping/packet loss or link-down anomaly detected on active match infrastructure.</p>
            <p><strong>Required Operational Actions:</strong></p>
            <ol style="margin-bottom:0;">
                <li>Execute failover commands or inspect physical switch connections in the designated zone.</li>
                <li>Verify redundant SFP+ fiber link integrity and reroute traffic immediately.</li>
            </ol>
        </div>
        """,
            unsafe_allow_html=True,
        )
    elif df.empty:
        st.info("No arena zones selected -- choose at least one zone in the sidebar to see telemetry.")
    else:
        st.success("All network endpoints operating within tournament specification. Zero active incidents.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Full Infrastructure Telemetry")
    st.dataframe(df, use_container_width=True)


render_dashboard(scenario_key, selected_zones)
