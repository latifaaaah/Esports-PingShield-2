from src.config import BASE_DEVICES, DEVICES_BY_ZONE, DISASTER_SCENARIOS, THRESHOLDS, ZONES


def test_devices_by_zone_matches_base_devices_exactly():
    """Guards against the zone/device mapping ever being hand-duplicated
    and drifting out of sync with BASE_DEVICES again."""
    rebuilt = {}
    for d in BASE_DEVICES:
        rebuilt.setdefault(d["zone"], []).append(d["id"])
    assert DEVICES_BY_ZONE == rebuilt


def test_zones_cover_every_device():
    assert set(ZONES) == {d["zone"] for d in BASE_DEVICES}


def test_every_device_has_required_fields():
    required = {"id", "zone", "base_ping", "base_jitter", "base_loss"}
    for device in BASE_DEVICES:
        assert required.issubset(device.keys())


def test_device_ids_are_unique():
    ids = [d["id"] for d in BASE_DEVICES]
    assert len(ids) == len(set(ids))


def test_scenario_keys_are_unique_and_normal_exists():
    assert "NORMAL" in DISASTER_SCENARIOS
    assert len(DISASTER_SCENARIOS) == len(set(DISASTER_SCENARIOS.keys()))


def test_warning_threshold_below_critical_threshold():
    assert THRESHOLDS["ping_warning_ms"] < THRESHOLDS["ping_critical_ms"]
    assert THRESHOLDS["loss_warning_pct"] < THRESHOLDS["loss_critical_pct"]
