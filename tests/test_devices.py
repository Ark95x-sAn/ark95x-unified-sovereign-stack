"""ARK95X Devices Adapter tests. Uses an injected fake command runner so
the request/approve gate is proven deterministically without depending on
a live docker-compose stack; a separate test proves the default runner is
a real subprocess call that degrades gracefully when docker is
unavailable."""
import pytest

from control_plane import build_default_control_plane
from devices import DevicesAdapter


class FakeCompleted:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def fake_runner_factory(returncode=0, stdout="ok", stderr=""):
    calls = []

    def runner(args):
        calls.append(args)
        return FakeCompleted(returncode=returncode, stdout=stdout, stderr=stderr)

    runner.calls = calls
    return runner


def test_check_service_status_reports_online_and_reachable():
    plane = build_default_control_plane()
    runner = fake_runner_factory(returncode=0, stdout='[{"Service":"redis"}]')
    adapter = DevicesAdapter(control_plane=plane, runner=runner)

    result = adapter.check_service_status("redis")

    assert result["reachable"] is True
    agent = plane.agents["devices"]
    assert agent.state == "online"
    assert agent.last_report["service"] == "redis"
    assert runner.calls == [["docker", "compose", "ps", "redis", "--format", "json"]]


def test_check_service_status_reports_unreachable_on_nonzero_exit():
    plane = build_default_control_plane()
    runner = fake_runner_factory(returncode=1, stdout="", stderr="no such service")
    adapter = DevicesAdapter(control_plane=plane, runner=runner)

    result = adapter.check_service_status("ghost")

    assert result["reachable"] is False
    assert plane.agents["devices"].state == "unreachable"


def test_request_restart_requires_control_plane():
    adapter = DevicesAdapter(control_plane=None)
    with pytest.raises(ValueError):
        adapter.request_restart("redis")


def test_request_restart_queues_for_human_approval_and_does_not_execute():
    plane = build_default_control_plane()
    runner = fake_runner_factory()
    adapter = DevicesAdapter(control_plane=plane, runner=runner)

    request = adapter.request_restart("redis")

    assert request["disposition"] == "queued_for_human_approval"
    assert request["executed"] is False
    assert runner.calls == []  # nothing executed yet -- the whole point of the gate


def test_approve_pending_action_executes_and_reports_real_outcome():
    plane = build_default_control_plane()
    runner = fake_runner_factory(returncode=0, stdout="redis restarted", stderr="")
    adapter = DevicesAdapter(control_plane=plane, runner=runner)

    request = adapter.request_restart("redis")
    result = adapter.approve_pending_action(request["request_id"])

    assert result["succeeded"] is True
    assert result["service"] == "redis"
    assert ["docker", "compose", "restart", "redis"] in runner.calls

    agent = plane.agents["devices"]
    assert agent.state == "completed"
    assert agent.last_report["request_id"] == request["request_id"]


def test_approve_pending_action_reports_failure_on_nonzero_exit():
    plane = build_default_control_plane()
    runner = fake_runner_factory(returncode=1, stdout="", stderr="failed to restart")
    adapter = DevicesAdapter(control_plane=plane, runner=runner)

    request = adapter.request_restart("redis")
    result = adapter.approve_pending_action(request["request_id"])

    assert result["succeeded"] is False
    assert plane.agents["devices"].state == "failed"


def test_approve_unknown_request_id_raises():
    plane = build_default_control_plane()
    adapter = DevicesAdapter(control_plane=plane, runner=fake_runner_factory())
    with pytest.raises(KeyError):
        adapter.approve_pending_action("not-a-real-id")


def test_default_runner_is_a_real_subprocess_call_and_does_not_raise():
    """No injected runner -- exercises the real subprocess.run path. Passes
    whether or not docker/docker-compose is actually installed; the point
    is the adapter never raises out of a missing/unreachable command."""
    adapter = DevicesAdapter(control_plane=None)
    result = adapter.check_service_status("nonexistent-service")
    assert isinstance(result, dict)
    assert "reachable" in result
