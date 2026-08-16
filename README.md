# Esports-PingShield Operations Center

A simulated network-operations dashboard for an esports LAN arena: live
endpoint latency/jitter/packet-loss monitoring, zone-level topology status,
and an automated incident-mitigation playbook -- built with Streamlit.

**This is a simulation environment.** Telemetry is generated locally with a
small per-tick random walk to produce a genuinely live-looking feed. No real
network devices, switches, or tournament traffic are involved -- the sidebar
says so explicitly, and the "LIVE SIMULATED TELEMETRY" badge is accurate to
what the app actually does rather than an unqualified "LIVE" claim over
static numbers.

## Architecture

```
app.py               # entrypoint: sidebar controls, auto-refresh fragment
requirements.txt
src/
    __init__.py
    config.py          # single source of truth: devices, zones, thresholds, scenarios
    engine.py          # scenario simulation + classify_status() + worst_status()
    ui.py              # Streamlit rendering only -- reads engine's status column
tests/
    __init__.py
    test_config.py      # consistency guarantees (zones/devices can't drift apart)
    test_engine.py       # scenario correctness + status classification
```

## What changed from the first draft, and why

- **One classify_status() function.** Previously the `ping > 30` threshold
  was hardcoded in four different places (`engine.py`, and three spots across
  `ui.py`/`app.py`) that had to be kept in sync by hand. Now every layer reads
  `engine.classify_status()` and the `status` column it produces -- change
  the threshold once in `config.py` and every view updates together.
- **Scenario dispatch by key, not by substring-matching a label string.**
  `"Scenario A" in scenario_name` breaks the moment the label text changes.
  `app.py` now passes the stable dict key (`"SERVER_DDOS"`, etc.) straight
  through to `engine.py`.
- **Zone -> device mapping is derived, not duplicated.** `ui.py` used to hold
  its own hand-typed copy of which device IDs belong to which zone, separate
  from `config.BASE_DEVICES`. `DEVICES_BY_ZONE` is now built once from
  `BASE_DEVICES` in `config.py`, so it can't drift out of sync.
- **A severed link is UNREACHABLE, not "0.0 jitter".** The Stage Right
  switch-failure scenario previously reported `jitter = 0.0` for a fully
  down link, which reads as "perfectly stable" rather than "not there."
  It's now a distinct `UNREACHABLE` status with `ping`/`jitter` reported as
  genuinely missing (`None` / "N/A" / "OFFLINE" in the chart), ranked worse
  than `CRITICAL` by `worst_status()`.
- **The "LIVE" badge is now true.** The dashboard previously rendered a
  static snapshot once per widget interaction behind a "LIVE TOURNAMENT
  FEED" label. `st.fragment(run_every=refresh_rate)` now reruns the
  dashboard on an interval with real per-tick noise, and the badge text was
  changed to make clear it's simulated telemetry, not real match traffic.
- **Error handling.** `process_scenario()` raises a typed `ScenarioError` on
  an unrecognised scenario key, caught at the UI boundary and shown via
  `st.error` instead of crashing the whole app or silently rendering the
  wrong scenario.
- **Tests.** 23 unit tests across `test_config.py` and `test_engine.py`,
  including regression tests for the exact two bugs above (threshold
  duplication and the zero-jitter-on-a-dead-link inconsistency).

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Running tests

```bash
pip install -r requirements.txt
pytest -v
```

`engine.py` and `config.py` import nothing from Streamlit, so the test suite
runs without a Streamlit runtime.

## Deploying to Streamlit Cloud

**Push with `git push` (from a real git checkout) or GitHub Desktop --
not the web "Add file > Upload files" drag-and-drop button.** The web
uploader has a known failure mode where nested folders (like `src/`) get
flattened or dropped silently, which produces exactly
`ModuleNotFoundError: No module named 'src'` at runtime even though every
file compiled fine locally.

Correct sequence:

```bash
git init
git add .
git commit -m "Esports-PingShield operations dashboard"
git branch -M main
git remote add origin <your-empty-github-repo-url>
git push -u origin main
```

Then on [share.streamlit.io](https://share.streamlit.io), point the app at
`app.py` in the repo root. Before deploying, open the repo on GitHub's file
browser and confirm you can see `src/config.py`, `src/engine.py`, and
`src/ui.py` as actual files inside a real `src` folder -- if the file tree
shows `src` as a folder icon you can click into, the push worked correctly.

`app.py` also inserts its own directory onto `sys.path` at startup as a
defensive measure against working-directory differences -- but that only
helps if `src/` actually exists in the deployed repo; it can't recover a
folder that never made it into the push.
