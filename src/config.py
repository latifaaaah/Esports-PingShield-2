"""Configuration constants, thresholds, and disaster scenarios for Esports-PingShield.

Every other module reads device topology and threshold values from
here. Keeping them in one place is what lets engine.py and ui.py stay
in agreement about what counts as HEALTHY/WARNING/CRITICAL instead of
each recomputing its own copy of the same magic number.
"""

# --- Disaster scenarios ------------------------------------------------
# Keys are the stable identifiers used in code (engine.py matches on
# these). Values are the human-readable labels shown in the sidebar.
# Matching on the key rather than substring-searching the label is
# what keeps scenario dispatch from breaking if the label text ever
# changes.
DISASTER_SCENARIOS = {
    "NORMAL": "Normal Operations (All Green)",
    "SERVER_DDOS": "Scenario A: DDoS on Primary Game Server",
    "STAGE_SWITCH_FAIL": "Scenario B: Stage Right Switch Failure",
    "STREAM_PACKET_LOSS": "Scenario C: Broadcast Stream Packet Loss & Jitter",
    "TOTAL_CONGESTION": "Scenario D: Total Stage Congestion",
}

# --- Device topology -----------------------------------------------------
BASE_DEVICES = [
    {"id": "PC-STAGE-L1", "zone": "Stage Left", "base_ping": 2.1, "base_jitter": 0.3, "base_loss": 0.0},
    {"id": "PC-STAGE-L2", "zone": "Stage Left", "base_ping": 2.3, "base_jitter": 0.4, "base_loss": 0.0},
    {"id": "PC-STAGE-R1", "zone": "Stage Right", "base_ping": 2.2, "base_jitter": 0.2, "base_loss": 0.0},
    {"id": "PC-STAGE-R2", "zone": "Stage Right", "base_ping": 2.4, "base_jitter": 0.5, "base_loss": 0.0},
    {"id": "OBS-BROADCAST-01", "zone": "Production Booth", "base_ping": 3.1, "base_jitter": 0.6, "base_loss": 0.0},
    {"id": "CASTER-DESK-PC", "zone": "Production Booth", "base_ping": 2.8, "base_jitter": 0.4, "base_loss": 0.0},
    {"id": "GAME-SERVER-PRIMARY", "zone": "Server Rack", "base_ping": 1.2, "base_jitter": 0.1, "base_loss": 0.0},
    {"id": "GAME-SERVER-BACKUP", "zone": "Server Rack", "base_ping": 1.3, "base_jitter": 0.1, "base_loss": 0.0},
]

# Zones and the zone -> device-id mapping are *derived* from
# BASE_DEVICES rather than hand-typed a second time, so they can never
# drift out of sync with the actual device list.
ZONES = list(dict.fromkeys(d["zone"] for d in BASE_DEVICES))

DEVICES_BY_ZONE: dict[str, list[str]] = {}
for _d in BASE_DEVICES:
    DEVICES_BY_ZONE.setdefault(_d["zone"], []).append(_d["id"])

# --- Status severity ----------------------------------------------------
STATUS_HEALTHY = "HEALTHY"
STATUS_WARNING = "WARNING"
STATUS_CRITICAL = "CRITICAL"
STATUS_UNREACHABLE = "UNREACHABLE"

SEVERITY_RANK = {
    STATUS_HEALTHY: 0,
    STATUS_WARNING: 1,
    STATUS_CRITICAL: 2,
    STATUS_UNREACHABLE: 3,
}

# --- Thresholds -----------------------------------------------------------
# Two-tier thresholds per metric. 100% loss is always UNREACHABLE
# regardless of ping, since a fully dropped link has no meaningful
# latency reading.
THRESHOLDS = {
    "ping_warning_ms": 15.0,
    "ping_critical_ms": 30.0,
    "loss_warning_pct": 1.0,
    "loss_critical_pct": 5.0,
}

# --- Live-simulation refresh ---------------------------------------------
REFRESH_MIN = 1
REFRESH_MAX = 5
DEFAULT_REFRESH = 3

# Relative noise applied per refresh tick so the feed genuinely moves
# instead of a "LIVE" badge sitting over static numbers.
NOISE_PING_PCT = 0.06
NOISE_JITTER_PCT = 0.10
NOISE_LOSS_ABS_PCT = 0.1
