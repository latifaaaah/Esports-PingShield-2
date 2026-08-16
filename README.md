# \u26a1 Esports-PingShield

**Enterprise-style network operations dashboard for esports LAN arena infrastructure.**
Real-time endpoint monitoring, zone-level topology health, automated incident
detection, and a scripted mitigation playbook -- built with Streamlit.

> Simulation environment: telemetry is generated locally with a live per-tick
> random walk to model realistic network behavior. No physical network
> hardware or live tournament traffic is involved.

---

## Overview

Esports-PingShield models the network operations layer of a competitive
gaming arena: player stations, a broadcast production booth, and a redundant
game-server rack, each streaming latency, jitter, and packet-loss telemetry.
An operator can inject one of several disaster scenarios (DDoS on the
primary game server, a severed stage switch, broadcast packet loss, arena-wide
congestion) and watch the dashboard classify affected endpoints, escalate
zone status, and surface a recommended incident-response runbook in real time.

## Features

- **Live telemetry feed** -- auto-refreshing dashboard with configurable
  refresh rate, driven by `st.fragment`, not a blocking sleep loop.
- **Deterministic health classification** -- every endpoint is scored
  `HEALTHY` / `WARNING` / `CRITICAL` / `UNREACHABLE` from a single set of
  latency and packet-loss thresholds.
- **Zone-level topology view** -- Stage Left, Stage Right, Production Booth,
  and Server Rack each roll up to their worst-case endpoint status.
- **Scenario injector** -- four disaster scenarios plus a normal-operations
  baseline, selectable from the sidebar.
- **Automated mitigation playbook** -- active incidents trigger a scripted
  SOP with affected systems and required operational actions.
- **Full telemetry table** -- per-endpoint ping, jitter, and packet loss for
  every reporting cycle.

## Architecture

```
app.py               entrypoint -- sidebar controls, auto-refresh fragment
src/
    config.py          device topology, zones, thresholds, scenario definitions
    engine.py           scenario simulation, health classification
    ui.py               Streamlit rendering components
tests/
    test_config.py       topology and threshold consistency checks
    test_engine.py        scenario and classification correctness
```

The system is built around a single-source-of-truth principle: device
topology, zone membership, and severity thresholds are all defined once in
`config.py`. The classification engine (`engine.py`) is the only place that
turns raw metrics into a status, and every rendering component consumes that
status rather than re-deriving its own thresholds -- so the topology grid,
the KPI cards, and the latency chart can never disagree with each other about
what counts as a problem.

A fully severed link is modeled as a distinct `UNREACHABLE` state rather than
a zero-value reading, since a dropped connection and a merely slow one call
for different operational responses.

## Tech Stack

- **Streamlit** -- application framework and UI
- **Pandas** -- telemetry data handling
- **Plotly** -- latency visualization
- **Pytest** -- unit testing

## Getting Started

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Testing

```bash
pytest -v
```

Business logic (`src/config.py`, `src/engine.py`) has no dependency on
Streamlit, so the full test suite runs independently of the UI layer.

## Target Roles

This project was built to demonstrate operational monitoring, incident
classification, and network-fault simulation relevant to:

- Network Operations Engineer
- Network Engineer
- Technical Operations Engineer
- Network Security Engineer
- Esports / Event Technology Engineer

## License

MIT
