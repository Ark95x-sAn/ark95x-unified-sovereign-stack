"""
ARK95X Protocol Router - Unified MCP/A2A/ACP Protocol System
Routes messages between agents using Model Context Protocol,
Agent-to-Agent Protocol, and Agent Communication Protocol.
Part of ARK95X Command Center | Network-95 LLC
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("ark95x.protocol_router")


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
    """Unified protocol router for MCP, A2A, and ACP."""

    def __init__(self):
        self.routes: Dict[str, Dict] = {}
        self.agent_cards: Dict[str, AgentCard] = {}
        self.message_log: List[Dict] = []
        self.metrics = {"messages_routed": 0, "errors": 0, "by_protocol": {"mcp": 0, "a2a": 0, "acp": 0}}
        self._handlers: Dict[str, callable] = {}
        logger.info("ProtocolRouter initialized")

    def register_agent(self, card: AgentCard):
        self.agent_cards[card.agent_id] = card
        for skill in card.skills:
            if skill not in self.routes:
                self.routes[skill] = []
            self.routes[skill].append(card.agent_id)
        logger.info(f"Registered agent: {card.agent_id} with {len(card.skills)} skills")

    def register_handler(self, action: str, handler: callable):
        self._handlers[action] = handler

    async def route(self, message: ProtocolMessage) -> Dict[str, Any]:
        logger.info(f"Routing {message.protocol.value}: {message.sender} -> {message.recipient} [{message.action}]")
        self.metrics["messages_routed"] += 1
        self.metrics["by_protocol"][message.protocol.value] += 1
        self.message_log.append({
            "protocol": message.protocol.value,
            "sender": message.sender,
            "recipient": message.recipient,
            "action": message.action,
            "timestamp": message.timestamp,
        })
        try:
            if message.protocol == ProtocolType.MCP:
                return await self._route_mcp(message)
            elif message.protocol == ProtocolType.A2A:
                return await self._route_a2a(message)
            elif message.protocol == ProtocolType.ACP:
                return await self._route_acp(message)
            else:
                raise ValueError(f"Unknown protocol: {message.protocol}")
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Routing error: {e}")
            return {"status": "error", "error": str(e)}

    async def broadcast(self, message: ProtocolMessage) -> List[Dict]:
        """Broadcast to all registered agents."""
        results = []
        for agent_id in self.agent_cards:
            msg = ProtocolMessage(
                protocol=message.protocol,
                sender=message.sender,
                recipient=agent_id,
                action=message.action,
                payload=message.payload,
                priority=message.priority,
            )
            r = await self.route(msg)
            results.append(r)
        return results

    async def _route_mcp(self, message):
        handler = self._handlers.get(message.action)
        if handler:
            return await handler(message.payload)
        return {"protocol": "mcp", "status": "delivered", "recipient": message.recipient}

    async def _route_a2a(self, message):
        card = self.agent_cards.get(message.recipient)
        if not card:
            return {"protocol": "a2a", "status": "agent_not_found", "recipient": message.recipient}
        return {"protocol": "a2a", "status": "delivered", "agent": card.name, "endpoint": card.endpoint}

    async def _route_acp(self, message):
        return {"protocol": "acp", "status": "delivered", "recipient": message.recipient, "channel": message.action}

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
