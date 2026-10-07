"""
ARK95X MANUS AGENT - Autonomous Execution & Build Agent
The hands of the system. Executes complex multi-step builds,
deployments, and system modifications with full autonomy.
Part of ARK95X Command Center | Network-95 LLC
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from . import _blocked, _invoke_handler, _not_implemented

logger = logging.getLogger("ark95x.manus")


class ManusMode(Enum):
    STEALTH = "stealth"
    FURY = "fury"
    PRECISION = "precision"
    AUTONOMOUS = "autonomous"
    SWARM = "swarm"


class TaskPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class ManusSkill:
    name: str
    category: str
    description: str
    handler: str
    requires: list = field(default_factory=list)
    cooldown_seconds: int = 0
    max_concurrent: int = 5


@dataclass
class ManusTask:
    task_id: str
    action: str
    target: str
    params: dict
    priority: TaskPriority = TaskPriority.MEDIUM
    status: str = "queued"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    result: dict = None
    error: str = None
    retries: int = 0
    max_retries: int = 3


class ManusAgent:
    SKILLS = {
        "code_generation": ManusSkill("code_generation", "build", "Generate production code from specs", "_skill_code_gen", ["spec", "language"]),
        "repo_management": ManusSkill("repo_management", "devops", "Git operations, branch mgmt, PR creation", "_skill_repo_mgmt", ["repo_url"]),
        "docker_deploy": ManusSkill("docker_deploy", "infra", "Build and deploy Docker containers", "_skill_docker_deploy", ["service_name"]),
        "api_integration": ManusSkill("api_integration", "integration", "Connect and wire external APIs", "_skill_api_integrate", ["api_spec"]),
        "database_ops": ManusSkill("database_ops", "data", "Schema migration, backup/restore", "_skill_db_ops", ["db_target"]),
        "system_audit": ManusSkill("system_audit", "security", "Full system security and health audit", "_skill_audit"),
        "workflow_build": ManusSkill("workflow_build", "automation", "Build n8n/automation workflows", "_skill_workflow_build", ["workflow_spec"]),
        "file_operations": ManusSkill("file_operations", "system", "Create, modify, organize files", "_skill_file_ops", ["path", "operation"]),
        "test_suite": ManusSkill("test_suite", "quality", "Generate and run test suites", "_skill_test_suite", ["target_module"]),
        "documentation": ManusSkill("documentation", "docs", "Generate docs, READMEs, API specs", "_skill_docs", ["scope"]),
    }

    PROTOCOLS = {
        "mcp": {"name": "Model Context Protocol", "version": "1.0", "transport": "stdio/sse"},
        "a2a": {"name": "Agent-to-Agent", "version": "1.0", "transport": "http/json-rpc"},
        "acp": {"name": "Agent Communication Protocol", "version": "0.2", "transport": "rest/mime"},
    }

    def __init__(self, mode=ManusMode.AUTONOMOUS):
        self.mode = mode
        self.agent_id = f"manus-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.task_queue = []
        self.completed = []
        self.active_tasks = {}
        self.metrics = {"tasks_completed": 0, "tasks_failed": 0, "tasks_reported": 0,
                        "tasks_blocked": 0, "uptime_start": datetime.utcnow().isoformat()}
        logger.info(f"ManusAgent initialized | mode={mode.value} | id={self.agent_id}")

    async def execute(self, task):
        if not isinstance(task, ManusTask):
            return _blocked("Expected a ManusTask.")
        task_id = task.task_id
        for key in ("task_id", "action", "target"):
            value = getattr(task, key)
            if not isinstance(value, str) or not value.strip():
                task.status = "blocked"
                task.error = f"{key} must be a nonempty string."
                return {**_blocked(task.error), "task_id": task_id}
        if not isinstance(task.params, dict):
            task.status = "blocked"
            task.error = "Task params must be a dictionary."
            return {**_blocked(task.error), "task_id": task_id}
        skill = self.SKILLS.get(task.action)
        if not skill:
            task.status = "blocked"
            task.error = f"Unknown skill: {task.action}"
            self.metrics["tasks_blocked"] += 1
            return {**_blocked(task.error), "task_id": task_id}
        if task_id in self.active_tasks:
            return {**_blocked("A task with this id is already running."), "task_id": task_id}
        logger.info(f"Dispatching {task_id}: {task.action} on {task.target}")
        task.status = "running"
        task.error = None
        self.active_tasks[task_id] = task
        try:
            handler = getattr(self, skill.handler, self._default_handler)
            outcome = await _invoke_handler(handler, task)
            task.status = outcome["status"]
            task.result = outcome.get("result")
            task.error = outcome.get("error")
            if task.status == "reported":
                self.metrics["tasks_reported"] += 1
            elif task.status == "failed":
                self.metrics["tasks_failed"] += 1
            elif task.status in {"blocked", "not_implemented"}:
                self.metrics["tasks_blocked"] += 1
            # There is no receipt validator here, so reported work is never
            # added to the completed list or the completed counter.
            return {**outcome, "task_id": task_id}
        except asyncio.CancelledError:
            task.status = "cancelled"
            task.error = "CancelledError"
            raise
        finally:
            self.active_tasks.pop(task_id, None)

    async def fury_mode(self, tasks):
        self.mode = ManusMode.FURY
        logger.info(f"FURY MODE ENGAGED | {len(tasks)} tasks")
        return await asyncio.gather(*[self.execute(t) for t in tasks], return_exceptions=True)

    async def multiplex(self, task_groups):
        logger.info(f"MULTIPLEX | {len(task_groups)} pipelines")
        results = {}
        for name, tasks in task_groups.items():
            results[name] = [await self.execute(t) for t in tasks]
        return results

    async def _skill_code_gen(self, task): return _not_implemented(task.action, task.target)
    async def _skill_repo_mgmt(self, task): return _not_implemented(task.action, task.target)
    async def _skill_docker_deploy(self, task): return _not_implemented(task.action, task.target)
    async def _skill_api_integrate(self, task): return _not_implemented(task.action, task.target)
    async def _skill_db_ops(self, task): return _not_implemented(task.action, task.target)
    async def _skill_audit(self, task): return _not_implemented(task.action, task.target)
    async def _skill_workflow_build(self, task): return _not_implemented(task.action, task.target)
    async def _skill_file_ops(self, task): return _not_implemented(task.action, task.target)
    async def _skill_test_suite(self, task): return _not_implemented(task.action, task.target)
    async def _skill_docs(self, task): return _not_implemented(task.action, task.target)
    async def _default_handler(self, task): return _not_implemented(task.action, task.target)

    def status(self):
        return {
            "agent_id": self.agent_id, "mode": self.mode.value,
            "queued": len(self.task_queue), "active": len(self.active_tasks),
            "completed": self.metrics["tasks_completed"], "failed": self.metrics["tasks_failed"],
            "reported": self.metrics["tasks_reported"], "blocked": self.metrics["tasks_blocked"],
            "skills": list(self.SKILLS.keys()), "protocols": list(self.PROTOCOLS.keys()),
        }
