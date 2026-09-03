"""Tests for the ARK95X single-control-plane merge contract."""

import pytest

from control_plane import (
    AUTHORITATIVE_STATE_PATH,
    AgentRecord,
    ControlPlane,
    build_default_control_plane,
)

EXPECTED_AGENTS = {
    "arc_x",
    "codex_security",
    "memory_cortex",
    "monitoring",
    "github",
    "n8n",
    "devices",
    "business_ops",
}


def test_all_existing_agents_converge_on_one_plane():
    plane = build_default_control_plane()

    assert set(plane.agents) == EXPECTED_AGENTS
    assert plane.snapshot()["authoritative_state_path"] == AUTHORITATIVE_STATE_PATH
    assert plane.snapshot()["agent_count"] == 8


def test_no_agent_can_override_or_self_approve():
    plane = build_default_control_plane()

    for agent in plane.agents.values():
        assert agent.can_override_control_plane is False
        assert agent.can_self_approve is False


def test_registration_rejects_competing_authority():
    plane = ControlPlane()

    with pytest.raises(ValueError, match="override"):
        plane.register_agent(
            AgentRecord(
                agent_id="parallel_brain",
                role="competing coordinator",
                capabilities=("route",),
                authority_scope=("analysis",),
                can_override_control_plane=True,
            )
        )

    with pytest.raises(ValueError, match="self-approve"):
        plane.register_agent(
            AgentRecord(
                agent_id="self_approver",
                role="unsafe executor",
                capabilities=("execute",),
                authority_scope=("financial",),
                can_self_approve=True,
            )
        )


def test_agent_report_is_accepted_by_control_plane():
    plane = build_default_control_plane()

    receipt = plane.report(
        "monitoring",
        "healthy",
        {"evidence_ref": "health-check-1", "confidence": 1.0},
    )
    monitoring = plane.agents["monitoring"]

    assert receipt["accepted"] is True
    assert monitoring.reporting_state == "reported"
    assert monitoring.live_adapter_state == "reporting"
    assert monitoring.last_report["evidence_ref"] == "health-check-1"
    assert monitoring.last_reported_at is not None


def test_normal_actions_queue_through_control_plane():
    plane = build_default_control_plane()

    request = plane.request_action(
        "arc_x",
        "rank current work",
        "planning",
    )

    assert request["disposition"] == "queued_for_control_plane"
    assert request["executed"] is False


@pytest.mark.parametrize(
    ("agent_id", "action_class"),
    [
        ("business_ops", "financial"),
        ("business_ops", "legal"),
        ("github", "deployment"),
        ("n8n", "account_change"),
        ("devices", "system_mutation"),
        ("codex_security", "security_sensitive"),
    ],
)
def test_consequential_actions_require_human_approval(agent_id, action_class):
    plane = build_default_control_plane()

    request = plane.request_action(
        agent_id,
        f"attempt {action_class}",
        action_class,
    )

    assert request["disposition"] == "queued_for_human_approval"
    assert request["executed"] is False


def test_out_of_scope_action_is_rejected():
    plane = build_default_control_plane()

    request = plane.request_action(
        "monitoring",
        "transfer funds",
        "financial",
    )

    assert request["disposition"] == "rejected_out_of_scope"
    assert request["executed"] is False


def test_unknown_agent_cannot_report_or_act():
    plane = build_default_control_plane()

    with pytest.raises(KeyError, match="Unknown agent"):
        plane.report("unknown", "healthy")

    with pytest.raises(KeyError, match="Unknown agent"):
        plane.request_action("unknown", "do thing", "analysis")
