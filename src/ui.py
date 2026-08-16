"""UI styling components, metric cards, topology grid, and charts.

Rendering only -- no thresholds and no status logic live in this
file. Every color/badge decision reads the "status" column that
engine.classify_status() already computed, so this file can never
disagree with engine.py about what counts as a problem.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.config import DEVICES_BY_ZONE, STATUS_CRITICAL, STATUS_HEALTHY, STATUS_UNREACHABLE, STATUS_WARNING, THRESHOLDS
from src.engine import worst_status

_BADGE_CLASS = {
    STATUS_HEALTHY: "badge-healthy",
    STATUS_WARNING: "badge-warning",
    STATUS_CRITICAL: "badge-critical",
    STATUS_UNREACHABLE: "badge-unreachable",
}


def apply_custom_css() -> None:
    st.markdown(
        """
    <style>
        .stApp { background-color: #090d16; color: #e2e8f0; }
        .main-header {
            background: linear-gradient(135deg, #0f172a, #1e293b);
            border-left: 5px solid #00f2fe;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .live-badge {
            background: #0284c7 !important; color: white !important;
            padding: 4px 12px !important; border-radius: 20px !important;
            font-size: 11px !important; font-weight: bold !important;
        }
        .metric-card {
            background: #0f172a !important;
            border: 1px solid #1e293b !important;
            border-radius: 10px !important;
            padding: 15px !important;
            text-align: center !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
        }
        .metric-label { font-size: 13px !important; color: #94a3b8 !important; font-weight: 600 !important; margin-bottom: 5px !important; }
        .metric-value { font-size: 26px !important; font-weight: 700 !important; }
        .metric-green { color: #10b981 !important; }
        .metric-amber { color: #f59e0b !important; }
        .metric-red { color: #ef4444 !important; }

        .topo-card {
            background: #0f172a !important;
            border: 1px solid #1e293b !important;
            border-radius: 8px !important;
            padding: 12px 15px !important;
            margin-bottom: 10px !important;
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
        }
        .topo-title { font-weight: bold !important; font-size: 15px !important; color: #ffffff !important; }
        .topo-devices { font-size: 11px !important; color: #64748b !important; margin-top: 3px !important; }
        .badge-healthy { color: #10b981 !important; font-weight: bold !important; font-size: 12px !important; }
        .badge-warning { color: #f59e0b !important; font-weight: bold !important; font-size: 12px !important; }
        .badge-critical { color: #ef4444 !important; font-weight: bold !important; font-size: 12px !important; }
        .badge-unreachable { color: #94a3b8 !important; font-weight: bold !important; font-size: 12px !important; }

        .playbook-card {
            background: rgba(239, 68, 68, 0.08) !important;
            border: 1px solid #ef4444 !important;
            border-radius: 10px !important;
            padding: 20px !important;
            margin-top: 20px !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def _fmt_ping(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.1f}"


def render_kpi_cards(df: pd.DataFrame) -> None:
    if df.empty:
        avg_ping, max_loss, degraded, unreachable = None, 0.0, 0, 0
    else:
        avg_ping = df["ping"].mean(skipna=True)
        avg_ping = None if pd.isna(avg_ping) else avg_ping
        max_loss = round(df["loss"].max(), 1)
        degraded = int((df["status"] == STATUS_CRITICAL).sum())
        unreachable = int((df["status"] == STATUS_UNREACHABLE).sum())

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">ACTIVE ARENA ENDPOINTS</div>
            <div class="metric-value metric-green">{len(df)}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        if avg_ping is None:
            ping_color, ping_display = "metric-red", "N/A"
        else:
            ping_color = "metric-red" if avg_ping > THRESHOLDS["ping_warning_ms"] else "metric-green"
            ping_display = f"{avg_ping:.2f} <span style='font-size:14px;'>ms</span>"
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">MEAN ARENA LATENCY</div>
            <div class="metric-value {ping_color}">{ping_display}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        status_color = "metric-red" if (degraded + unreachable) > 0 else "metric-green"
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">DEGRADED / CRITICAL ENDPOINTS</div>
            <div class="metric-value {status_color}">{degraded + unreachable}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        loss_color = "metric-red" if max_loss > THRESHOLDS["loss_warning_pct"] else "metric-green"
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">MAX PACKET LOSS</div>
            <div class="metric-value {loss_color}">{max_loss}%</div>
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_topology_grid(df: pd.DataFrame) -> None:
    st.subheader("Arena Topology Grid")

    for zone, device_ids in DEVICES_BY_ZONE.items():
        zone_df = df[df["zone"] == zone] if not df.empty else pd.DataFrame()
        status = worst_status(list(zone_df["status"])) if not zone_df.empty else STATUS_HEALTHY
        badge_class = _BADGE_CLASS[status]

        st.markdown(
            f"""
        <div class="topo-card">
            <div>
                <div class="topo-title">{zone}</div>
                <div class="topo-devices">Devices: {", ".join(device_ids)}</div>
            </div>
            <div class="{badge_class}">{status}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )


_STATUS_COLOR = {
    STATUS_HEALTHY: "#10b981",
    STATUS_WARNING: "#f59e0b",
    STATUS_CRITICAL: "#ef4444",
    STATUS_UNREACHABLE: "#64748b",
}


def render_latency_chart(df: pd.DataFrame) -> None:
    st.subheader("Endpoint Latency & Jitter Breakdown")

    if df.empty:
        st.info("No endpoints selected.")
        return

    colors = [_STATUS_COLOR[s] for s in df["status"]]
    critical_ceiling = THRESHOLDS["ping_critical_ms"] * 2

    # UNREACHABLE devices have no numeric ping (None) -- give the bar
    # a fixed sentinel height so it still renders, but label it
    # "OFFLINE" rather than a fabricated number.
    plot_ping = df["ping"].fillna(critical_ceiling)
    labels = [
        "OFFLINE" if pd.isna(p) else f"{p:.1f}" for p in df["ping"]
    ]

    fig = go.Figure(
        go.Bar(x=df["id"], y=plot_ping, marker_color=colors, text=labels, textposition="outside")
    )
    fig.add_hline(
        y=THRESHOLDS["ping_critical_ms"],
        line_dash="dot",
        line_color="#ef4444",
        annotation_text="Critical",
        annotation_position="top right",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff"),
        height=340,
        yaxis_title="Latency (ms)",
        margin=dict(l=10, r=10, t=30, b=10),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
