# dispatcher.py — ARK95X Task Dispatcher
# Routes tasks to agents based on type, priority, and fury state
# Integrates with unified_crew.py and protocol_router.py

from __future__ import annotations
import uuid
import time
from typing import Optional, List, Dict, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

from unified_crew import (
    UnifiedCrew, CrewTask, AgentRole, get_crew
)

# ── Task categories map to agents
TASK_ROUTING: Dict[str, AgentRole] = {
    # Manus — Research & Intel
    "research":    AgentRole.MANUS,
    "litigation":  AgentRole.MANUS,
    "property":    AgentRole.MANUS,
    "financial":   AgentRole.MANUS,
    "data":        AgentRole.MANUS,
    "extract":     AgentRole.MANUS,
    "analyze":     AgentRole.MANUS,
    # ZenCode — Architecture & Code
    "code":        AgentRole.ZENCODE,
    "build":       AgentRole.ZENCODE,
    "api":         AgentRole.ZENCODE,
    "deploy":      AgentRole.ZENCODE,
    "schema":      AgentRole.ZENCODE,
    "database":    AgentRole.ZENCODE,
    "backend":     AgentRole.ZENCODE,
    "refactor":    AgentRole.ZENCODE,
    "test":        AgentRole.ZENCODE,
    # VibeCoder — UI/UX & Creative
    "ui":          AgentRole.VIBECODER,
    "ux":          AgentRole.VIBECODER,
    "dashboard":   AgentRole.VIBECODER,
    "design":      AgentRole.VIBECODER,
    "frontend":    AgentRole.VIBECODER,
    "visual":      AgentRole.VIBECODER,
    "creative":    AgentRole.VIBECODER,
}

@dataclass
class DispatchRequest:
    description:  str
    category:     str
    priority:     int = 5
    fury_override: bool = False
    task_id:      str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    metadata:     dict = field(default_factory=dict)

# ── Dispatcher
class Dispatcher:
    def __init__(self, crew: Optional[UnifiedCrew] = None, fury: bool = True):
        self.crew    = crew or get_crew(fury=fury)
        self.history: List[dict] = []
        self._hooks: List[Callable[[CrewTask, str], None]] = []

    def add_hook(self, fn: Callable[[CrewTask, str], None]):
        """Register a post-dispatch callback."""
        self._hooks.append(fn)

    def route(self, req: DispatchRequest) -> str:
        agent_role = TASK_ROUTING.get(req.category.lower(), AgentRole.MANUS)
        task = CrewTask(
            task_id=req.task_id,
            description=req.description,
            assigned_to=agent_role,
            priority=req.priority,
            fury=req.fury_override or self.crew.conductor.fury_mode,
            metadata=req.metadata,
        )
        result = self.crew.conductor.dispatch(task)
        self._record(req, task, result)
        for hook in self._hooks:
            hook(task, result)
        return result

    def batch_route(self, requests: List[DispatchRequest]) -> List[str]:
        tasks = []
        for req in requests:
            agent_role = TASK_ROUTING.get(req.category.lower(), AgentRole.MANUS)
            tasks.append(CrewTask(
                task_id=req.task_id,
                description=req.description,
                assigned_to=agent_role,
                priority=req.priority,
                fury=req.fury_override or self.crew.conductor.fury_mode,
                metadata=req.metadata,
            ))
        # Sort by priority descending
        tasks.sort(key=lambda t: t.priority, reverse=True)
        return self.crew.conductor.multiplex_run(tasks)

    def _record(self, req: DispatchRequest, task: CrewTask, result: str):
        self.history.append({
            "ts":       time.time(),
            "task_id":  req.task_id,
            "category": req.category,
            "agent":    task.assigned_to.value,
            "priority": req.priority,
            "status":   task.status,
            "result":   result[:80],
        })

    def summary(self) -> dict:
        by_agent: Dict[str, int] = {}
        for h in self.history:
            by_agent[h["agent"]] = by_agent.get(h["agent"], 0) + 1
        return {
            "total_dispatched": len(self.history),
            "by_agent":         by_agent,
            "fury":             self.crew.conductor.fury_mode,
            "memory_keys":      len(self.crew.memory.context_snapshot()),
        }

# ── Convenience builders
def quick_dispatch(description: str, category: str = "research",
                   priority: int = 5) -> str:
    dispatcher = Dispatcher()
    req = DispatchRequest(description=description,
                          category=category,
                          priority=priority)
    return dispatcher.route(req)

# ── Singleton dispatcher
_dispatcher: Optional[Dispatcher] = None

def get_dispatcher(fury: bool = True) -> Dispatcher:
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = Dispatcher(fury=fury)
    return _dispatcher

if __name__ == "__main__":
    d = get_dispatcher(fury=True)
    reqs = [
        DispatchRequest("Analyze bank litigation docs",  "litigation", priority=9),
        DispatchRequest("Build case timeline API",        "api",        priority=8),
        DispatchRequest("Design litigation dashboard",    "dashboard",  priority=8),
        DispatchRequest("Extract property value data",    "property",   priority=7),
        DispatchRequest("Refactor command center routes", "refactor",   priority=7),
        DispatchRequest("Build real-time agent status UI","ui",         priority=6),
    ]
    results = d.batch_route(reqs)
    print("\n[ARK95X DISPATCHER] Summary:")
    import json
    print(json.dumps(d.summary(), indent=2))
