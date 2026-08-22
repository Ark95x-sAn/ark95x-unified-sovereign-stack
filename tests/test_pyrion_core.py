from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import companions.pyrion_core.engine as engine_module
from companions.pyrion_core.engine import (
    GENESIS_HASH,
    IntegrityError,
    PolicyError,
    PyrionEngine,
    action_scope_hash,
    canonical,
    digest,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
TRUSTED_ACTORS = {
    "human:ark95x": "human",
    "human:test": "human",
    "agent:test": "agent",
    "tool:test": "tool",
    "system:test": "system",
}


def mission() -> dict:
    return {
        "schema_version": "pyrion.mission/v1",
        "mission_id": "mis.network95",
        "revision": 1,
        "title": "Build a verified packet",
        "objective": "Create one source-backed and validated decision packet",
        "status": "active",
        "priority": 5,
        "created_at": "2026-08-22T12:00:00Z",
        "due_at": "2026-08-29T12:00:00Z",
        "evidence_policy": "required",
        "evidence_requirements": [{
            "requirement_id": "req.timeline",
            "label": "Traceable timeline",
            "weight": 5,
            "minimum_verified_sources": 2,
            "required": True,
        }],
        "artifact_requirements": [{
            "artifact_id": "art.log",
            "label": "Decision log",
            "weight": 3,
            "required": True,
            "verification_required": True,
        }],
        "approval_gates": [{
            "approval_id": "apr.release",
            "label": "Release approval",
            "action_id": "act.release",
            "required_for_completion": True,
        }],
        "risk_profile": {"assessed": True, "severity": 3, "likelihood": 2},
        "candidate_actions": [
            {
                "action_id": "act.draft",
                "kind": "draft",
                "description": "Build the internal draft",
                "priority": 5,
                "impact": "low",
                "reversible": True,
                "external_side_effect": False,
                "requires_human_approval": False,
                "prerequisite_requirement_ids": ["req.timeline"],
                "prerequisite_artifact_ids": [],
            },
            {
                "action_id": "act.release",
                "kind": "external_write",
                "description": "Release the packet",
                "priority": 4,
                "impact": "high",
                "reversible": False,
                "external_side_effect": True,
                "requires_human_approval": True,
                "prerequisite_requirement_ids": ["req.timeline"],
                "prerequisite_artifact_ids": ["art.log"],
            },
        ],
        "metadata": {},
    }


def event(
    event_id: str,
    event_type: str,
    payload: dict,
    second: int,
    actor_type: str = "tool",
    *,
    actor_id: str | None = None,
    revision: int = 1,
    mission_id: str = "mis.network95",
) -> dict:
    return {
        "schema_version": "pyrion.event/v1",
        "event_id": event_id,
        "mission_id": mission_id,
        "mission_revision": revision,
        "occurred_at": f"2026-08-22T12:00:{second:02d}Z",
        "actor": {
            "actor_id": actor_id or f"{actor_type}:test",
            "actor_type": actor_type,
        },
        "type": event_type,
        "payload": payload,
    }


def simple_mission() -> dict:
    result = mission()
    result["evidence_policy"] = "not_required"
    result["evidence_requirements"] = []
    result["artifact_requirements"] = []
    result["approval_gates"] = []
    result["candidate_actions"] = [copy.deepcopy(result["candidate_actions"][0])]
    result["candidate_actions"][0]["prerequisite_requirement_ids"] = []
    return result


class PyrionEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = Path(self.tmp.name) / "pyrion.jsonl"
        self.engine = PyrionEngine(self.ledger, TRUSTED_ACTORS)
        self.mission = mission()
        self.register = self.engine.register_mission(
            self.mission,
            {"actor_id": "human:ark95x", "actor_type": "human"},
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def head(self) -> str:
        return self.engine.verify_ledger()["head_hash"]

    def assess(self, as_of: str = "2026-08-22T12:00:30Z") -> dict:
        return self.engine.assess("mis.network95", self.head(), as_of)

    def record_minimum_evidence(self) -> None:
        self.engine.record_event(event("evt.obs.one", "evidence.observed", {
            "evidence_id": "ev.one", "requirement_id": "req.timeline",
            "source_id": "src.one", "source_ref": "internal://one",
            "content_sha256": SHA_A,
        }, 1))
        self.engine.record_event(event("evt.ver.one", "evidence.verified", {
            "evidence_id": "ev.one", "verification_ref": "test://one",
            "content_sha256": SHA_A,
        }, 2, "human"))
        self.engine.record_event(event("evt.obs.two", "evidence.observed", {
            "evidence_id": "ev.two", "requirement_id": "req.timeline",
            "source_id": "src.two", "source_ref": "internal://two",
            "content_sha256": SHA_B,
        }, 3))

    def record_full_prerequisites(self) -> None:
        self.record_minimum_evidence()
        self.engine.record_event(event("evt.ver.two", "evidence.verified", {
            "evidence_id": "ev.two", "verification_ref": "test://two",
            "content_sha256": SHA_B,
        }, 4, "human"))
        self.engine.record_event(event("evt.art.one", "artifact.recorded", {
            "artifact_id": "art.log", "location": "library://decision-log",
            "content_sha256": SHA_A,
        }, 5))
        self.engine.record_event(event("evt.art.ver", "artifact.verified", {
            "artifact_id": "art.log", "verification_ref": "test://artifact",
            "content_sha256": SHA_A,
        }, 6, "human"))

    def test_canonical_json_is_order_independent(self) -> None:
        self.assertEqual(canonical({"b": 2, "a": 1}), canonical({"a": 1, "b": 2}))

    def test_register_is_idempotent_bounded_and_chain_is_valid(self) -> None:
        repeated = self.engine.register_mission(
            self.mission,
            {"actor_id": "human:ark95x", "actor_type": "human"},
        )
        self.assertTrue(repeated["idempotent"])
        verified = self.engine.verify_ledger(self.register["head_hash"])
        self.assertEqual(1, verified["entries"])
        registration = json.loads(self.ledger.read_text(encoding="utf-8"))["event"]
        self.assertLessEqual(len(registration["event_id"]), 64)
        self.assertEqual(1, registration["mission_revision"])

    def test_maximum_length_mission_id_has_bounded_registration_id(self) -> None:
        other = Path(self.tmp.name) / "long.jsonl"
        candidate = simple_mission()
        candidate["mission_id"] = "m" + "a" * 63
        engine = PyrionEngine(other, TRUSTED_ACTORS)
        engine.register_mission(
            candidate, {"actor_id": "human:ark95x", "actor_type": "human"}
        )
        registration = json.loads(other.read_text(encoding="utf-8"))["event"]
        self.assertLessEqual(len(registration["event_id"]), 64)

    def test_untrusted_registration_and_actor_type_forgery_fail_closed(self) -> None:
        other = Path(self.tmp.name) / "untrusted.jsonl"
        engine = PyrionEngine(other, TRUSTED_ACTORS)
        with self.assertRaises(PolicyError):
            engine.register_mission(
                simple_mission(),
                {"actor_id": "agent:test", "actor_type": "human"},
            )

        scope = action_scope_hash(self.mission, self.mission["candidate_actions"][1])
        self.engine.record_event(event("evt.apr.forged", "approval.decided", {
            "approval_id": "apr.release", "action_id": "act.release",
            "decision": "approved", "scope_hash": scope,
        }, 1, "human", actor_id="agent:test"))
        assessment = self.assess("2026-08-22T12:00:02Z")
        self.assertEqual(0, assessment["scores"]["approval"])
        self.assertIn("UNTRUSTED_AUTHORITY_EVENT", assessment["flags"])

    def test_ignored_untrusted_authority_event_cannot_drive_pet_telemetry(self) -> None:
        self.engine.record_event(event("evt.obs.one", "evidence.observed", {
            "evidence_id": "ev.one", "requirement_id": "req.timeline",
            "source_id": "src.one", "source_ref": "internal://one",
            "content_sha256": SHA_A,
        }, 1))
        self.engine.record_event(event("evt.ver.forged", "evidence.verified", {
            "evidence_id": "ev.one", "verification_ref": "test://forged",
            "content_sha256": SHA_A,
        }, 2, "human", actor_id="agent:test"))
        assessment = self.assess("2026-08-22T12:00:03Z")
        self.assertIn("UNTRUSTED_AUTHORITY_EVENT", assessment["flags"])
        self.assertEqual("review", assessment["pet_state"])
        self.assertNotEqual("running-right", assessment["pet_state"])

    def test_trusted_agent_cannot_grant_human_approval_or_execute(self) -> None:
        scope = action_scope_hash(self.mission, self.mission["candidate_actions"][1])
        self.engine.record_event(event("evt.apr.agent", "approval.decided", {
            "approval_id": "apr.release", "action_id": "act.release",
            "decision": "approved", "scope_hash": scope,
        }, 1, "agent"))
        assessment = self.assess("2026-08-22T12:00:02Z")
        self.assertEqual(0, assessment["scores"]["approval"])
        self.assertFalse(assessment["next_action"]["execution_permitted"])
        self.assertFalse(hasattr(self.engine, "execute"))

    def test_assess_requires_and_checks_trusted_head(self) -> None:
        with self.assertRaises(TypeError):
            self.engine.assess("mis.network95")  # type: ignore[call-arg]
        with self.assertRaises(IntegrityError):
            self.engine.assess(
                "mis.network95", GENESIS_HASH, "2026-08-22T12:00:01Z"
            )
        assessment = self.engine.assess(
            "mis.network95", self.register["head_hash"], "2026-08-22T12:00:01Z"
        )
        self.assertEqual(self.register["head_hash"], assessment["ledger_head_hash"])

    def test_event_id_collision_fails(self) -> None:
        first = event("evt.obs.one", "evidence.observed", {
            "evidence_id": "ev.one", "requirement_id": "req.timeline",
            "source_id": "src.one", "source_ref": "internal://one",
            "content_sha256": SHA_A,
        }, 1)
        self.engine.record_event(first)
        changed = copy.deepcopy(first)
        changed["payload"]["source_ref"] = "internal://different"
        with self.assertRaises(PolicyError):
            self.engine.record_event(changed)

    def test_tampering_and_truncation_fail_closed(self) -> None:
        self.record_minimum_evidence()
        lines = self.ledger.read_text(encoding="utf-8").splitlines()
        entry = json.loads(lines[1])
        entry["event"]["payload"]["source_ref"] = "tampered://source"
        lines[1] = json.dumps(entry, separators=(",", ":"), sort_keys=True)
        self.ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with self.assertRaises(IntegrityError):
            self.engine.verify_ledger()

        other = Path(self.tmp.name) / "truncated.jsonl"
        other.write_text('{"ledger_version":1', encoding="utf-8")
        with self.assertRaises(IntegrityError):
            PyrionEngine(other, TRUSTED_ACTORS).verify_ledger()

    def test_source_id_list_is_rejected_and_bad_replay_is_integrity_error(self) -> None:
        invalid = event("evt.obs.bad", "evidence.observed", {
            "evidence_id": "ev.bad", "requirement_id": "req.timeline",
            "source_id": [], "source_ref": "internal://bad",
            "content_sha256": SHA_A,
        }, 1)
        with self.assertRaises(PolicyError):
            self.engine.record_event(invalid)

        valid = event("evt.obs.one", "evidence.observed", {
            "evidence_id": "ev.one", "requirement_id": "req.timeline",
            "source_id": "src.one", "source_ref": "internal://one",
            "content_sha256": SHA_A,
        }, 1)
        self.engine.record_event(valid)
        lines = self.ledger.read_text(encoding="utf-8").splitlines()
        entry = json.loads(lines[-1])
        entry["event"]["payload"]["source_id"] = []
        unsigned = {key: value for key, value in entry.items() if key != "entry_hash"}
        entry["entry_hash"] = digest(unsigned)
        lines[-1] = canonical(entry).decode("utf-8")
        self.ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with self.assertRaises(IntegrityError):
            self.engine.verify_ledger()

    def test_evidence_formula_and_artifact_independence(self) -> None:
        self.record_minimum_evidence()
        before = self.assess("2026-08-22T12:00:04Z")
        self.assertEqual(68, before["scores"]["evidence"])
        self.assertEqual(0, before["scores"]["artifact"])
        self.assertEqual("verify_evidence", before["next_action"]["kind"])
        self.assertEqual("review", before["pet_state"])

        self.engine.record_event(event("evt.art.one", "artifact.recorded", {
            "artifact_id": "art.log", "location": "library://decision-log",
            "content_sha256": SHA_A,
        }, 4))
        after = self.assess("2026-08-22T12:00:05Z")
        self.assertEqual(68, after["scores"]["evidence"])
        self.assertEqual(50, after["scores"]["artifact"])

    def test_revisions_are_monotonic_current_and_state_isolated(self) -> None:
        self.engine.record_event(event("evt.obs.one", "evidence.observed", {
            "evidence_id": "ev.one", "requirement_id": "req.timeline",
            "source_id": "src.one", "source_ref": "internal://one",
            "content_sha256": SHA_A,
        }, 1))
        skipped = copy.deepcopy(self.mission)
        skipped["revision"] = 3
        skipped["created_at"] = "2026-08-22T12:00:20Z"
        with self.assertRaises(PolicyError):
            self.engine.register_mission(
                skipped, {"actor_id": "human:ark95x", "actor_type": "human"}
            )

        revised = copy.deepcopy(self.mission)
        revised["revision"] = 2
        revised["created_at"] = "2026-08-22T12:00:20Z"
        self.engine.register_mission(
            revised, {"actor_id": "human:ark95x", "actor_type": "human"}
        )
        with self.assertRaises(PolicyError):
            self.engine.record_event(event("evt.obs.stale", "evidence.observed", {
                "evidence_id": "ev.stale", "requirement_id": "req.timeline",
                "source_id": "src.stale", "source_ref": "internal://stale",
                "content_sha256": SHA_A,
            }, 21, revision=1))

        head = self.head()
        earlier = self.engine.assess(
            "mis.network95", head, "2026-08-22T12:00:05Z"
        )
        current = self.engine.assess(
            "mis.network95", head, "2026-08-22T12:00:21Z"
        )
        self.assertEqual(1, earlier["mission_revision"])
        self.assertEqual(18, earlier["scores"]["evidence"])
        self.assertEqual(2, current["mission_revision"])
        self.assertEqual(0, current["scores"]["evidence"])

    def test_every_event_requires_mission_revision(self) -> None:
        candidate = event("evt.obs.one", "evidence.observed", {
            "evidence_id": "ev.one", "requirement_id": "req.timeline",
            "source_id": "src.one", "source_ref": "internal://one",
            "content_sha256": SHA_A,
        }, 1)
        del candidate["mission_revision"]
        with self.assertRaises(PolicyError):
            self.engine.record_event(candidate)

    def approval(self, event_id: str, second: int, *, decision: str = "approved", expires_at: str | None = None, approval_id: str = "apr.release") -> None:
        payload = {
            "approval_id": approval_id,
            "action_id": "act.release",
            "decision": decision,
            "scope_hash": action_scope_hash(
                self.mission, self.mission["candidate_actions"][1]
            ),
        }
        if expires_at:
            payload["expires_at"] = expires_at
        self.engine.record_event(event(event_id, "approval.decided", payload, second, "human"))

    def complete_release(self, event_id: str, second: int) -> None:
        self.engine.record_event(event(event_id, "action.completed", {
            "action_id": "act.release",
            "scope_hash": action_scope_hash(
                self.mission, self.mission["candidate_actions"][1]
            ),
            "result_ref": "external://result", "result_sha256": SHA_A,
        }, second))

    def test_post_hoc_backdated_approval_never_erases_completion_violation(self) -> None:
        candidate = self.mission["candidate_actions"][1]
        candidate["prerequisite_requirement_ids"] = []
        candidate["prerequisite_artifact_ids"] = []
        other = Path(self.tmp.name) / "posthoc.jsonl"
        self.engine = PyrionEngine(other, TRUSTED_ACTORS)
        self.engine.register_mission(
            self.mission, {"actor_id": "human:ark95x", "actor_type": "human"}
        )
        self.complete_release("evt.done.release", 10)
        self.approval("evt.apr.posthoc", 5)
        assessment = self.assess("2026-08-22T12:00:20Z")
        self.assertEqual(100, assessment["scores"]["approval"])
        self.assertIn("UNAPPROVED_HIGH_IMPACT_COMPLETION", assessment["flags"])

    def test_expired_or_denied_approval_is_invalid_at_completion(self) -> None:
        candidate = self.mission["candidate_actions"][1]
        candidate["prerequisite_requirement_ids"] = []
        candidate["prerequisite_artifact_ids"] = []
        other = Path(self.tmp.name) / "expired.jsonl"
        self.engine = PyrionEngine(other, TRUSTED_ACTORS)
        self.engine.register_mission(
            self.mission, {"actor_id": "human:ark95x", "actor_type": "human"}
        )
        self.approval(
            "evt.apr.expiring", 1, expires_at="2026-08-22T12:00:02Z"
        )
        self.complete_release("evt.done.release", 3)
        assessment = self.assess("2026-08-22T12:00:04Z")
        self.assertIn("UNAPPROVED_HIGH_IMPACT_COMPLETION", assessment["flags"])

        denied_ledger = Path(self.tmp.name) / "denied.jsonl"
        self.engine = PyrionEngine(denied_ledger, TRUSTED_ACTORS)
        self.engine.register_mission(
            self.mission, {"actor_id": "human:ark95x", "actor_type": "human"}
        )
        self.approval("evt.apr.yes", 1)
        self.approval("evt.apr.no", 2, decision="denied")
        self.complete_release("evt.done.denied", 3)
        assessment = self.assess("2026-08-22T12:00:04Z")
        self.assertIn("UNAPPROVED_HIGH_IMPACT_COMPLETION", assessment["flags"])

    def test_valid_approval_at_completion_avoids_violation(self) -> None:
        candidate = self.mission["candidate_actions"][1]
        candidate["prerequisite_requirement_ids"] = []
        candidate["prerequisite_artifact_ids"] = []
        other = Path(self.tmp.name) / "valid-approval.jsonl"
        self.engine = PyrionEngine(other, TRUSTED_ACTORS)
        self.engine.register_mission(
            self.mission, {"actor_id": "human:ark95x", "actor_type": "human"}
        )
        self.approval(
            "evt.apr.valid", 1, expires_at="2026-08-22T12:00:05Z"
        )
        self.complete_release("evt.done.release", 3)
        assessment = self.assess("2026-08-22T12:00:04Z")
        self.assertNotIn("UNAPPROVED_ACTION_COMPLETION", assessment["flags"])

    def test_each_approval_gate_requires_its_own_decision(self) -> None:
        self.mission["approval_gates"].append({
            "approval_id": "apr.legal",
            "label": "Legal approval",
            "action_id": "act.release",
            "required_for_completion": True,
        })
        candidate = self.mission["candidate_actions"][1]
        candidate["prerequisite_requirement_ids"] = []
        candidate["prerequisite_artifact_ids"] = []
        other = Path(self.tmp.name) / "two-gates.jsonl"
        self.engine = PyrionEngine(other, TRUSTED_ACTORS)
        self.engine.register_mission(
            self.mission, {"actor_id": "human:ark95x", "actor_type": "human"}
        )
        self.approval("evt.apr.release", 1)
        self.complete_release("evt.done.release", 2)
        assessment = self.assess("2026-08-22T12:00:03Z")
        self.assertEqual(50, assessment["scores"]["approval"])
        self.assertIn("UNAPPROVED_HIGH_IMPACT_COMPLETION", assessment["flags"])

    def test_explicit_low_impact_human_approval_is_enforced(self) -> None:
        candidate = simple_mission()
        action = candidate["candidate_actions"][0]
        action["requires_human_approval"] = True
        candidate["approval_gates"] = [{
            "approval_id": "apr.draft",
            "label": "Draft approval",
            "action_id": "act.draft",
            "required_for_completion": True,
        }]
        other = Path(self.tmp.name) / "explicit-approval.jsonl"
        engine = PyrionEngine(other, TRUSTED_ACTORS)
        registered = engine.register_mission(
            candidate, {"actor_id": "human:ark95x", "actor_type": "human"}
        )
        assessment = engine.assess(
            candidate["mission_id"], registered["head_hash"],
            "2026-08-22T12:00:01Z",
        )
        self.assertIn("APPROVAL_MISSING", assessment["flags"])
        self.assertEqual("request_human_approval", assessment["next_action"]["kind"])

    def test_optional_candidate_prerequisites_control_eligibility(self) -> None:
        candidate = simple_mission()
        candidate["evidence_requirements"] = [{
            "requirement_id": "req.timeline", "label": "Optional evidence",
            "weight": 5, "minimum_verified_sources": 1, "required": False,
        }]
        candidate["artifact_requirements"] = [{
            "artifact_id": "art.log", "label": "Optional artifact",
            "weight": 3, "required": False, "verification_required": True,
        }]
        action = candidate["candidate_actions"][0]
        action["prerequisite_requirement_ids"] = ["req.timeline"]
        action["prerequisite_artifact_ids"] = ["art.log"]
        other = Path(self.tmp.name) / "prerequisites.jsonl"
        engine = PyrionEngine(other, TRUSTED_ACTORS)
        registered = engine.register_mission(
            candidate, {"actor_id": "human:ark95x", "actor_type": "human"}
        )
        first = engine.assess(
            candidate["mission_id"], registered["head_hash"],
            "2026-08-22T12:00:01Z",
        )
        self.assertEqual("collect_evidence", first["next_action"]["kind"])
        self.assertIn("ACTION_PREREQUISITE", first["next_action"]["rationale_codes"])

        engine.record_event(event("evt.obs.optional", "evidence.observed", {
            "evidence_id": "ev.optional", "requirement_id": "req.timeline",
            "source_id": "src.optional", "source_ref": "internal://optional",
            "content_sha256": SHA_A,
        }, 1))
        engine.record_event(event("evt.ver.optional", "evidence.verified", {
            "evidence_id": "ev.optional", "verification_ref": "test://optional",
            "content_sha256": SHA_A,
        }, 2, "human"))
        second = engine.assess(
            candidate["mission_id"], engine.verify_ledger()["head_hash"],
            "2026-08-22T12:00:03Z",
        )
        self.assertEqual("locate_or_verify_artifact", second["next_action"]["kind"])

        engine.record_event(event("evt.art.optional", "artifact.recorded", {
            "artifact_id": "art.log", "location": "library://optional",
            "content_sha256": SHA_B,
        }, 3))
        engine.record_event(event("evt.art.optional.ver", "artifact.verified", {
            "artifact_id": "art.log", "verification_ref": "test://optional",
            "content_sha256": SHA_B,
        }, 4, "human"))
        ready = engine.assess(
            candidate["mission_id"], engine.verify_ledger()["head_hash"],
            "2026-08-22T12:00:05Z",
        )
        self.assertEqual("prepare_safe_action", ready["next_action"]["kind"])

    def test_premature_completion_is_immutably_flagged(self) -> None:
        self.complete_release("evt.done.premature", 1)
        assessment = self.assess("2026-08-22T12:00:02Z")
        self.assertIn("ACTION_PREREQUISITES_UNMET_AT_COMPLETION", assessment["flags"])
        self.assertLessEqual(assessment["scores"]["readiness"], 25)

    def test_invalid_completion_attempt_does_not_complete_or_remove_action(self) -> None:
        other = Path(self.tmp.name) / "invalid-completion.jsonl"
        candidate = simple_mission()
        engine = PyrionEngine(other, TRUSTED_ACTORS)
        engine.register_mission(
            candidate, {"actor_id": "human:ark95x", "actor_type": "human"}
        )
        engine.record_event(event("evt.done.invalid", "action.completed", {
            "action_id": "act.draft", "scope_hash": SHA_B,
            "result_ref": "internal://invalid", "result_sha256": SHA_A,
        }, 1))
        assessment = engine.assess(
            candidate["mission_id"], engine.verify_ledger()["head_hash"],
            "2026-08-22T12:00:02Z",
        )
        self.assertIn("ACTION_SCOPE_MISMATCH", assessment["flags"])
        self.assertEqual("prepare_safe_action", assessment["next_action"]["kind"])
        self.assertEqual("act.draft", assessment["next_action"]["target_id"])
        self.assertNotEqual("running-right", assessment["pet_state"])

    def test_terminal_status_precedes_work_and_completed_actions_do_not_repeat(self) -> None:
        self.engine.record_event(event("evt.status.complete", "mission.status_changed", {
            "status": "complete", "reason": "closed",
        }, 1, "human"))
        complete = self.assess("2026-08-22T12:00:02Z")
        self.assertEqual("review_and_anchor_closure", complete["next_action"]["kind"])

        other = Path(self.tmp.name) / "completed-action.jsonl"
        candidate = simple_mission()
        engine = PyrionEngine(other, TRUSTED_ACTORS)
        engine.register_mission(
            candidate, {"actor_id": "human:ark95x", "actor_type": "human"}
        )
        action = candidate["candidate_actions"][0]
        engine.record_event(event("evt.done.draft", "action.completed", {
            "action_id": "act.draft", "scope_hash": action_scope_hash(candidate, action),
            "result_ref": "internal://draft", "result_sha256": SHA_A,
        }, 1))
        assessment = engine.assess(
            candidate["mission_id"], engine.verify_ledger()["head_hash"],
            "2026-08-22T12:00:02Z",
        )
        self.assertEqual("review_and_anchor_closure", assessment["next_action"]["kind"])
        self.assertNotEqual("act.draft", assessment["next_action"]["target_id"])

        cancelled_ledger = Path(self.tmp.name) / "cancelled.jsonl"
        engine = PyrionEngine(cancelled_ledger, TRUSTED_ACTORS)
        engine.register_mission(
            candidate, {"actor_id": "human:ark95x", "actor_type": "human"}
        )
        engine.record_event(event("evt.status.cancelled", "mission.status_changed", {
            "status": "cancelled", "reason": "owner cancelled",
        }, 1, "human"))
        cancelled = engine.assess(
            candidate["mission_id"], engine.verify_ledger()["head_hash"],
            "2026-08-22T12:00:02Z",
        )
        self.assertEqual("reconcile_cancelled_mission", cancelled["next_action"]["kind"])

    def test_as_of_replay_ignores_later_event(self) -> None:
        self.record_minimum_evidence()
        head = self.head()
        early = self.engine.assess(
            "mis.network95", head, "2026-08-22T12:00:02Z"
        )
        later = self.engine.assess(
            "mis.network95", head, "2026-08-22T12:00:04Z"
        )
        self.assertEqual(50, early["scores"]["evidence"])
        self.assertEqual(68, later["scores"]["evidence"])

    def test_windows_locking_fallback_is_used_when_fcntl_is_absent(self) -> None:
        class FakeMSVCRT:
            LK_LOCK = 1
            LK_UNLCK = 2

            def __init__(self) -> None:
                self.calls: list[tuple[int, int]] = []

            def locking(self, _fd: int, mode: int, count: int) -> None:
                self.calls.append((mode, count))

        fake = FakeMSVCRT()
        other = Path(self.tmp.name) / "windows-lock.jsonl"
        engine = PyrionEngine(other, TRUSTED_ACTORS)
        with mock.patch.object(engine_module, "fcntl", None), mock.patch.object(
            engine_module, "msvcrt", fake
        ):
            with engine._locked_file():
                pass
        self.assertEqual([(fake.LK_LOCK, 1), (fake.LK_UNLCK, 1)], fake.calls)


if __name__ == "__main__":
    unittest.main()
