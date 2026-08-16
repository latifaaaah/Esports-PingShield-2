import pandas as pd
import pytest

from src.config import BASE_DEVICES, DEVICES_BY_ZONE, STATUS_CRITICAL, STATUS_HEALTHY, STATUS_UNREACHABLE, STATUS_WARNING, ZONES
from src.engine import ScenarioError, classify_status, process_scenario, worst_status


def test_normal_scenario_is_all_healthy():
    df = process_scenario("NORMAL", ZONES)
    assert len(df) == len(BASE_DEVICES)
    assert (df["status"] == STATUS_HEALTHY).all()


def test_unknown_scenario_raises():
    with pytest.raises(ScenarioError):
        process_scenario("NOT_A_REAL_SCENARIO", ZONES)


def test_empty_zone_selection_returns_empty_frame_with_correct_columns():
    df = process_scenario("NORMAL", [])
    assert df.empty
    assert list(df.columns) == ["id", "zone", "ping", "jitter", "loss", "status"]


def test_server_ddos_only_affects_primary_server():
    df = process_scenario("SERVER_DDOS", ZONES)
    primary = df[df["id"] == "GAME-SERVER-PRIMARY"].iloc[0]
    backup = df[df["id"] == "GAME-SERVER-BACKUP"].iloc[0]
    assert primary["status"] == STATUS_CRITICAL
    assert backup["status"] == STATUS_HEALTHY


def test_stage_switch_failure_marks_stage_right_unreachable_not_zero_jitter():
    df = process_scenario("STAGE_SWITCH_FAIL", ZONES)
    stage_right = df[df["zone"] == "Stage Right"]
    assert (stage_right["status"] == STATUS_UNREACHABLE).all()
    assert stage_right["ping"].isna().all()
    assert stage_right["jitter"].isna().all()
    stage_left = df[df["zone"] == "Stage Left"]
    assert (stage_left["status"] == STATUS_HEALTHY).all()


def test_stream_packet_loss_only_affects_broadcast_encoder():
    df = process_scenario("STREAM_PACKET_LOSS", ZONES)
    obs = df[df["id"] == "OBS-BROADCAST-01"].iloc[0]
    caster = df[df["id"] == "CASTER-DESK-PC"].iloc[0]
    assert obs["status"] in (STATUS_WARNING, STATUS_CRITICAL)
    assert caster["status"] == STATUS_HEALTHY


def test_total_congestion_affects_every_selected_device():
    df_normal = process_scenario("NORMAL", ZONES)
    df_congested = process_scenario("TOTAL_CONGESTION", ZONES)
    merged = df_normal.merge(df_congested, on="id", suffixes=("_normal", "_congested"))
    assert (merged["ping_congested"] > merged["ping_normal"]).all()


def test_zone_filter_only_returns_devices_in_selected_zones():
    df = process_scenario("NORMAL", ["Server Rack"])
    assert set(df["zone"]) == {"Server Rack"}
    assert set(df["id"]) == set(DEVICES_BY_ZONE["Server Rack"])


class TestClassifyStatus:
    def test_healthy(self):
        assert classify_status(2.0, 0.0) == STATUS_HEALTHY

    def test_warning_on_ping(self):
        assert classify_status(20.0, 0.0) == STATUS_WARNING

    def test_critical_on_ping(self):
        assert classify_status(50.0, 0.0) == STATUS_CRITICAL

    def test_critical_on_loss(self):
        assert classify_status(2.0, 8.0) == STATUS_CRITICAL

    def test_full_loss_is_unreachable_even_with_low_ping(self):
        assert classify_status(2.0, 100.0) == STATUS_UNREACHABLE

    def test_missing_ping_is_unreachable(self):
        assert classify_status(None, 100.0) == STATUS_UNREACHABLE


class TestWorstStatus:
    def test_empty_list_defaults_healthy(self):
        assert worst_status([]) == STATUS_HEALTHY

    def test_picks_highest_severity(self):
        assert worst_status([STATUS_HEALTHY, STATUS_WARNING, STATUS_CRITICAL]) == STATUS_CRITICAL

    def test_unreachable_beats_critical(self):
        assert worst_status([STATUS_CRITICAL, STATUS_UNREACHABLE]) == STATUS_UNREACHABLE
