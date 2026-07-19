"""ARK95X single-control-plane authority and reporting contract.

The control plane coordinates existing systems around one state of truth:
ARK-STATE.json. Agents may observe, recommend, veto, route, or execute inside
narrow scopes, but they do not own global state and cannot self-approve.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

CONTROL_PLANE_ID = "ark95x-control-plane"
AUTHORITATIVE_STATE_PATH = "ARK-STATE.json"

APPROVAL_REQUIRED_ACTION_CLASSES = frozenset(
    {
        "account_change",
        "destructive",
        "deployment",
        "financial",
        "legal",
        "public",
        "security_sensitive",
        "system_mutation",
    }
)


@dataclass
class AgentRecord:
    """Registration and current report state for one specialist agent."""

    agent_id: str
    role: str
    capabilities: tuple[str, ...]
    authority_scope: tuple[str, ...]
    state: str = "registered"
    reporting_state: str = "contract_registered"
    live_adapter_state: str = "pending"
    can_override_control_plane: bool = False
    can_self_approve: bool = False
    last_reported_at: Optional[str] = None
    last_report: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ControlPlane:
    """Registry, reporting bus, and authority gate for all ARK95X agents."""

    def __init__(
        self,
        control_plane_id: str = CONTROL_PLANE_ID,
        authoritative_state_path: str = AUTHORITATIVE_STATE_PATH,
    ) -> None:
        self.control_plane_id = control_plane_id
        self.authoritative_state_path = authoritative_state_path
        self._agents: Dict[str, AgentRecord] = {}
        self._action_queue: list[Dict[str, Any]] = []

    @property
    def agents(self) -> Dict[str, AgentRecord]:
        return dict(self._agents)

    @property
    def action_queue(self) -> tuple[Dict[str, Any], ...]:
        return tuple(self._action_queue)

    def register_agent(self, record: AgentRecord) -> AgentRecord:
        """Register a subordinate specialist under the shared control plane."""
        if record.can_override_control_plane:
            raise ValueError("Agents cannot override the control plane")
        if record.can_self_approve:
            raise ValueError("Agents cannot self-approve consequential actions")
        if record.agent_id in self._agents:
            raise ValueError(f"Agent already registered: {record.agent_id}")
        self._agents[record.agent_id] = record
        return record

    def report(
        self,
        agent_id: str,
        status: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        live: bool = True,
    ) -> Dict[str, Any]:
        """Accept one agent report and update its heartbeat state."""
        agent = self._require_agent(agent_id)
        reported_at = datetime.now(timezone.utc).isoformat()
        agent.state = status
        agent.reporting_state = "reported"
        if live:
            agent.live_adapter_state = "reporting"
        agent.last_reported_at = reported_at
        agent.last_report = dict(payload or {})
        return {
            "control_plane_id": self.control_plane_id,
            "agent_id": agent_id,
            "accepted": True,
            "reported_at": reported_at,
        }

    def request_action(
        self,
        agent_id: str,
        action: str,
        action_class: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Queue an action; never grant a specialist direct global authority."""
        agent = self._require_agent(agent_id)
        if action_class not in agent.authority_scope:
            disposition = "rejected_out_of_scope"
        elif action_class in APPROVAL_REQUIRED_ACTION_CLASSES:
            disposition = "queued_for_human_approval"
        else:
            disposition = "queued_for_control_plane"

        request = {
            "request_id": f"{agent_id}:{len(self._action_queue) + 1}",
            "agent_id": agent_id,
            "action": action,
            "action_class": action_class,
            "payload": dict(payload or {}),
            "disposition": disposition,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "executed": False,
        }
        self._action_queue.append(request)
        return dict(request)

    def snapshot(self) -> Dict[str, Any]:
        """Return the control-plane view without replacing ARK-STATE.json."""
        return {
            "control_plane_id": self.control_plane_id,
            "authoritative_state_path": self.authoritative_state_path,
            "agent_count": len(self._agents),
            "agents": {
                agent_id: record.to_dict()
                for agent_id, record in sorted(self._agents.items())
            },
            "queued_actions": list(self._action_queue),
        }

    def _require_agent(self, agent_id: str) -> AgentRecord:
        try:
            return self._agents[agent_id]
        except KeyError as exc:
            raise KeyError(f"Unknown agent: {agent_id}") from exc


DEFAULT_AGENT_SPECS: tuple[AgentRecord, ...] = (
    AgentRecord(
        agent_id="arc_x",
        role="apex coordinator and intent router",
        capabilities=("decode_intent", "rank_options", "route_agents", "simulate"),
        authority_scope=("analysis", "planning", "routing"),
    ),
    AgentRecord(
        agent_id="codex_security",
        role="defensive governor and security reviewer",
        capabilities=("inspect", "threat_model", "veto", "contain", "verify"),
        authority_scope=("analysis", "security_sensitive", "system_mutation"),
    ),
    AgentRecord(
        agent_id="memory_cortex",
        role="verified memory activation and retirement",
        capabilities=("retrieve", "link", "propose_memory_patch", "retire_stale"),
        authority_scope=("analysis", "memory_update"),
    ),
    AgentRecord(
        agent_id="monitoring",
        role="pulse, health, anomaly, and evidence observer",
        capabilities=("observe", "measure", "alert", "attach_evidence"),
        authority_scope=("analysis", "alerting"),
    ),
    AgentRecord(
        agent_id="github",
        role="source control and proof lane",
        capabilities=("read_repo", "create_patch", "record_proof", "manage_pr"),
        authority_scope=("analysis", "repository_write", "deployment", "public"),
    ),
    AgentRecord(
        agent_id="n8n",
        role="workflow transport and scheduled operations bus",
        capabilities=("move_data", "normalize", "schedule", "dispatch"),
        authority_scope=("analysis", "workflow_write", "account_change", "public"),
    ),
    AgentRecord(
        agent_id="devices",
        role="approved local and network execution lane",
        capabilities=("inventory", "heartbeat", "run_scoped_task", "report_result"),
        authority_scope=("analysis", "device_task", "system_mutation", "destructive"),
    ),
    AgentRecord(
        agent_id="business_ops",
        role="wealth, legal, real-estate, and operating decision lane",
        capabilities=("score", "forecast", "prepare_packet", "recommend_action"),
        authority_scope=("analysis", "planning", "financial", "legal", "public"),
    ),
)


def build_default_control_plane(
    specs: Iterable[AgentRecord] = DEFAULT_AGENT_SPECS,
) -> ControlPlane:
    """Build the eight-agent plane from the existing ARK95X roles."""
    plane = ControlPlane()
    for spec in specs:
        # Copy mutable fields so repeated builds remain isolated.
        plane.register_agent(
            AgentRecord(
                agent_id=spec.agent_id,
                role=spec.role,
                capabilities=tuple(spec.capabilities),
                authority_scope=tuple(spec.authority_scope),
            )
        )
    return plane
