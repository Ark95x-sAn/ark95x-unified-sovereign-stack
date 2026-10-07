# dispatcher.py — ARK95X Task Dispatcher
# Routes tasks to agents based on type, priority, and fury state
# Integrates with unified_crew.py and protocol_router.py

from __future__ import annotations
import uuid
import time
from copy import deepcopy
from typing import Optional, List, Dict, Callable, Any
from dataclasses import asdict, dataclass, field
from enum import Enum

if __package__:
    from .unified_crew import UnifiedCrew, CrewTask, AgentRole, get_crew
else:
    from unified_crew import UnifiedCrew, CrewTask, AgentRole, get_crew

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
        req = deepcopy(req)
        agent_role = TASK_ROUTING.get(req.category.lower())
        task = CrewTask(
            task_id=req.task_id,
            description=req.description,
            assigned_to=agent_role,
            priority=req.priority,
            fury=req.fury_override or self.crew.conductor.fury_mode,
            metadata=deepcopy(req.metadata),
        )
        if agent_role is None:
            result = f"[BLOCKED] Unknown task category: {req.category!r}"
            self.crew.conductor._store_result(
                task, result, status="blocked", executed=False
            )
        else:
            result = self.crew.conductor.dispatch(task)
        entry = self._record(req, task, result)
        for index, hook in enumerate(tuple(self._hooks)):
            try:
                hook(deepcopy(task), result)
            except Exception as exc:
                # A callback failure does not undo or retry an attempted task.
                entry["hook_errors"].append({
                    "hook_index": index, "error_type": type(exc).__name__,
                    "error": str(exc),
                })
        return result

    def batch_route(self, requests: List[DispatchRequest]) -> List[str]:
        # Preserve the existing stable priority order and the single-task audit path.
        # This prototype is sequential; batch size does not establish concurrency.
        return [self.route(req) for req in sorted(
            requests, key=lambda req: req.priority, reverse=True
        )]

    def _record(self, req: DispatchRequest, task: CrewTask, result: str):
        entry = {
            "ts":       time.time(),
            "task_id":  req.task_id,
            "category": req.category,
            "agent":    task.assigned_to.value if task.assigned_to else None,
            "priority": req.priority,
            "status":   task.status,
            "executed": task.executed,
            "verified": task.verified,
            "result":   result,
            "input":    asdict(req),
            "hook_errors": [],
        }
        self.history.append(entry)
        return entry

    def summary(self) -> dict:
        by_agent: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for h in self.history:
            agent = h["agent"] or "unassigned"
            by_agent[agent] = by_agent.get(agent, 0) + 1
            by_status[h["status"]] = by_status.get(h["status"], 0) + 1
        return {
            "total_dispatched": len(self.history),
            "by_agent":         by_agent,
            "by_status":        by_status,
            "verified_tasks":   sum(h["verified"] is True for h in self.history),
            "hook_errors":      sum(len(h["hook_errors"]) for h in self.history),
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
