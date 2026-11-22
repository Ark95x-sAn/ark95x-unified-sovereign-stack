"""Named-agent routing table for the Beekeeper ledger.

Agents read and write tasks through hive.db. This table only maps
logical agent names to short descriptions — no network I/O.
"""

from __future__ import annotations

from typing import Mapping

# Canonical agent names used in tasks.assigned_agent
KNOWN_AGENTS: Mapping[str, str] = {
    "Muse": "Design / creative agent",
    "Grokbot": "X / research agent",
    "Cursor": "Code / build agent",
    "Jarvis": "Orchestrator / command center",
    "Crew": "Multi-agent crew runner",
    "Operator": "Human operator terminal",
}


def is_known_agent(name: str) -> bool:
    """Return True if name is in the routing table (case-sensitive)."""
    return name in KNOWN_AGENTS


def list_agents() -> list[str]:
    """Return sorted agent names from the routing table."""
    return sorted(KNOWN_AGENTS.keys())


def route_to(agent: str) -> str:
    """
    Validate and return the canonical agent name for assignment.

    Raises ValueError if the agent is not in the routing table.
    """
    if not is_known_agent(agent):
        known = ", ".join(list_agents())
        raise ValueError(f"Unknown agent {agent!r}. Known: {known}")
    return agent
