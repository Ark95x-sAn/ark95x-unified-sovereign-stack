"""ARK95X Memory Cortex Adapter tests. Proves proposals actually patch a
real ARK-STATE.json-shaped file on disk once the control plane accepts
them (memory_update auto-queues -- see control_plane.control_plane)."""
import json

import pytest

from control_plane import build_default_control_plane
from memory_cortex import MemoryCortexAdapter


@pytest.fixture
def state_path(tmp_path):
    path = tmp_path / "ARK-STATE.json"
    path.write_text(json.dumps({
        "genome_id": "test-genome",
        "known_gaps": ["existing gap"],
        "todo_queue": [{"id": "T1", "title": "existing task", "status": "done"}],
    }))
    return path


def test_propose_known_gap_applies_and_reports(state_path):
    plane = build_default_control_plane()
    adapter = MemoryCortexAdapter(control_plane=plane, state_path=str(state_path))

    request = adapter.propose_known_gap("a brand new gap")

    assert request["disposition"] == "queued_for_control_plane"
    assert request["applied"] is True

    state = json.loads(state_path.read_text())
    assert "a brand new gap" in state["known_gaps"]
    assert "existing gap" in state["known_gaps"]  # untouched

    agent = plane.agents["memory_cortex"]
    assert agent.state == "accepted"
    assert agent.last_report["patch_type"] == "known_gaps_add"


def test_propose_duplicate_known_gap_is_a_no_op(state_path):
    plane = build_default_control_plane()
    adapter = MemoryCortexAdapter(control_plane=plane, state_path=str(state_path))

    request = adapter.propose_known_gap("existing gap")

    assert request["applied"] is False
    state = json.loads(state_path.read_text())
    assert state["known_gaps"].count("existing gap") == 1

    agent = plane.agents["memory_cortex"]
    assert agent.state == "rejected_duplicate"


def test_propose_todo_task_applies_and_reports(state_path):
    plane = build_default_control_plane()
    adapter = MemoryCortexAdapter(control_plane=plane, state_path=str(state_path))

    task = {"id": "T99", "title": "new proposed task", "status": "pending"}
    request = adapter.propose_todo_task(task)

    assert request["applied"] is True
    state = json.loads(state_path.read_text())
    ids = [t["id"] for t in state["todo_queue"]]
    assert "T99" in ids
    assert "T1" in ids  # untouched


def test_propose_duplicate_todo_task_is_a_no_op(state_path):
    plane = build_default_control_plane()
    adapter = MemoryCortexAdapter(control_plane=plane, state_path=str(state_path))

    request = adapter.propose_todo_task({"id": "T1", "title": "dup", "status": "pending"})

    assert request["applied"] is False
    state = json.loads(state_path.read_text())
    assert len(state["todo_queue"]) == 1


def test_updated_at_bumped_on_real_write(state_path):
    plane = build_default_control_plane()
    adapter = MemoryCortexAdapter(control_plane=plane, state_path=str(state_path))

    adapter.propose_known_gap("another gap")

    state = json.loads(state_path.read_text())
    assert "updated_at" in state
