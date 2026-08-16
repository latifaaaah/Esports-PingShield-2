"""Scenario simulation and health-classification engine.

Two responsibilities live here and nowhere else:
1. process_scenario() turns (scenario, selected zones) into a
   telemetry DataFrame, including a small per-tick random walk so
   auto-refresh produces a genuinely live-looking feed instead of a
   frozen snapshot behind a "LIVE" badge.
2. classify_status() is the single place that decides
   HEALTHY / WARNING / CRITICAL / UNREACHABLE. ui.py and app.py both
   read the resulting "status" column rather than re-deriving their
   own ping/loss thresholds, so the two layers can't disagree about
   what counts as a problem.
"""

from __future__ import annotations

import math
import random

import pandas as pd

from src.config import (
    BASE_DEVICES,
    DISASTER_SCENARIOS,
    NOISE_JITTER_PCT,
    NOISE_LOSS_ABS_PCT,
    NOISE_PING_PCT,
    SEVERITY_RANK,
    STATUS_CRITICAL,
    STATUS_HEALTHY,
    STATUS_UNREACHABLE,
    STATUS_WARNING,
    THRESHOLDS,
)

TELEMETRY_COLUMNS = ["id", "zone", "ping", "jitter", "loss", "status"]


class ScenarioError(Exception):
    """Raised when process_scenario receives an unknown scenario key."""


def _noisy(value: float | None, pct: float) -> float | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    delta = max(value, 0.01) * pct
    return round(max(0.0, value + random.uniform(-delta, delta)), 2)


def classify_status(ping: float | None, loss: float) -> str:
    """Classify a single device reading into a severity status.

    A fully dropped link (loss >= 100%, or no ping reading at all) is
    UNREACHABLE — a distinct, worse category than CRITICAL, since
    "very slow" and "not there" call for different operational
    responses.
    """
    if loss >= 100.0 or ping is None:
        return STATUS_UNREACHABLE
    if ping >= THRESHOLDS["ping_critical_ms"] or loss >= THRESHOLDS["loss_critical_pct"]:
        return STATUS_CRITICAL
    if ping >= THRESHOLDS["ping_warning_ms"] or loss >= THRESHOLDS["loss_warning_pct"]:
        return STATUS_WARNING
    return STATUS_HEALTHY


def worst_status(statuses: list[str]) -> str:
    """Return the highest-severity status in a list, defaulting to HEALTHY."""
    if not statuses:
        return STATUS_HEALTHY
    return max(statuses, key=lambda s: SEVERITY_RANK[s])


def _apply_scenario(device: dict, scenario_key: str) -> tuple[float | None, float | None, float]:
    """Return (ping, jitter, loss) for one device under the given scenario,
    before per-tick noise is applied."""
    ping, jitter, loss = device["base_ping"], device["base_jitter"], device["base_loss"]

    if scenario_key == "SERVER_DDOS" and device["id"] == "GAME-SERVER-PRIMARY":
        ping, jitter, loss = 145.0, 32.0, 12.5
    elif scenario_key == "STAGE_SWITCH_FAIL" and device["zone"] == "Stage Right":
        # A severed switch means no readable ping or jitter at all --
        # not "0 jitter", which would misleadingly imply a perfectly
        # stable (nonexistent) connection.
        ping, jitter, loss = None, None, 100.0
    elif scenario_key == "STREAM_PACKET_LOSS" and device["id"] == "OBS-BROADCAST-01":
        ping, jitter, loss = 48.0, 18.5, 4.2
    elif scenario_key == "TOTAL_CONGESTION":
        ping = ping + 35.0
        jitter = jitter + 4.0
        loss = loss + 2.5

    return ping, jitter, loss


def process_scenario(scenario_key: str, selected_zones: list[str]) -> pd.DataFrame:
    """Produce one telemetry snapshot for the given scenario and zone filter.

    Raises ScenarioError on an unrecognised scenario key so a typo or
    a stale caller fails loudly instead of silently rendering the
    "Normal Operations" baseline.
    """
    if scenario_key not in DISASTER_SCENARIOS:
        raise ScenarioError(f"Unknown scenario key: {scenario_key!r}")

    devices = [d for d in BASE_DEVICES if d["zone"] in selected_zones]
    if not devices:
        return pd.DataFrame(columns=TELEMETRY_COLUMNS)

    rows = []
    for device in devices:
        ping, jitter, loss = _apply_scenario(device, scenario_key)

        ping = _noisy(ping, NOISE_PING_PCT)
        jitter = _noisy(jitter, NOISE_JITTER_PCT)
        if loss < 100.0:
            loss = round(max(0.0, loss + random.uniform(-NOISE_LOSS_ABS_PCT, NOISE_LOSS_ABS_PCT)), 2)

        status = classify_status(ping, loss)
        rows.append(
            {
                "id": device["id"],
                "zone": device["zone"],
                "ping": ping,
                "jitter": jitter,
                "loss": loss,
                "status": status,
            }
        )

    return pd.DataFrame(rows, columns=TELEMETRY_COLUMNS)
