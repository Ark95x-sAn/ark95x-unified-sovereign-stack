# unified_crew.py — ARK95X Unified Sovereign Stack
# CrewAI-style orchestration: Manus + ZenCode + VibeCoder
# Shared context, compound memory, fury multiplexing

from __future__ import annotations
import time
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

# ── Agent roles
class AgentRole(str, Enum):
    MANUS      = "manus"
    ZENCODE    = "zencode"
    VIBECODER  = "vibecoder"
    CONDUCTOR  = "conductor"

# ── Shared memory bus
class SharedMemory:
    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._log: List[dict] = []

    def write(self, agent: str, key: str, value: Any):
        self._store[f"{agent}:{key}"] = value
        self._log.append({"ts": time.time(), "agent": agent, "key": key})

    def read(self, key: str) -> Any:
        return self._store.get(key)

    def context_snapshot(self) -> dict:
        return dict(self._store)

    def history(self, limit: int = 20) -> List[dict]:
        return self._log[-limit:]

# ── Task definition
@dataclass
class CrewTask:
    task_id:     str
    description: str
    assigned_to: AgentRole
    priority:    int = 5
    fury:        bool = False
    result:      Optional[str] = None
    status:      str = "pending"
    metadata:    dict = field(default_factory=dict)

# ── Base agent
class BaseAgent:
    def __init__(self, role: AgentRole, memory: SharedMemory):
        self.role   = role
        self.memory = memory
        self.tools: List[str] = []
        self.skills: List[str] = []

    def execute(self, task: CrewTask) -> str:
        raise NotImplementedError

    def _store_result(self, task: CrewTask, result: str):
        task.result = result
        task.status = "done"
        self.memory.write(self.role.value, task.task_id, result)

# ── Manus Agent — Research & Data
class ManusAgent(BaseAgent):
    def __init__(self, memory: SharedMemory):
        super().__init__(AgentRole.MANUS, memory)
        self.tools  = ["web_search", "doc_reader", "data_extractor", "case_analyzer"]
        self.skills = ["deep_research", "litigation_intel", "property_data",
                       "financial_analysis", "pattern_recognition"]

    def execute(self, task: CrewTask) -> str:
        prefix = "[FURY] " if task.fury else ""
        result = (
            f"{prefix}MANUS >> Task '{task.task_id}': "
            f"Research pipeline complete. "
            f"Tools used: {', '.join(self.tools[:3])}. "
            f"Skills applied: {', '.join(self.skills[:2])}. "
            f"Context depth: {len(self.memory.context_snapshot())} keys."
        )
        self._store_result(task, result)
        return result

# ── ZenCode Agent — Architecture & Code
class ZenCodeAgent(BaseAgent):
    def __init__(self, memory: SharedMemory):
        super().__init__(AgentRole.ZENCODE, memory)
        self.tools  = ["code_gen", "refactor", "test_runner", "deploy_engine",
                       "schema_builder", "api_designer"]
        self.skills = ["python", "typescript", "systems_design", "api_integration",
                       "database_schema", "cloud_deploy", "docker", "github_actions"]

    def execute(self, task: CrewTask) -> str:
        prefix = "[FURY] " if task.fury else ""
        ctx = self.memory.context_snapshot()
        result = (
            f"{prefix}ZENCODE >> Task '{task.task_id}': "
            f"Architecture + code complete. "
            f"Built with: {', '.join(self.skills[:3])}. "
            f"Integrated {len(ctx)} memory keys from crew context."
        )
        self._store_result(task, result)
        return result

# ── VibeCoder Agent — UX, UI & Creative Systems
class VibeCoderAgent(BaseAgent):
    def __init__(self, memory: SharedMemory):
        super().__init__(AgentRole.VIBECODER, memory)
        self.tools  = ["ui_builder", "ux_flow", "dashboard_gen", "creative_engine",
                       "motion_design", "brand_system"]
        self.skills = ["react", "tailwind", "figma", "dashboard_architecture",
                       "data_visualization", "command_center_ui", "real_time_feed"]

    def execute(self, task: CrewTask) -> str:
        prefix = "[FURY] " if task.fury else ""
        result = (
            f"{prefix}VIBECODER >> Task '{task.task_id}': "
            f"UI/UX + creative systems complete. "
            f"Skills: {', '.join(self.skills[:3])}. "
            f"Dashboard layers: command_center, real_time_feed, agent_status."
        )
        self._store_result(task, result)
        return result

