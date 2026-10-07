"""
ARK95X Protocol Router - Local handlers and protocol route descriptions
MCP actions may invoke registered local handlers. MCP transport, A2A transport,
and ACP transport are not implemented here; agent cards are discovery metadata.
Part of ARK95X Command Center | Network-95 LLC
"""
import asyncio
import copy
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("ark95x.protocol_router")


def _require_string_object_keys(value):
    """Reject keys that JSON encoding would silently coerce or collapse."""
    pending = [value]
    visited = set()
    while pending:
        current = pending.pop()
        if not isinstance(current, (dict, list, tuple)) or id(current) in visited:
            continue
        visited.add(id(current))
        if isinstance(current, dict):
            if any(not isinstance(key, str) for key in current):
                raise ValueError("Local MCP handler JSON object keys must be strings")
            pending.extend(current.values())
        else:
            pending.extend(current)


class ProtocolType(Enum):
    MCP = "mcp"
    A2A = "a2a"
    ACP = "acp"


class MessagePriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class ProtocolMessage:
    protocol: ProtocolType
    sender: str
    recipient: str
    action: str
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    ttl_seconds: int = 300


@dataclass
class AgentCard:
    """A2A Agent Card - describes agent capabilities."""
    agent_id: str
    name: str
    description: str
    skills: List[str]
    protocols: List[str]
    endpoint: str
    version: str = "1.0.0"


class ProtocolRouter:
    """Report local handler outcomes without claiming transport delivery.

    ``messages_routed`` retains its existing name and counts attempts, including
    unavailable routes. A returned handler value is local output, not a receipt
    authenticating a recipient, remote execution, or completion of its action.
    """

    def __init__(self):
        self.routes: Dict[str, Dict] = {}
        self.agent_cards: Dict[str, AgentCard] = {}
        self.message_log: List[Dict] = []
        self.metrics = {
            "messages_routed": 0, "errors": 0, "cancelled": 0,
            "local_handler_returns": 0,
            "by_protocol": {"mcp": 0, "a2a": 0, "acp": 0},
        }
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = {}
        logger.info("ProtocolRouter initialized")

    def register_agent(self, card: AgentCard):
        self.agent_cards[card.agent_id] = card
        for skill in card.skills:
            if skill not in self.routes:
                self.routes[skill] = []
            self.routes[skill].append(card.agent_id)
        logger.info(f"Registered agent: {card.agent_id} with {len(card.skills)} skills")

    def register_handler(self, action: str, handler: Callable):
        """Register an async local callable; registration grants no transport."""
        self._handlers[action] = handler

    async def route(self, message: ProtocolMessage) -> Dict[str, Any]:
        protocol = message.protocol.value if isinstance(message.protocol, ProtocolType) else str(message.protocol)
        context = {
            "protocol": protocol,
            "sender": message.sender,
            "recipient": message.recipient,
            "action": message.action,
            "correlation_id": message.correlation_id,
        }
        logger.info("Routing %s: %s -> %s [%s] correlation=%s", protocol,
                    message.sender, message.recipient, message.action, message.correlation_id)
        self.metrics["messages_routed"] += 1
        if isinstance(message.protocol, ProtocolType):
            self.metrics["by_protocol"][protocol] += 1
        entry = {
            **context,
            "timestamp": message.timestamp,
            "status": "routing",
        }
        self.message_log.append(entry)
        try:
            if message.protocol == ProtocolType.MCP:
                result = await self._route_mcp(message)
            elif message.protocol == ProtocolType.A2A:
                result = await self._route_a2a(message)
            elif message.protocol == ProtocolType.ACP:
                result = await self._route_acp(message)
            else:
                raise ValueError(f"Unknown protocol: {message.protocol}")
        except asyncio.CancelledError:
            self._record_outcome(context, entry, {
                "status": "cancelled",
                "error": "Routing was cancelled; any local handler effects remain unverified",
            })
            raise
        except Exception as e:
            logger.error("Routing error for %s correlation=%s: %s", context["recipient"],
                         context["correlation_id"], e)
            result = {"status": "error", "error": str(e), "error_type": type(e).__name__}
        return self._record_outcome(context, entry, result)

    def _record_outcome(self, context: Dict, entry: Dict, result: Dict) -> Dict[str, Any]:
        outcome = {
            "evidence_scope": "none",
            **result,
            **context,
            "delivered": False,
            "transport_verified": False,
        }
        if outcome["status"] == "local_handler_returned":
            self.metrics["local_handler_returns"] += 1
        elif outcome["status"] == "cancelled":
            self.metrics["cancelled"] += 1
        else:
            self.metrics["errors"] += 1
        entry.update(copy.deepcopy(outcome))
        entry["finished_at"] = datetime.now(timezone.utc).isoformat()
        return outcome

    async def broadcast(self, message: ProtocolMessage) -> List[Dict]:
        """Route once per registered agent, preserving the originating context.

        Results describe attempts. This method supplies no network broadcast.
        """
        template = copy.deepcopy(message)
        results = []
        for agent_id in list(self.agent_cards):
            msg = ProtocolMessage(
                protocol=template.protocol,
                sender=template.sender,
                recipient=agent_id,
                action=template.action,
                payload=copy.deepcopy(template.payload),
                priority=template.priority,
                correlation_id=template.correlation_id,
                timestamp=template.timestamp,
                ttl_seconds=template.ttl_seconds,
            )
            r = await self.route(msg)
            results.append(r)
        return results

    async def _route_mcp(self, message):
        handler = self._handlers.get(message.action)
        if handler is None:
            return {
                "status": "not_implemented",
                "error": "No local MCP handler is registered and MCP transport is not implemented",
            }
        if not isinstance(message.payload, dict):
            raise ValueError("Local MCP handler payload must be an object")
        output = await handler(copy.deepcopy(message.payload))
        if not isinstance(output, dict):
            raise ValueError("Local MCP handler must return a JSON object")
        # Freeze JSON output so later handler mutations cannot rewrite the log.
        _require_string_object_keys(output)
        output = json.loads(json.dumps(output, allow_nan=False))
        if "status" in output and not isinstance(output["status"], str):
            raise ValueError("Local MCP handler status must be a string when present")
        for indicator in ("success", "isError"):
            if indicator in output and type(output[indicator]) is not bool:
                raise ValueError(f"Local MCP handler {indicator} must be a boolean when present")
        failed_statuses = {
            "error", "failed", "failure", "fail", "blocked", "denied", "rejected",
            "cancelled", "canceled", "timeout", "timed_out", "unknown", "partial",
            "not_implemented", "agent_not_found", "unsupported", "unavailable",
        }
        failed = (
            output.get("status", "").strip().lower() in failed_statuses
            or output.get("success") is False
            or output.get("isError") is True
            or output.get("error") not in (None, "", False)
        )
        result = {
            "status": "error" if failed else "local_handler_returned",
            "evidence_scope": "local_handler",
            "handler_result": output,
        }
        if failed:
            result["error"] = "Local MCP handler reported an unsuccessful outcome"
        return result

    async def _route_a2a(self, message):
        card = self.agent_cards.get(message.recipient)
        if not card:
            return {"status": "agent_not_found", "error": "No agent card matches the recipient"}
        return {
            "status": "not_implemented", "agent": card.name, "endpoint": card.endpoint,
            "error": "Agent card found; A2A transport is not implemented",
        }

    async def _route_acp(self, message):
        return {
            "status": "not_implemented", "channel": message.action,
            "error": "ACP transport is not implemented",
        }

    def discover_agents(self, skill: str = None) -> List[Dict]:
        if skill:
            agent_ids = self.routes.get(skill, [])
            return [self.agent_cards[aid].__dict__ for aid in agent_ids if aid in self.agent_cards]
        return [card.__dict__ for card in self.agent_cards.values()]

    def status(self):
        return {
            "router": "ARK95X Protocol Router",
            "registered_agents": len(self.agent_cards),
            "registered_skills": len(self.routes),
            "metrics": self.metrics,
            "protocols": [p.value for p in ProtocolType],
            "message_log_size": len(self.message_log),
        }


