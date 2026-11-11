"""Tamper-evident mission assessment for Pyrion-95.

This package records facts and proposes one next action. It intentionally has
no network, shell, credential, connector, or external-execution interface.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterator

try:  # pragma: no cover - exercised on Unix CI
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None

try:  # pragma: no cover - Windows-only fallback
    import msvcrt
except ImportError:  # pragma: no cover - Unix
    msvcrt = None

GENESIS_HASH = "0" * 64
ID_PATTERN = re.compile(r"^[a-z][a-z0-9._:-]{2,63}$")
HEX64_PATTERN = re.compile(r"^[0-9a-f]{64}$")
SUPPORTED_EVENTS = {
    "mission.registered",
    "mission.status_changed",
    "evidence.observed",
    "evidence.verified",
    "evidence.rejected",
    "artifact.recorded",
    "artifact.verified",
    "risk.observed",
    "risk.mitigation_verified",
    "risk.resolved",
    "approval.decided",
    "action.completed",
    "action.failed",
}
EVENT_REQUIRED_PAYLOAD = {
    "mission.registered": {"mission"},
    "mission.status_changed": {"status", "reason"},
    "evidence.observed": {"evidence_id", "requirement_id", "source_id", "source_ref", "content_sha256"},
    "evidence.verified": {"evidence_id", "verification_ref", "content_sha256"},
    "evidence.rejected": {"evidence_id", "reason_code"},
    "artifact.recorded": {"artifact_id", "location", "content_sha256"},
    "artifact.verified": {"artifact_id", "verification_ref", "content_sha256"},
    "risk.observed": {"risk_id", "description", "severity", "likelihood"},
    "risk.mitigation_verified": {"risk_id", "effectiveness_bp", "control_ref"},
    "risk.resolved": {"risk_id", "resolution_ref"},
    "approval.decided": {"approval_id", "action_id", "decision", "scope_hash"},
    "action.completed": {"action_id", "scope_hash", "result_ref", "result_sha256"},
    "action.failed": {"action_id", "scope_hash", "reason_code"},
}
HIGH_IMPACT_KINDS = {
    "external_write",
    "financial",
    "legal_filing",
    "safety_control",
    "credential_change",
    "destructive",
    "publication",
    "deployment",
}
MAX_EVENT_BYTES = 1_048_576


class IntegrityError(RuntimeError):
    """The append-only ledger cannot be trusted."""


class PolicyError(ValueError):
    """A mission or event violates the closed schema/policy."""


def canonical(value: Any) -> bytes:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PolicyError(f"value is not canonical JSON: {exc}") from exc
    return encoded


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise PolicyError("timestamp must be UTC and end in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise PolicyError(f"invalid UTC timestamp: {value}") from exc
    if parsed.tzinfo != timezone.utc:
        raise PolicyError("timestamp must use UTC")
    return parsed


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def require_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        raise PolicyError(f"{label} must match {ID_PATTERN.pattern}")
    return value


def require_int(value: Any, label: str, low: int = 1, high: int = 5) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise PolicyError(f"{label} must be an integer from {low} to {high}")
    return value


def validate_mission(mission: dict[str, Any]) -> None:
    if not isinstance(mission, dict):
        raise PolicyError("mission must be an object")
    required = {
        "schema_version", "mission_id", "revision", "title", "objective",
        "status", "priority", "created_at", "evidence_policy",
        "evidence_requirements", "artifact_requirements", "approval_gates",
        "risk_profile", "candidate_actions",
    }
    allowed = required | {"due_at", "metadata"}
    missing = sorted(required - mission.keys())
    extra = sorted(mission.keys() - allowed)
    if missing or extra:
        raise PolicyError(f"mission fields invalid; missing={missing}, extra={extra}")
    if mission["schema_version"] != "pyrion.mission/v1":
        raise PolicyError("unsupported mission schema_version")
    require_id(mission["mission_id"], "mission_id")
    if isinstance(mission["revision"], bool) or not isinstance(mission["revision"], int) or mission["revision"] < 1:
        raise PolicyError("revision must be an integer >= 1")
    for field in ("title", "objective"):
        if not isinstance(mission[field], str) or not mission[field].strip() or len(mission[field]) > 5000:
            raise PolicyError(f"{field} must be a non-empty bounded string")
    if mission["status"] not in {"planned", "active", "blocked", "complete", "cancelled"}:
        raise PolicyError("invalid mission status")
    require_int(mission["priority"], "priority")
    parse_utc(mission["created_at"])
    if mission.get("due_at") is not None:
        parse_utc(mission["due_at"])
    if mission["evidence_policy"] not in {"required", "not_required"}:
        raise PolicyError("invalid evidence_policy")

    for field in (
        "evidence_requirements", "artifact_requirements", "approval_gates",
        "candidate_actions",
    ):
        if not isinstance(mission[field], list):
            raise PolicyError(f"{field} must be a list")

    seen: set[str] = set()
    for req in mission["evidence_requirements"]:
        if not isinstance(req, dict):
            raise PolicyError("each evidence requirement must be an object")
        rid = require_id(req.get("requirement_id"), "requirement_id")
        if rid in seen:
            raise PolicyError(f"duplicate mission id: {rid}")
        seen.add(rid)
        require_int(req.get("weight"), f"{rid}.weight")
        require_int(req.get("minimum_verified_sources"), f"{rid}.minimum_verified_sources", 1, 20)
        if not isinstance(req.get("required"), bool):
            raise PolicyError(f"{rid}.required must be boolean")
    if mission["evidence_policy"] == "required" and not any(
        req.get("required") for req in mission["evidence_requirements"]
    ):
        raise PolicyError("required evidence policy has no required requirement")

    for item in mission["artifact_requirements"]:
        if not isinstance(item, dict):
            raise PolicyError("each artifact requirement must be an object")
        aid = require_id(item.get("artifact_id"), "artifact_id")
        if aid in seen:
            raise PolicyError(f"duplicate mission id: {aid}")
        seen.add(aid)
        require_int(item.get("weight"), f"{aid}.weight")
        if not isinstance(item.get("required"), bool) or not isinstance(item.get("verification_required"), bool):
            raise PolicyError(f"{aid} booleans are invalid")

    action_ids: set[str] = set()
    for action in mission["candidate_actions"]:
        if not isinstance(action, dict):
            raise PolicyError("each candidate action must be an object")
        action_id = require_id(action.get("action_id"), "action_id")
        if action_id in seen:
            raise PolicyError(f"duplicate mission id: {action_id}")
        seen.add(action_id)
        action_ids.add(action_id)
        require_int(action.get("priority"), f"{action_id}.priority")
        if action.get("impact") not in {"low", "medium", "high", "critical"}:
            raise PolicyError(f"{action_id}.impact invalid")
        if (
            not isinstance(action.get("reversible"), bool)
            or not isinstance(action.get("external_side_effect"), bool)
            or not isinstance(action.get("requires_human_approval"), bool)
        ):
            raise PolicyError(f"{action_id} booleans invalid")
        for field in ("prerequisite_requirement_ids", "prerequisite_artifact_ids"):
            if not isinstance(action.get(field), list):
                raise PolicyError(f"{action_id}.{field} must be a list")
        for rid in action.get("prerequisite_requirement_ids", []):
            require_id(rid, f"{action_id}.prerequisite_requirement_id")
            if rid not in {r.get("requirement_id") for r in mission["evidence_requirements"]}:
                raise PolicyError(f"{action_id} references unknown evidence requirement {rid}")
        for aid in action.get("prerequisite_artifact_ids", []):
            require_id(aid, f"{action_id}.prerequisite_artifact_id")
            if aid not in {a.get("artifact_id") for a in mission["artifact_requirements"]}:
                raise PolicyError(f"{action_id} references unknown artifact {aid}")

    approval_actions: set[str] = set()
    for gate in mission["approval_gates"]:
        if not isinstance(gate, dict):
            raise PolicyError("each approval gate must be an object")
        approval_id = require_id(gate.get("approval_id"), "approval_id")
        if approval_id in seen:
            raise PolicyError(f"duplicate mission id: {approval_id}")
        seen.add(approval_id)
        gate_action_id = require_id(gate.get("action_id"), f"{approval_id}.action_id")
        if gate_action_id not in action_ids:
            raise PolicyError(f"{approval_id} references unknown action")
        if not isinstance(gate.get("required_for_completion"), bool):
            raise PolicyError(f"{approval_id}.required_for_completion must be boolean")
        if gate["required_for_completion"]:
            approval_actions.add(gate["action_id"])

    for action in mission["candidate_actions"]:
        high_impact = bool(
            action.get("impact") in {"high", "critical"}
            or not action.get("reversible", True)
            or action.get("external_side_effect")
            or action.get("kind") in HIGH_IMPACT_KINDS
        )
        if (high_impact or action["requires_human_approval"]) and action["action_id"] not in approval_actions:
            raise PolicyError(
                f"{action['action_id']} requires a completion approval gate"
            )

    risk = mission["risk_profile"]
    if not isinstance(risk, dict):
        raise PolicyError("risk_profile must be an object")
    if not isinstance(risk.get("assessed"), bool):
        raise PolicyError("risk_profile.assessed must be boolean")
    if risk["assessed"]:
        require_int(risk.get("severity"), "risk severity")
        require_int(risk.get("likelihood"), "risk likelihood")


def validate_event(event: dict[str, Any]) -> None:
    if not isinstance(event, dict):
        raise PolicyError("event must be an object")
    required = {
        "schema_version", "event_id", "mission_id", "mission_revision",
        "occurred_at", "actor", "type", "payload",
    }
    if set(event) != required:
        raise PolicyError(f"event fields invalid; expected exactly {sorted(required)}")
    if event["schema_version"] != "pyrion.event/v1":
        raise PolicyError("unsupported event schema_version")
    require_id(event["event_id"], "event_id")
    require_id(event["mission_id"], "mission_id")
    if (
        isinstance(event["mission_revision"], bool)
        or not isinstance(event["mission_revision"], int)
        or event["mission_revision"] < 1
    ):
        raise PolicyError("mission_revision must be an integer >= 1")
    parse_utc(event["occurred_at"])
    if event["type"] not in SUPPORTED_EVENTS:
        raise PolicyError(f"unsupported event type: {event['type']}")
    actor = event["actor"]
    if not isinstance(actor, dict) or set(actor) != {"actor_id", "actor_type"}:
        raise PolicyError("actor must contain exactly actor_id and actor_type")
    if actor["actor_type"] not in {"human", "agent", "system", "tool"}:
        raise PolicyError("invalid actor_type")
    require_id(actor["actor_id"], "actor_id")
    if not isinstance(event["payload"], dict):
        raise PolicyError("event payload must be an object")
    payload = event["payload"]
    missing_payload = sorted(EVENT_REQUIRED_PAYLOAD[event["type"]] - payload.keys())
    if missing_payload:
        raise PolicyError(f"{event['type']} missing payload fields {missing_payload}")
    for key, value in payload.items():
        if key.endswith("_id"):
            require_id(value, key)
        if key in {"content_sha256", "result_sha256", "scope_hash"}:
            if not isinstance(value, str) or not HEX64_PATTERN.fullmatch(value):
                raise PolicyError(f"{key} must be 64 lowercase hex characters")
    if event["type"] == "mission.status_changed" and payload["status"] not in {"planned", "active", "blocked", "complete", "cancelled"}:
        raise PolicyError("mission.status_changed status invalid")
    if event["type"] == "approval.decided" and payload["decision"] not in {"approved", "denied"}:
        raise PolicyError("approval decision invalid")
    if event["type"] == "risk.observed":
        require_int(payload["severity"], "risk severity")
        require_int(payload["likelihood"], "risk likelihood")
    if event["type"] == "risk.mitigation_verified":
        effectiveness = payload["effectiveness_bp"]
        if isinstance(effectiveness, bool) or not isinstance(effectiveness, int) or not 0 <= effectiveness <= 10_000:
            raise PolicyError("effectiveness_bp must be an integer from 0 to 10000")
    if payload.get("expires_at") is not None:
        parse_utc(payload["expires_at"])
    if len(canonical(event)) > MAX_EVENT_BYTES:
        raise PolicyError("event exceeds 1 MiB")
    if event["type"] == "mission.registered":
        mission = event["payload"].get("mission")
        if not isinstance(mission, dict):
            raise PolicyError("mission.registered requires payload.mission")
        validate_mission(mission)
        if mission["mission_id"] != event["mission_id"]:
            raise PolicyError("registered mission_id mismatch")
        if mission["revision"] != event["mission_revision"]:
            raise PolicyError("registered mission_revision mismatch")


def action_scope_hash(mission: dict[str, Any], action: dict[str, Any]) -> str:
    return digest({
        "mission_id": mission["mission_id"],
        "mission_revision": mission["revision"],
        "action_id": action["action_id"],
        "kind": action.get("kind"),
        "description": action.get("description"),
        "impact": action.get("impact"),
        "reversible": action.get("reversible"),
        "external_side_effect": action.get("external_side_effect"),
        "requires_human_approval": action.get("requires_human_approval"),
        "prerequisites": {
            "evidence": action.get("prerequisite_requirement_ids", []),
            "artifacts": action.get("prerequisite_artifact_ids", []),
        },
    })


def round_half_up(value: Fraction) -> int:
    return (value.numerator * 2 + value.denominator) // (2 * value.denominator)


def weighted_mean(items: list[tuple[int, int]], default: int = 10_000) -> int:
    total_weight = sum(weight for _, weight in items)
    if not total_weight:
        return default
    return round_half_up(Fraction(sum(score * weight for score, weight in items), total_weight))


class PyrionEngine:
    """Append facts, verify a trusted chain, and propose without executing."""

    _AUTHORITY_EVENTS = {
        "mission.status_changed",
        "evidence.verified",
        "evidence.rejected",
        "artifact.verified",
        "risk.mitigation_verified",
        "risk.resolved",
        "approval.decided",
        "action.completed",
        "action.failed",
    }

    def __init__(
        self,
        ledger_path: str | Path,
        trusted_actors: dict[str, str] | None = None,
    ):
        self.ledger_path = Path(ledger_path)
        if trusted_actors is None:
            trusted_actors = {}
        if not isinstance(trusted_actors, dict):
            raise PolicyError("trusted_actors must be an actor_id to actor_type mapping")
        self._trusted_actors: dict[str, str] = {}
        for actor_id, actor_type in trusted_actors.items():
            require_id(actor_id, "trusted actor_id")
            if actor_type not in {"human", "agent", "system", "tool"}:
                raise PolicyError(f"invalid trusted actor_type for {actor_id}")
            self._trusted_actors[actor_id] = actor_type

    def _trusted_actor_type(self, event: dict[str, Any]) -> str | None:
        actor = event["actor"]
        trusted_type = self._trusted_actors.get(actor["actor_id"])
        if trusted_type != actor["actor_type"]:
            return None
        return trusted_type

    @contextlib.contextmanager
    def _locked_file(self) -> Iterator[Any]:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if self.ledger_path.exists() and self.ledger_path.is_symlink():
            raise IntegrityError("refusing symlink ledger")
        flags = os.O_RDWR | os.O_CREAT | os.O_APPEND
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(self.ledger_path, flags, 0o600)
        handle = os.fdopen(fd, "r+", encoding="utf-8", newline="")
        unix_locked = False
        windows_locked = False
        windows_lock_handle: Any | None = None
        try:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                unix_locked = True
            elif msvcrt is not None:  # pragma: no cover - Windows only
                lock_path = self.ledger_path.with_name(self.ledger_path.name + ".lock")
                if lock_path.exists() and lock_path.is_symlink():
                    raise IntegrityError("refusing symlink lock file")
                lock_flags = os.O_RDWR | os.O_CREAT
                if hasattr(os, "O_NOFOLLOW"):
                    lock_flags |= os.O_NOFOLLOW
                lock_fd = os.open(lock_path, lock_flags, 0o600)
                windows_lock_handle = os.fdopen(lock_fd, "r+b", buffering=0)
                if os.fstat(lock_fd).st_size == 0:
                    windows_lock_handle.write(b"\0")
                windows_lock_handle.seek(0)
                msvcrt.locking(
                    windows_lock_handle.fileno(), msvcrt.LK_LOCK, 1
                )
                windows_locked = True
            else:  # pragma: no cover - unsupported platform
                raise IntegrityError("no supported process-locking primitive")
            yield handle
        finally:
            if unix_locked:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            elif windows_locked:  # pragma: no cover - Windows only
                windows_lock_handle.seek(0)
                msvcrt.locking(
                    windows_lock_handle.fileno(), msvcrt.LK_UNLCK, 1
                )
            if windows_lock_handle is not None:
                windows_lock_handle.close()
            handle.close()

    @staticmethod
    def _read_and_verify(handle: Any) -> tuple[list[dict[str, Any]], str]:
        handle.seek(0)
        raw = handle.read()
        if raw and not raw.endswith("\n"):
            raise IntegrityError("ledger has a truncated final line")
        entries: list[dict[str, Any]] = []
        previous = GENESIS_HASH
        event_ids: set[str] = set()
        current_revisions: dict[str, int] = {}
        for line_number, line in enumerate(raw.splitlines(), start=1):
            if not line.strip():
                raise IntegrityError(f"blank ledger line {line_number}")
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                raise IntegrityError(f"invalid JSON on ledger line {line_number}") from exc
            required = {
                "ledger_version", "sequence", "recorded_at", "previous_hash",
                "event", "entry_hash",
            }
            if not isinstance(entry, dict) or set(entry) != required:
                raise IntegrityError(f"invalid fields on ledger line {line_number}")
            if (
                entry["ledger_version"] != 1
                or isinstance(entry["sequence"], bool)
                or entry["sequence"] != line_number
            ):
                raise IntegrityError(f"invalid sequence/version on ledger line {line_number}")
            if entry["previous_hash"] != previous:
                raise IntegrityError(f"broken previous hash on ledger line {line_number}")
            supplied = entry["entry_hash"]
            unsigned = {key: value for key, value in entry.items() if key != "entry_hash"}
            if supplied != digest(unsigned):
                raise IntegrityError(f"broken entry hash on ledger line {line_number}")
            try:
                parse_utc(entry["recorded_at"])
                validate_event(entry["event"])
            except (KeyError, TypeError, PolicyError) as exc:
                raise IntegrityError(f"invalid event on ledger line {line_number}: {exc}") from exc
            event = entry["event"]
            event_id = event["event_id"]
            if event_id in event_ids:
                raise IntegrityError(f"duplicate event_id {event_id}")
            event_ids.add(event_id)
            mission_id = event["mission_id"]
            revision = event["mission_revision"]
            current = current_revisions.get(mission_id)
            if event["type"] == "mission.registered":
                expected_revision = 1 if current is None else current + 1
                if revision != expected_revision:
                    raise IntegrityError(
                        f"non-monotonic revision for {mission_id} on ledger line {line_number}"
                    )
                current_revisions[mission_id] = revision
            elif current is None or revision != current:
                raise IntegrityError(
                    f"event revision is not current for {mission_id} on ledger line {line_number}"
                )
            entries.append(entry)
            previous = supplied
        return entries, previous

    @staticmethod
    def _current_mission(
        entries: list[dict[str, Any]], mission_id: str
    ) -> dict[str, Any] | None:
        for entry in reversed(entries):
            event = entry["event"]
            if event["mission_id"] == mission_id and event["type"] == "mission.registered":
                return event["payload"]["mission"]
        return None

    def register_mission(
        self, mission: dict[str, Any], actor: dict[str, str]
    ) -> dict[str, Any]:
        validate_mission(mission)
        event = {
            "schema_version": "pyrion.event/v1",
            "event_id": f"evt.register.{digest({'mission_id': mission['mission_id'], 'revision': mission['revision']})[:16]}",
            "mission_id": mission["mission_id"],
            "mission_revision": mission["revision"],
            "occurred_at": mission["created_at"],
            "actor": actor,
            "type": "mission.registered",
            "payload": {"mission": mission},
        }
        return self.record_event(event)

    def record_event(self, event: dict[str, Any]) -> dict[str, Any]:
        validate_event(event)
        with self._locked_file() as handle:
            entries, head = self._read_and_verify(handle)
            event_bytes = canonical(event)
            for entry in entries:
                if entry["event"]["event_id"] == event["event_id"]:
                    if canonical(entry["event"]) == event_bytes:
                        return {
                            "idempotent": True,
                            "sequence": entry["sequence"],
                            "head_hash": head,
                        }
                    raise PolicyError(f"event_id collision: {event['event_id']}")

            current_mission = self._current_mission(entries, event["mission_id"])
            if event["type"] == "mission.registered":
                if self._trusted_actor_type(event) not in {"human", "system"}:
                    raise PolicyError("mission registration requires a trusted human or system")
                expected_revision = 1 if current_mission is None else current_mission["revision"] + 1
                if event["mission_revision"] != expected_revision:
                    raise PolicyError(
                        f"mission revision must be exactly {expected_revision}"
                    )
            else:
                if current_mission is None:
                    raise PolicyError(f"mission not registered: {event['mission_id']}")
                if event["mission_revision"] != current_mission["revision"]:
                    raise PolicyError("event mission_revision is not the current revision")
                self._validate_event_references(event, current_mission)

            unsigned = {
                "ledger_version": 1,
                "sequence": len(entries) + 1,
                "recorded_at": now_utc(),
                "previous_hash": head,
                "event": event,
            }
            entry = {**unsigned, "entry_hash": digest(unsigned)}
            handle.write(canonical(entry).decode("utf-8") + "\n")
            handle.flush()
            os.fsync(handle.fileno())
            return {
                "idempotent": False,
                "sequence": entry["sequence"],
                "head_hash": entry["entry_hash"],
            }

    @staticmethod
    def _validate_event_references(
        event: dict[str, Any], mission: dict[str, Any]
    ) -> None:
        payload = event["payload"]
        event_type = event["type"]
        actions = {item["action_id"]: item for item in mission["candidate_actions"]}
        requirements = {
            item["requirement_id"] for item in mission["evidence_requirements"]
        }
        artifacts = {item["artifact_id"] for item in mission["artifact_requirements"]}
        if event_type == "evidence.observed" and payload["requirement_id"] not in requirements:
            raise PolicyError("evidence event references an unknown requirement")
        if event_type in {"artifact.recorded", "artifact.verified"} and payload["artifact_id"] not in artifacts:
            raise PolicyError("artifact event references an unknown artifact")
        if event_type in {"action.completed", "action.failed"} and payload["action_id"] not in actions:
            raise PolicyError("action event references an unknown action")
        if event_type == "approval.decided":
            gates = {
                gate["approval_id"]: gate for gate in mission["approval_gates"]
            }
            gate = gates.get(payload["approval_id"])
            if gate is None or gate["action_id"] != payload["action_id"]:
                raise PolicyError("approval event does not match a mission approval gate")

    def verify_ledger(self, expected_head_hash: str | None = None) -> dict[str, Any]:
        if expected_head_hash is not None and not HEX64_PATTERN.fullmatch(expected_head_hash):
            raise PolicyError("expected_head_hash must be 64 lowercase hex characters")
        with self._locked_file() as handle:
            entries, head = self._read_and_verify(handle)
            if expected_head_hash is not None and expected_head_hash != head:
                raise IntegrityError("ledger head does not match trusted anchor")
        return {"valid": True, "entries": len(entries), "head_hash": head}

    def assess(
        self,
        mission_id: str,
        expected_head_hash: str,
        as_of: str | None = None,
    ) -> dict[str, Any]:
        require_id(mission_id, "mission_id")
        if not isinstance(expected_head_hash, str) or not HEX64_PATTERN.fullmatch(expected_head_hash):
            raise PolicyError("expected_head_hash is required and must be 64 lowercase hex characters")
        cutoff = parse_utc(as_of) if as_of else None
        evaluated_at = as_of or now_utc()
        with self._locked_file() as handle:
            entries, head = self._read_and_verify(handle)
            if expected_head_hash != head:
                raise IntegrityError("ledger head does not match trusted anchor")
            events = [
                entry["event"]
                for entry in entries
                if entry["event"]["mission_id"] == mission_id
                and (
                    cutoff is None
                    or parse_utc(entry["event"]["occurred_at"]) <= cutoff
                )
            ]
        return self._assess_events(mission_id, events, head, evaluated_at)

    def _assess_events(
        self,
        mission_id: str,
        events: list[dict[str, Any]],
        head: str,
        evaluated_at: str,
    ) -> dict[str, Any]:
        registrations = [
            event
            for event in events
            if event["type"] == "mission.registered"
            and self._trusted_actor_type(event) in {"human", "system"}
        ]
        if not registrations:
            raise PolicyError(f"mission not registered by a trusted actor: {mission_id}")
        registration = max(registrations, key=lambda item: item["mission_revision"])
        mission = registration["payload"]["mission"]
        revision = mission["revision"]
        events = [event for event in events if event["mission_revision"] == revision]

        status = mission["status"]
        evidence: dict[str, dict[str, Any]] = {}
        artifacts: dict[str, dict[str, Any]] = {}
        risks: dict[str, dict[str, Any]] = {}
        approvals: dict[str, dict[str, Any]] = {}
        failed_actions: set[str] = set()
        completed_actions: dict[str, dict[str, Any]] = {}
        latest_type = "mission.registered"
        flags: list[str] = []
        actions = {item["action_id"]: item for item in mission["candidate_actions"]}
        gates_by_action: dict[str, list[dict[str, Any]]] = {}
        for gate in mission["approval_gates"]:
            if gate.get("required_for_completion"):
                gates_by_action.setdefault(gate["action_id"], []).append(gate)

        for event in events:
            payload = event["payload"]
            event_type = event["type"]
            trusted_type = self._trusted_actor_type(event)
            if event_type == "mission.registered":
                continue
            if event_type in self._AUTHORITY_EVENTS and trusted_type is None:
                flags.append("UNTRUSTED_AUTHORITY_EVENT")
                continue
            applied = False
            if event_type == "mission.status_changed":
                status = payload["status"]
                applied = True
            elif event_type == "evidence.observed":
                evidence[payload["evidence_id"]] = {
                    **payload, "verified": False, "rejected": False,
                }
                applied = True
            elif event_type == "evidence.verified":
                item = evidence.get(payload["evidence_id"])
                if item and item["content_sha256"] == payload["content_sha256"]:
                    item["verified"] = True
                    item["verification_ref"] = payload["verification_ref"]
                    applied = True
                else:
                    flags.append("EVIDENCE_HASH_MISMATCH")
            elif event_type == "evidence.rejected":
                item = evidence.get(payload["evidence_id"])
                if item:
                    item["rejected"] = True
                    item["verified"] = False
                    applied = True
            elif event_type == "artifact.recorded":
                artifacts[payload["artifact_id"]] = {**payload, "verified": False}
                applied = True
            elif event_type == "artifact.verified":
                item = artifacts.get(payload["artifact_id"])
                if item and item["content_sha256"] == payload["content_sha256"]:
                    item["verified"] = True
                    item["verification_ref"] = payload["verification_ref"]
                    applied = True
                else:
                    flags.append("ARTIFACT_HASH_MISMATCH")
            elif event_type == "risk.observed":
                risks[payload["risk_id"]] = {
                    **payload, "effectiveness_bp": 0, "resolved": False,
                }
                applied = True
            elif event_type == "risk.mitigation_verified":
                risk = risks.get(payload["risk_id"])
                if risk:
                    risk["effectiveness_bp"] = min(9_000, payload["effectiveness_bp"])
                    applied = True
            elif event_type == "risk.resolved":
                risk = risks.get(payload["risk_id"])
                if risk:
                    risk["resolved"] = True
                    applied = True
            elif event_type == "approval.decided":
                approvals[payload["approval_id"]] = {
                    **payload,
                    "actor_id": event["actor"]["actor_id"],
                    "actor_type": trusted_type,
                    "occurred_at": event["occurred_at"],
                }
                applied = True
            elif event_type == "action.failed":
                failed_actions.add(payload["action_id"])
                applied = True
            elif event_type == "action.completed":
                action = actions[payload["action_id"]]
                completion_time = parse_utc(event["occurred_at"])
                expected_scope = action_scope_hash(mission, action)
                scope_valid = payload["scope_hash"] == expected_scope
                if not scope_valid:
                    flags.append("ACTION_SCOPE_MISMATCH")
                prerequisites_valid = self._action_prerequisites_satisfied(
                    mission, action, evidence, artifacts
                )
                if not prerequisites_valid:
                    flags.append("ACTION_PREREQUISITES_UNMET_AT_COMPLETION")
                approval_required = self._action_requires_approval(
                    action, gates_by_action.get(action["action_id"], [])
                )
                approvals_valid = all(
                    self._approval_valid(
                        approvals.get(gate["approval_id"]),
                        gate,
                        action,
                        mission,
                        completion_time,
                    )
                    for gate in gates_by_action.get(action["action_id"], [])
                )
                if approval_required and (not scope_valid or not approvals_valid):
                    flags.append("UNAPPROVED_ACTION_COMPLETION")
                    if self._is_high_impact(action):
                        flags.append("UNAPPROVED_HIGH_IMPACT_COMPLETION")
                completion_valid = bool(
                    scope_valid
                    and prerequisites_valid
                    and (not approval_required or approvals_valid)
                )
                if completion_valid:
                    failed_actions.discard(payload["action_id"])
                    completed_actions[payload["action_id"]] = {
                        **payload, "occurred_at": event["occurred_at"],
                    }
                    applied = True
            if applied:
                latest_type = event_type

        required_evidence = [
            req for req in mission["evidence_requirements"] if req["required"]
        ]
        evidence_components: list[tuple[int, int, str, int, int]] = []
        for req in required_evidence:
            records = [
                item
                for item in evidence.values()
                if item["requirement_id"] == req["requirement_id"]
                and not item["rejected"]
            ]
            verified_sources = {
                item["source_id"] for item in records if item["verified"]
            }
            observed_sources = {
                item["source_id"] for item in records if not item["verified"]
            } - verified_sources
            minimum = req["minimum_verified_sources"]
            score = round_half_up(
                Fraction(
                    min(len(verified_sources), minimum) * 10_000
                    + min(
                        len(observed_sources),
                        max(0, minimum - len(verified_sources)),
                    )
                    * 3_500,
                    minimum,
                )
            )
            evidence_components.append(
                (
                    min(10_000, score), req["weight"], req["requirement_id"],
                    len(verified_sources), len(observed_sources),
                )
            )
        evidence_bp = weighted_mean(
            [(score, weight) for score, weight, *_ in evidence_components],
            10_000 if mission["evidence_policy"] == "not_required" else 0,
        )

        required_artifacts = [
            item for item in mission["artifact_requirements"] if item["required"]
        ]
        artifact_components: list[tuple[int, int, str]] = []
        for req in required_artifacts:
            record = artifacts.get(req["artifact_id"])
            if not record:
                score = 0
            elif req["verification_required"] and not record["verified"]:
                score = 5_000
            else:
                score = 10_000
            artifact_components.append((score, req["weight"], req["artifact_id"]))
        artifact_bp = weighted_mean(
            [(score, weight) for score, weight, _ in artifact_components]
        )

        completion_gates = [
            gate for gate in mission["approval_gates"] if gate["required_for_completion"]
        ]
        approval_components: list[tuple[int, str]] = []
        evaluated_time = parse_utc(evaluated_at)
        for gate in completion_gates:
            action = actions[gate["action_id"]]
            valid = self._approval_valid(
                approvals.get(gate["approval_id"]),
                gate,
                action,
                mission,
                evaluated_time,
            )
            approval_components.append((10_000 if valid else 0, gate["approval_id"]))
        approval_bp = weighted_mean([(score, 1) for score, _ in approval_components])

        risk_profile = mission["risk_profile"]
        residuals: list[Fraction] = []
        if risk_profile["assessed"]:
            residuals.append(
                Fraction(risk_profile["severity"] * risk_profile["likelihood"], 25)
            )
        for risk in risks.values():
            if risk["resolved"]:
                continue
            exposure = Fraction(risk["severity"] * risk["likelihood"], 25)
            residuals.append(
                exposure
                * Fraction(10_000 - risk.get("effectiveness_bp", 0), 10_000)
            )
        if not residuals:
            risk_bp = 5_000
            flags.append("RISK_UNASSESSED")
        else:
            safe_product = Fraction(1, 1)
            for residual in residuals:
                safe_product *= 1 - residual
            risk_bp = round_half_up((1 - safe_product) * 10_000)

        missing_approval_actions: list[str] = []
        for action in actions.values():
            if action["action_id"] in completed_actions:
                continue
            gates = gates_by_action.get(action["action_id"], [])
            if not self._action_requires_approval(action, gates):
                continue
            if not all(
                self._approval_valid(
                    approvals.get(gate["approval_id"]),
                    gate,
                    action,
                    mission,
                    evaluated_time,
                )
                for gate in gates
            ):
                missing_approval_actions.append(action["action_id"])

        readiness_bp = round_half_up(
            Fraction(50, 100) * evidence_bp
            + Fraction(25, 100) * (10_000 - risk_bp)
            + Fraction(15, 100) * artifact_bp
            + Fraction(10, 100) * approval_bp
        )
        if status == "blocked":
            readiness_bp = min(readiness_bp, 2_500)
        if any(residual >= Fraction(80, 100) for residual in residuals):
            readiness_bp = min(readiness_bp, 3_500)
        if any(score == 0 for score, *_ in evidence_components):
            readiness_bp = min(readiness_bp, 5_900)
        if status == "planned":
            readiness_bp = min(readiness_bp, 6_000)
        if missing_approval_actions:
            flags.append("APPROVAL_MISSING")
            readiness_bp = min(readiness_bp, 4_900)
        if {
            "UNAPPROVED_ACTION_COMPLETION",
            "ACTION_SCOPE_MISMATCH",
            "ACTION_PREREQUISITES_UNMET_AT_COMPLETION",
        } & set(flags):
            readiness_bp = min(readiness_bp, 2_500)

        next_action = self._next_action(
            mission,
            status,
            evidence_components,
            evidence,
            artifact_components,
            artifacts,
            risk_bp,
            missing_approval_actions,
            actions,
            approvals,
            gates_by_action,
            set(completed_actions),
            failed_actions,
            evaluated_time,
        )
        if failed_actions:
            pet_state = "failed"
        elif status == "complete" and readiness_bp >= 8_000 and risk_bp < 5_000:
            pet_state = "jumping"
        elif status == "cancelled":
            pet_state = "idle"
        elif status == "blocked" or next_action["kind"] in {
            "request_human_approval", "request_blocker_resolution",
        }:
            pet_state = "waiting"
        elif risk_bp >= 5_000 or any(
            observed for *_, observed in evidence_components
        ):
            pet_state = "review"
        elif latest_type in {"evidence.verified", "artifact.verified", "action.completed"}:
            pet_state = "running-right"
        elif latest_type in {"evidence.rejected", "risk.observed"}:
            pet_state = "running-left"
        elif next_action["kind"] in {
            "define_next_action", "reconcile_cancelled_mission",
        }:
            pet_state = "idle"
        else:
            pet_state = "running"

        return {
            "schema_version": "pyrion.assessment/v1",
            "scoring_version": "pyrion.score/v1",
            "policy_version": "pyrion.policy/v1",
            "mission_id": mission_id,
            "mission_revision": revision,
            "evaluated_at": evaluated_at,
            "ledger_head_hash": head,
            "scores": {
                "evidence": round_half_up(Fraction(evidence_bp, 100)),
                "artifact": round_half_up(Fraction(artifact_bp, 100)),
                "approval": round_half_up(Fraction(approval_bp, 100)),
                "risk": round_half_up(Fraction(risk_bp, 100)),
                "readiness": round_half_up(Fraction(readiness_bp, 100)),
            },
            "flags": sorted(set(flags)),
            "pet_state": pet_state,
            "next_action": next_action,
            "components": {
                "evidence_requirements": [
                    {
                        "requirement_id": req_id,
                        "score": round_half_up(Fraction(score, 100)),
                        "verified_sources": verified,
                        "observed_sources": observed,
                    }
                    for score, _weight, req_id, verified, observed
                    in evidence_components
                ],
                "artifact_gates": [
                    {
                        "artifact_id": artifact_id,
                        "score": round_half_up(Fraction(score, 100)),
                    }
                    for score, _weight, artifact_id in artifact_components
                ],
                "approval_gates": [
                    {
                        "approval_id": approval_id,
                        "score": round_half_up(Fraction(score, 100)),
                    }
                    for score, approval_id in approval_components
                ],
                "active_risks": len(
                    [risk for risk in risks.values() if not risk["resolved"]]
                ),
            },
        }

    @staticmethod
    def _is_high_impact(action: dict[str, Any]) -> bool:
        return bool(
            action.get("impact") in {"high", "critical"}
            or not action.get("reversible", True)
            or action.get("external_side_effect")
            or action.get("kind") in HIGH_IMPACT_KINDS
        )

    @classmethod
    def _action_requires_approval(
        cls, action: dict[str, Any], gates: list[dict[str, Any]]
    ) -> bool:
        return bool(
            cls._is_high_impact(action)
            or action.get("requires_human_approval")
            or gates
        )

    @staticmethod
    def _approval_valid(
        approval: dict[str, Any] | None,
        gate: dict[str, Any],
        action: dict[str, Any],
        mission: dict[str, Any],
        at: datetime,
    ) -> bool:
        if not approval:
            return False
        if (
            approval.get("approval_id") != gate["approval_id"]
            or approval.get("action_id") != action["action_id"]
            or approval.get("decision") != "approved"
            or approval.get("actor_type") != "human"
            or approval.get("scope_hash") != action_scope_hash(mission, action)
        ):
            return False
        if parse_utc(approval["occurred_at"]) > at:
            return False
        expires_at = approval.get("expires_at")
        return expires_at is None or parse_utc(expires_at) >= at

    @staticmethod
    def _requirement_satisfied(
        mission: dict[str, Any],
        requirement_id: str,
        evidence: dict[str, dict[str, Any]],
    ) -> bool:
        requirement = next(
            item
            for item in mission["evidence_requirements"]
            if item["requirement_id"] == requirement_id
        )
        verified_sources = {
            item["source_id"]
            for item in evidence.values()
            if item["requirement_id"] == requirement_id
            and item.get("verified")
            and not item.get("rejected")
        }
        return len(verified_sources) >= requirement["minimum_verified_sources"]

    @staticmethod
    def _artifact_satisfied(
        mission: dict[str, Any],
        artifact_id: str,
        artifacts: dict[str, dict[str, Any]],
    ) -> bool:
        requirement = next(
            item
            for item in mission["artifact_requirements"]
            if item["artifact_id"] == artifact_id
        )
        record = artifacts.get(artifact_id)
        return bool(
            record
            and (
                not requirement["verification_required"]
                or record.get("verified")
            )
        )

    @classmethod
    def _action_prerequisites_satisfied(
        cls,
        mission: dict[str, Any],
        action: dict[str, Any],
        evidence: dict[str, dict[str, Any]],
        artifacts: dict[str, dict[str, Any]],
    ) -> bool:
        return all(
            cls._requirement_satisfied(mission, requirement_id, evidence)
            for requirement_id in action["prerequisite_requirement_ids"]
        ) and all(
            cls._artifact_satisfied(mission, artifact_id, artifacts)
            for artifact_id in action["prerequisite_artifact_ids"]
        )

    @staticmethod
    def _proposal(
        mission: dict[str, Any],
        kind: str,
        target: str | None,
        summary: str,
        rationale: list[str],
        blocked_action: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        basis = {
            "mission_id": mission["mission_id"],
            "revision": mission["revision"],
            "kind": kind,
            "target": target,
            "rationale": rationale,
        }
        result = {
            "proposal_id": f"prp.{digest(basis)[:16]}",
            "kind": kind,
            "target_id": target,
            "summary": summary,
            "rationale_codes": rationale,
            "impact": "low",
            "requires_human_approval": False,
            "execution_permitted": False,
        }
        if blocked_action:
            result["blocked_action_id"] = blocked_action["action_id"]
            result["blocked_action_scope_hash"] = action_scope_hash(
                mission, blocked_action
            )
        return result

    @classmethod
    def _next_action(
        cls,
        mission: dict[str, Any],
        status: str,
        evidence_components: list[tuple[int, int, str, int, int]],
        evidence: dict[str, dict[str, Any]],
        artifact_components: list[tuple[int, int, str]],
        artifacts: dict[str, dict[str, Any]],
        risk_bp: int,
        missing_approval_actions: list[str],
        actions: dict[str, dict[str, Any]],
        approvals: dict[str, dict[str, Any]],
        gates_by_action: dict[str, list[dict[str, Any]]],
        completed_actions: set[str],
        failed_actions: set[str],
        evaluated_time: datetime,
    ) -> dict[str, Any]:
        if status == "complete":
            return cls._proposal(
                mission,
                "review_and_anchor_closure",
                None,
                "Review and anchor mission closure",
                ["MISSION_COMPLETE"],
            )
        if status == "cancelled":
            return cls._proposal(
                mission,
                "reconcile_cancelled_mission",
                None,
                "Reconcile the cancelled mission without further action",
                ["MISSION_CANCELLED"],
            )
        if failed_actions:
            action_id = sorted(failed_actions)[0]
            return cls._proposal(
                mission,
                "recover_failed_action",
                action_id,
                "Review failure evidence before retrying",
                ["ACTION_FAILED"],
            )
        if not mission["risk_profile"]["assessed"]:
            return cls._proposal(
                mission, "assess_risk", None, "Assess mission risk", ["RISK_UNASSESSED"]
            )
        if risk_bp >= 8_000:
            return cls._proposal(
                mission,
                "draft_risk_mitigation_plan",
                None,
                "Draft a risk mitigation plan",
                ["CRITICAL_RISK"],
            )
        for item in evidence.values():
            if not item.get("verified") and not item.get("rejected"):
                return cls._proposal(
                    mission,
                    "verify_evidence",
                    item["evidence_id"],
                    "Verify observed evidence",
                    ["EVIDENCE_UNVERIFIED"],
                )
        for score, _weight, requirement_id, _verified, _observed in evidence_components:
            if score == 0:
                return cls._proposal(
                    mission,
                    "collect_evidence",
                    requirement_id,
                    "Collect traceable evidence",
                    ["EVIDENCE_MISSING"],
                )
        for score, _weight, artifact_id in artifact_components:
            if score < 10_000:
                return cls._proposal(
                    mission,
                    "locate_or_verify_artifact",
                    artifact_id,
                    "Locate or verify the required artifact",
                    ["ARTIFACT_NOT_VALIDATED"],
                )
        if status == "blocked":
            return cls._proposal(
                mission,
                "request_blocker_resolution",
                None,
                "Request resolution of the recorded blocker",
                ["MISSION_BLOCKED"],
            )

        remaining = [
            action
            for action in actions.values()
            if action["action_id"] not in completed_actions
        ]
        if not remaining:
            return cls._proposal(
                mission,
                "review_and_anchor_closure",
                None,
                "Review completed actions and anchor closure",
                ["ALL_ACTIONS_COMPLETED"],
            )
        ordered = sorted(
            remaining, key=lambda item: (-item["priority"], item["action_id"])
        )
        eligible = [
            action
            for action in ordered
            if cls._action_prerequisites_satisfied(
                mission, action, evidence, artifacts
            )
        ]
        for action in ordered:
            if action in eligible:
                continue
            for requirement_id in action["prerequisite_requirement_ids"]:
                if not cls._requirement_satisfied(
                    mission, requirement_id, evidence
                ):
                    return cls._proposal(
                        mission,
                        "collect_evidence",
                        requirement_id,
                        "Satisfy the candidate action evidence prerequisite",
                        ["ACTION_PREREQUISITE"],
                    )
            for artifact_id in action["prerequisite_artifact_ids"]:
                if not cls._artifact_satisfied(mission, artifact_id, artifacts):
                    return cls._proposal(
                        mission,
                        "locate_or_verify_artifact",
                        artifact_id,
                        "Satisfy the candidate action artifact prerequisite",
                        ["ACTION_PREREQUISITE"],
                    )

        missing = set(missing_approval_actions)
        for action in eligible:
            gates = gates_by_action.get(action["action_id"], [])
            if cls._action_requires_approval(action, gates):
                if action["action_id"] in missing:
                    return cls._proposal(
                        mission,
                        "request_human_approval",
                        action["action_id"],
                        "Request exact, scoped human approval",
                        ["APPROVAL_MISSING"],
                        action,
                    )
                if all(
                    cls._approval_valid(
                        approvals.get(gate["approval_id"]),
                        gate,
                        action,
                        mission,
                        evaluated_time,
                    )
                    for gate in gates
                ):
                    return cls._proposal(
                        mission,
                        "prepare_approved_action",
                        action["action_id"],
                        action.get("description", "Prepare approved action"),
                        ["APPROVAL_VALID", "PREREQUISITES_MET"],
                        action,
                    )
            else:
                return cls._proposal(
                    mission,
                    "prepare_safe_action",
                    action["action_id"],
                    action.get("description", "Prepare safe action"),
                    ["LOW_IMPACT_CANDIDATE", "PREREQUISITES_MET"],
                )
        return cls._proposal(
            mission,
            "define_next_action",
            None,
            "Define the next bounded action",
            ["NO_ELIGIBLE_ACTION"],
        )
