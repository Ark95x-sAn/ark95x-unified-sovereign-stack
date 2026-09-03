"""ARK95X arc_x <-> Control Plane integration tests.
Proves router/failover.py's real routing decision (which backend a task
gets dispatched to) is reported through the control plane as arc_x, per
docs/control-plane-pass-1.md ("ARC X ... Final dispatch and cross-agent
priority"). Backward compatibility (control_plane=None) is already covered
by the pre-existing tests/test_failover.py suite.
"""
import asyncio
import json

import pytest

from control_plane import build_default_control_plane
from router.failover import FailoverRouter, BackendAdapter


class FakeBackend(BackendAdapter):
    def __init__(self, name, priority, available=True, response="ok", raises=False):
        self.name = name
        self.priority = priority
        self._available = available
        self._response = response
        self._raises = raises

    async def is_available(self) -> bool:
        return self._available

    async def dispatch(self, prompt: str) -> str:
        if self._raises:
            raise RuntimeError("backend exploded")
        return self._response


def write_state(path, todo_queue):
    path.write_text(json.dumps({"todo_queue": todo_queue}))


def test_successful_dispatch_reports_routed_through_arc_x(tmp_path):
    state_path = tmp_path / "ARK-STATE.json"
    write_state(state_path, [{"id": "T1", "status": "pending", "depends_on": [], "phase": 5, "title": "x"}])
    plane = build_default_control_plane()
    fake = FakeBackend("ollama", 2, response="done")
    router = FailoverRouter(state_path=str(state_path), backends=[fake], control_plane=plane)

    result = asyncio.run(router.dispatch_next())

    assert result["status"] == "dispatched"
    agent = plane.agents["arc_x"]
    assert agent.state == "routed"
    assert agent.last_report["task_id"] == "T1"
    assert agent.last_report["backend"] == "ollama"


def test_routing_request_is_queued_for_control_plane_not_human(tmp_path):
    """routing is not in APPROVAL_REQUIRED_ACTION_CLASSES -- it should auto-
    proceed rather than block on a human, matching arc_x's coordinator
    role."""
    state_path = tmp_path / "ARK-STATE.json"
    write_state(state_path, [{"id": "T1", "status": "pending", "depends_on": [], "phase": 5, "title": "x"}])
    plane = build_default_control_plane()
    fake = FakeBackend("ollama", 2, response="done")
    router = FailoverRouter(state_path=str(state_path), backends=[fake], control_plane=plane)

    request = router._request_arc_x_route(task_id="T1", backend="ollama")

    assert request["disposition"] == "queued_for_control_plane"


def test_no_backend_available_reports_through_arc_x(tmp_path):
    state_path = tmp_path / "ARK-STATE.json"
    write_state(state_path, [{"id": "T1", "status": "pending", "depends_on": []}])
    plane = build_default_control_plane()
    router = FailoverRouter(
        state_path=str(state_path),
        backends=[FakeBackend("claude", 1, available=False)],
        control_plane=plane,
    )

    result = asyncio.run(router.dispatch_next())

    assert result["status"] == "no_backend_available"
    assert plane.agents["arc_x"].state == "no_backend"


def test_dispatch_failure_reports_through_arc_x(tmp_path):
    state_path = tmp_path / "ARK-STATE.json"
    write_state(state_path, [{"id": "T1", "status": "pending", "depends_on": [], "phase": 5, "title": "x"}])
    plane = build_default_control_plane()
    fake = FakeBackend("groq", 3, raises=True)
    router = FailoverRouter(state_path=str(state_path), backends=[fake], control_plane=plane)

    result = asyncio.run(router.dispatch_next())

    assert result["status"] == "dispatch_failed"
    assert plane.agents["arc_x"].state == "dispatch_failed"


def test_no_pending_tasks_reports_idle_through_arc_x(tmp_path):
    state_path = tmp_path / "ARK-STATE.json"
    write_state(state_path, [{"id": "T1", "status": "done", "depends_on": []}])
    plane = build_default_control_plane()
    router = FailoverRouter(state_path=str(state_path), backends=[FakeBackend("claude", 1)], control_plane=plane)

    result = asyncio.run(router.dispatch_next())

    assert result["status"] == "no_pending_tasks"
    assert plane.agents["arc_x"].state == "idle"


def test_without_control_plane_behavior_is_unchanged(tmp_path):
    state_path = tmp_path / "ARK-STATE.json"
    write_state(state_path, [{"id": "T1", "status": "pending", "depends_on": [], "phase": 5, "title": "x"}])
    fake = FakeBackend("ollama", 2, response="done")
    router = FailoverRouter(state_path=str(state_path), backends=[fake], control_plane=None)

    result = asyncio.run(router.dispatch_next())

    assert result["status"] == "dispatched"  # no control_plane calls raised or blocked anything