def create_default_router():
    router = ProtocolRouter()
    router.register_agent(AgentCard(
        agent_id="manus", name="Manus Agent",
        description="Autonomous execution & build agent",
        skills=["code_generation", "repo_management", "docker_deploy", "api_integration", "database_ops", "system_audit", "workflow_build", "file_operations", "test_suite", "documentation"],
        protocols=["mcp", "a2a", "acp"], endpoint="http://localhost:8000/agents/manus",
    ))
    router.register_agent(AgentCard(
        agent_id="zencode", name="ZenCode Agent",
        description="Deep architecture & code quality engine",
        skills=["architecture_design", "code_review", "pattern_analysis", "dependency_audit", "api_design", "schema_generation", "refactor_engine", "performance_profile", "security_scan", "test_generation", "documentation_gen", "complexity_analysis"],
        protocols=["mcp", "a2a", "acp"], endpoint="http://localhost:8000/agents/zencode",
    ))
    router.register_agent(AgentCard(
        agent_id="vibecoder", name="VibeCoder Agent",
        description="Creative intelligence & rapid prototyping engine",
        skills=["nl_to_code", "ui_generation", "rapid_prototype", "api_scaffold", "dashboard_builder", "workflow_designer", "creative_solve", "code_remix", "prompt_engineering", "data_visualization", "template_factory", "integration_weaver"],
        protocols=["mcp", "a2a", "acp"], endpoint="http://localhost:8000/agents/vibecoder",
    ))
    return router