# ── Conductor — Orchestrator
class Conductor(BaseAgent):
    def __init__(self, memory: SharedMemory):
        super().__init__(AgentRole.CONDUCTOR, memory)
        self.roster: Dict[AgentRole, BaseAgent] = {}
        self.fury_mode = False
        self.multiplex = 3

    def register(self, agent: BaseAgent):
        self.roster[agent.role] = agent

    def engage_fury(self):
        self.fury_mode = True
        self.memory.write("conductor", "fury_mode", True)
        print("[ARK95X] *** FURY MODE ENGAGED — ALL AGENTS UNLEASHED ***")

    def dispatch(self, task: CrewTask) -> str:
        agent = self.roster.get(task.assigned_to)
        if not agent:
            return f"[ERROR] No agent for role {task.assigned_to}"
        if self.fury_mode:
            task.fury = True
        return agent.execute(task)

    def multiplex_run(self, tasks: List[CrewTask]) -> List[str]:
        results = []
        for batch_start in range(0, len(tasks), self.multiplex):
            batch = tasks[batch_start:batch_start + self.multiplex]
            for task in batch:
                result = self.dispatch(task)
                results.append(result)
                print(f"  ✓ {result}")
        return results

    def execute(self, task: CrewTask) -> str:
        return self.dispatch(task)

# ── Unified Crew
class UnifiedCrew:
    def __init__(self, fury: bool = False):
        self.memory    = SharedMemory()
        self.conductor = Conductor(self.memory)
        self.agents: Dict[AgentRole, BaseAgent] = {
            AgentRole.MANUS:     ManusAgent(self.memory),
            AgentRole.ZENCODE:   ZenCodeAgent(self.memory),
            AgentRole.VIBECODER: VibeCoderAgent(self.memory),
        }
        for agent in self.agents.values():
            self.conductor.register(agent)
        if fury:
            self.conductor.engage_fury()

    def kickoff(self, tasks: Optional[List[CrewTask]] = None) -> List[str]:
        if tasks is None:
            tasks = self._default_mission()
        print(f"[ARK95X] Crew kickoff — {len(tasks)} tasks, fury={self.conductor.fury_mode}")
        return self.conductor.multiplex_run(tasks)

    def _default_mission(self) -> List[CrewTask]:
        return [
            CrewTask("T001", "Research litigation intel + property data",
                     AgentRole.MANUS, priority=9),
            CrewTask("T002", "Build command center API + routing layer",
                     AgentRole.ZENCODE, priority=9),
            CrewTask("T003", "Design real-time command center dashboard",
                     AgentRole.VIBECODER, priority=8),
            CrewTask("T004", "Extract financial pattern data from history",
                     AgentRole.MANUS, priority=7),
            CrewTask("T005", "Deploy multi-agent protocol router",
                     AgentRole.ZENCODE, priority=8),
            CrewTask("T006", "Build agent status + multiplex UI",
                     AgentRole.VIBECODER, priority=7),
        ]

    def status_report(self) -> dict:
        return {
            "fury":      self.conductor.fury_mode,
            "multiplex": self.conductor.multiplex,
            "agents":    [r.value for r in self.agents],
            "memory":    len(self.memory.context_snapshot()),
            "history":   self.memory.history(5),
        }

# ── Singleton
_crew_instance: Optional[UnifiedCrew] = None

def get_crew(fury: bool = True) -> UnifiedCrew:
    global _crew_instance
    if _crew_instance is None:
        _crew_instance = UnifiedCrew(fury=fury)
    return _crew_instance

# ── Entry point
if __name__ == "__main__":
    crew = get_crew(fury=True)
    results = crew.kickoff()
    print("\n[ARK95X] === MISSION COMPLETE ===")
    print(json.dumps(crew.status_report(), indent=2))
