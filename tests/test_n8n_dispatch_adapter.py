"""ARK95X n8n Dispatch Adapter tests. Feeds real
router.failover.FailoverRouter.dispatch_next()-shaped results through the
adapter and proves it branches exactly like
workflows/ark_failover_dispatch_v1.json's Check_Dispatch_Status switch
node, gating the account-changing branch through the control plane."""
import pytest

from control_plane import build_default_control_plane
from n8n.dispatch_adapter import N8nDispatchAdapter


def test_dispatched_status_requests_account_change_and_does_not_auto_apply():
    plane = build_default_control_plane()
    adapter = N8nDispatchAdapter(control_plane=plane)

    request = adapter.handle_dispatch_result(
        {"status": "dispatched", "task_id": "T5.6", "backend": "ollama", "response": "..."}
    )

    assert request["disposition"] == "queued_for_human_approval"
    assert request["executed"] is False
    assert request["request_id"] in adapter._pending


def test_approve_pending_commit_reports_completion():
    plane = build_default_control_plane()
    adapter = N8nDispatchAdapter(control_plane=plane)

    request = adapter.handle_dispatch_result(
        {"status": "dispatched", "task_id": "T5.6", "backend": "ollama", "response": "..."}
    )
    result = adapter.approve_pending_commit(request["request_id"])

    assert result["task_id"] == "T5.6"
    agent = plane.agents["n8n"]
    assert agent.state == "completed"
    assert agent.last_report["task_id"] == "T5.6"


def test_approve_unknown_commit_request_raises():
    adapter = N8nDispatchAdapter(control_plane=build_default_control_plane())
    with pytest.raises(KeyError):
        adapter.approve_pending_commit("not-a-real-id")


@pytest.mark.parametrize("status", ["no_backend_available", "dispatch_failed"])
def test_failure_statuses_are_reported_as_alerts(status):
    plane = build_default_control_plane()
    adapter = N8nDispatchAdapter(control_plane=plane)

    result = adapter.handle_dispatch_result({"status": status, "task_id": "T5.6"})

    assert result["accepted"] is True
    assert plane.agents["n8n"].state == "alert"


def test_no_pending_tasks_status_is_reported_as_idle():
    plane = build_default_control_plane()
    adapter = N8nDispatchAdapter(control_plane=plane)

    adapter.handle_dispatch_result({"status": "no_pending_tasks"})

    assert plane.agents["n8n"].state == "idle"


def test_without_control_plane_dispatched_status_is_a_noop():
    adapter = N8nDispatchAdapter(control_plane=None)
    result = adapter.handle_dispatch_result({"status": "dispatched", "task_id": "T5.6", "backend": "ollama"})
    assert result["disposition"] == "no_control_plane"


def test_without_control_plane_report_statuses_return_none():
    adapter = N8nDispatchAdapter(control_plane=None)
    assert adapter.handle_dispatch_result({"status": "no_pending_tasks"}) is None
