"""Regression tests for truthful mesh routing and undelivered handoffs.

No physical device, authenticated transport, model endpoint or cloud is used.
"""

from types import SimpleNamespace

import pytest

import core.device_mesh as mesh_module
from core.device_mesh import DEVICE_FLEET, DeviceMesh, DeviceStatus, SyncProtocol


@pytest.fixture
def clock(monkeypatch):
    observation = SimpleNamespace(now=100.0)
    monkeypatch.setattr(
        mesh_module, "time", SimpleNamespace(monotonic=lambda: observation.now)
    )
    return observation


def test_inventory_does_not_imply_devices_are_connected():
    mesh = DeviceMesh()

    assert all(device.status == DeviceStatus.STANDBY for device in mesh.list_devices())
    assert mesh.list_online() == []
    assert mesh.find_best_device_for_model("chatgpt_pro") is None
    assert mesh.mesh_status()["online"] == 0


def test_mesh_instances_do_not_share_mutable_device_state():
    first, second = DeviceMesh(), DeviceMesh()
    original_roles = list(DEVICE_FLEET["pc_win11"].roles)
    original_gpu = DEVICE_FLEET["pc_win11"].capabilities["gpu"]

    first.get_device("pc_win11").roles.append("temporary_role")
    first.get_device("pc_win11").capabilities["gpu"] = "test_hardware"
    first.record_heartbeat("pc_win11")

    assert second.get_device("pc_win11").roles == original_roles
    assert second.get_device("pc_win11").capabilities["gpu"] == original_gpu
    assert second.get_device("pc_win11").last_seen is None
    assert second.list_online() == []
    assert DEVICE_FLEET["pc_win11"].roles == original_roles
    assert DEVICE_FLEET["pc_win11"].capabilities["gpu"] == original_gpu
    assert DEVICE_FLEET["pc_win11"].status == DeviceStatus.STANDBY


def test_configuration_and_serialized_timestamp_cannot_create_reachability():
    mesh = DeviceMesh()
    mesh.set_status("pc_win11", DeviceStatus.ONLINE)
    device = mesh.get_device("pc_win11")
    assert device.last_seen is None
    device.last_seen = "2099-01-01T00:00:00+00:00"

    assert mesh.list_online() == []
    assert mesh.find_best_device_for_model("ollama_llama3") is None
    summary = mesh.mesh_status()
    assert summary["online"] == 0
    assert summary["devices"]["pc_win11"]["status"] == "standby"
    assert summary["devices"]["pc_win11"]["recorded_status"] == "online"


def test_recent_observations_expire_and_can_be_refreshed(clock):
    mesh = DeviceMesh(heartbeat_timeout_seconds=5)
    mesh.record_heartbeat("pc_win11")
    assert mesh.find_best_device_for_model("ollama_llama3").id == "pc_win11"

    clock.now += 6
    assert mesh.list_online() == []
    assert mesh.find_best_device_for_model("ollama_llama3") is None
    summary = mesh.mesh_status()
    assert summary["online"] == 0
    assert summary["online"] + summary["offline"] + summary["standby"] == summary["total_devices"]

    mesh.record_heartbeat("pc_win11")
    assert [device.id for device in mesh.list_online()] == ["pc_win11"]


def test_status_reactivation_requires_a_new_observation(clock):
    mesh = DeviceMesh()
    mesh.record_heartbeat("pc_win11")
    mesh.set_status("pc_win11", DeviceStatus.STANDBY)
    mesh.set_status("pc_win11", DeviceStatus.ONLINE)

    assert mesh.find_best_device_for_model("ollama_llama3") is None
    mesh.record_heartbeat("pc_win11")
    assert mesh.find_best_device_for_model("ollama_llama3").id == "pc_win11"


def test_handoff_preserves_both_devices_until_delivery_exists():
    mesh = DeviceMesh()
    source = mesh.get_device("pc_win11")
    target = mesh.get_device("surface_pro")
    source.active_context = "source task remains running"
    target.active_context = "unrelated target task"
    before_source = source.model_dump()
    before_target = target.model_dump()

    handoff = mesh.handoff_context("pc_win11", "surface_pro", "task snapshot", "task-1")

    assert handoff.status == "transport_not_implemented"
    assert handoff.context_payload == "task snapshot"
    assert handoff.task_id == "task-1"
    assert source.model_dump() == before_source
    assert target.model_dump() == before_target
    assert mesh.list_online() == []
    assert mesh.handoff_log == [handoff]


def test_handoff_does_not_invent_a_cloud_bridge():
    mesh = DeviceMesh()
    mesh.get_device("pc_win11").sync_bridges = [SyncProtocol.TAILSCALE]
    mesh.get_device("surface_pro").sync_bridges = [SyncProtocol.USB]

    handoff = mesh.handoff_context("pc_win11", "surface_pro", "snapshot")

    assert handoff.sync_protocol is None
    assert handoff.status == "transport_not_implemented"


def test_failover_preparation_does_not_report_or_apply_migration(clock):
    mesh = DeviceMesh()
    source = mesh.get_device("pc_win11")
    source.active_context = "unfinished work"
    mesh.set_status("pc_win11", DeviceStatus.OFFLINE)
    mesh.record_heartbeat("surface_pro")
    target = mesh.get_device("surface_pro")
    target_before = target.model_dump()

    assert mesh.auto_failover("pc_win11") is None
    assert source.active_context == "unfinished work"
    assert target.model_dump() == target_before
    assert len(mesh.handoff_log) == 1
    assert mesh.handoff_log[0].target_device == "surface_pro"
    assert mesh.handoff_log[0].status == "transport_not_implemented"


@pytest.mark.parametrize("target_state", ["standby", "configured_online", "expired"])
def test_failover_does_not_select_unobserved_or_stale_targets(clock, target_state):
    mesh = DeviceMesh(heartbeat_timeout_seconds=5)
    mesh.get_device("pc_win11").active_context = "unfinished work"
    if target_state == "configured_online":
        mesh.set_status("surface_pro", DeviceStatus.ONLINE)
    elif target_state == "expired":
        mesh.record_heartbeat("surface_pro")
        clock.now += 6

    assert mesh.auto_failover("pc_win11") is None
    assert mesh.handoff_log == []


def test_failover_chain_does_not_route_back_to_source():
    mesh = DeviceMesh()
    assert mesh.get_failover_chain("pc_win11") == ["surface_pro"]


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_timeout_must_be_positive_and_finite(timeout):
    with pytest.raises(ValueError, match="finite and positive"):
        DeviceMesh(heartbeat_timeout_seconds=timeout)
