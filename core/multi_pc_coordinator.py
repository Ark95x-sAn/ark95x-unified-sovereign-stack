"""
ARK95X Multi-PC Coordinator
============================
Treats each physical PC as a self-managing autonomous node.
Nodes coordinate through a shared task bus and report health
to a central coordinator that dispatches work based on
capability scores and current load.

Architecture:
    Coordinator (this service, port 8096)
        ├── Node: pc_win11   (gaming PC, GPU, Docker, Ollama)
        ├── Node: pc_gaming  (second gaming PC — same autonomy)
        ├── Node: surface_pro (mobile command)
        └── Node: [any future PC added via register_node()]

Each node:
    - Pulls tasks from its queue
    - Executes autonomously
    - Reports status/output back to coordinator
    - Can spawn sub-tasks to other nodes
    - Runs 24/7 automation loops independently

Sync: Tailscale mesh (primary) → local network → GitHub (fallback)
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

COORDINATOR_PORT = int(os.getenv("COORDINATOR_PORT", "8096"))
TAILSCALE_SUBNET = os.getenv("TAILSCALE_SUBNET", "100.64.0.0/24")
NODE_HEARTBEAT_INTERVAL = int(os.getenv("NODE_HEARTBEAT_INTERVAL", "30"))
TASK_POLL_INTERVAL = int(os.getenv("TASK_POLL_INTERVAL", "5"))

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class NodeStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    STANDBY = "standby"
    BUSY = "busy"
    IDLE = "idle"
    ERROR = "error"


class TaskStatus(str, Enum):
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class CapabilityTag(str, Enum):
    GPU = "gpu"
    DOCKER = "docker"
    OLLAMA = "ollama"
    HIGH_RAM = "high_ram"
    SCRAPING = "scraping"
    TRADING = "trading"
    BUILD = "build"
    DEPLOY = "deploy"
    MONITORING = "monitoring"
    AUTOMATION = "automation"
    LOCAL_LLM = "local_llm"
    DEVELOPMENT = "development"
    ALWAYS_ON = "always_on"


# ---------------------------------------------------------------------------
# Node Registry
# ---------------------------------------------------------------------------


class NodeCapabilities(BaseModel):
    gpu: str | None = None
    ram_gb: int = 8
    cpu_cores: int = 4
    docker: bool = False
    ollama: bool = False
    wsl2: bool = False
    always_on: bool = False
    max_parallel_tasks: int = 3
    tags: list[CapabilityTag] = Field(default_factory=list)
    custom: dict[str, Any] = Field(default_factory=dict)


class NodeRegistration(BaseModel):
    node_id: str
    name: str
    platform: str
    host: str
    port: int = 8097
    capabilities: NodeCapabilities
    tailscale_ip: str | None = None
    local_ip: str | None = None


class NodeHealth(BaseModel):
    node_id: str
    status: NodeStatus
    cpu_pct: float = 0.0
    ram_pct: float = 0.0
    active_tasks: int = 0
    queued_tasks: int = 0
    uptime_seconds: float = 0.0
    last_heartbeat: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    error_message: str | None = None


class CoordinatorNode(BaseModel):
    registration: NodeRegistration
    health: NodeHealth = Field(default_factory=lambda: NodeHealth(
        node_id="", status=NodeStatus.OFFLINE
    ))
    score: float = 0.0

    def reachable_url(self) -> str:
        host = self.registration.tailscale_ip or self.registration.local_ip or self.registration.host
        return f"http://{host}:{self.registration.port}"

    def capability_score(self, required_tags: list[CapabilityTag]) -> float:
        caps = self.registration.capabilities
        score = 0.0
        tag_set = set(caps.tags)
        for tag in required_tags:
            if tag in tag_set:
                score += 20.0
        if caps.gpu:
            score += 15.0
        if caps.ram_gb >= 32:
            score += 10.0
        if caps.docker:
            score += 5.0
        if caps.ollama:
            score += 5.0
        load_penalty = (self.health.cpu_pct / 100) * 30.0
        return max(0.0, score - load_penalty)


# ---------------------------------------------------------------------------
# Task Bus
# ---------------------------------------------------------------------------


class CoordinatorTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    task_type: str = "general"
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    required_capabilities: list[CapabilityTag] = Field(default_factory=list)
    preferred_node: str | None = None
    assigned_node: str | None = None
    status: TaskStatus = TaskStatus.QUEUED
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    started_at: str | None = None
    completed_at: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    parent_task_id: str | None = None
    sub_task_ids: list[str] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 2


class TaskResult(BaseModel):
    task_id: str
    node_id: str
    status: TaskStatus
    result: dict[str, Any] | None = None
    error: str | None = None
    completed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ---------------------------------------------------------------------------
# Coordinator Core
# ---------------------------------------------------------------------------


class MultiPCCoordinator:
    """
    Central coordinator for the multi-PC sovereign mesh.
    Dispatches tasks, monitors node health, and manages failover.
    """

    def __init__(self) -> None:
        self.nodes: dict[str, CoordinatorNode] = {}
        self.task_queue: list[CoordinatorTask] = []
        self.completed_tasks: list[CoordinatorTask] = []
        self.failed_tasks: list[CoordinatorTask] = []
        self._running = False
        self._register_default_nodes()

    def _initial_status(self, caps: NodeCapabilities) -> NodeStatus:
        """Always-on nodes start STANDBY (reachable); others start OFFLINE."""
        return NodeStatus.STANDBY if caps.always_on else NodeStatus.OFFLINE

    def _register_default_nodes(self) -> None:
        """Pre-register known nodes from the device fleet."""
        defaults = [
            NodeRegistration(
                node_id="pc_win11",
                name="Primary Gaming PC (Win11 Pro)",
                platform="windows_11_pro",
                host="pc-win11.local",
                port=8097,
                tailscale_ip=os.getenv("NODE_PC_WIN11_IP"),
                local_ip="192.168.1.100",
                capabilities=NodeCapabilities(
                    gpu="nvidia_rtx",
                    ram_gb=32,
                    cpu_cores=12,
                    docker=True,
                    ollama=True,
                    wsl2=True,
                    always_on=True,
                    max_parallel_tasks=8,
                    tags=[
                        CapabilityTag.GPU,
                        CapabilityTag.DOCKER,
                        CapabilityTag.OLLAMA,
                        CapabilityTag.HIGH_RAM,
                        CapabilityTag.LOCAL_LLM,
                        CapabilityTag.DEVELOPMENT,
                        CapabilityTag.BUILD,
                        CapabilityTag.DEPLOY,
                        CapabilityTag.ALWAYS_ON,
                    ],
                ),
            ),
            NodeRegistration(
                node_id="pc_gaming_2",
                name="Secondary Gaming PC",
                platform="windows_11",
                host="pc-gaming2.local",
                port=8097,
                tailscale_ip=os.getenv("NODE_PC_GAMING2_IP"),
                local_ip="192.168.1.101",
                capabilities=NodeCapabilities(
                    gpu="nvidia_rtx",
                    ram_gb=32,
                    cpu_cores=16,
                    docker=True,
                    ollama=True,
                    wsl2=True,
                    always_on=True,
                    max_parallel_tasks=8,
                    tags=[
                        CapabilityTag.GPU,
                        CapabilityTag.DOCKER,
                        CapabilityTag.OLLAMA,
                        CapabilityTag.HIGH_RAM,
                        CapabilityTag.LOCAL_LLM,
                        CapabilityTag.SCRAPING,
                        CapabilityTag.AUTOMATION,
                        CapabilityTag.TRADING,
                        CapabilityTag.MONITORING,
                        CapabilityTag.ALWAYS_ON,
                    ],
                ),
            ),
            NodeRegistration(
                node_id="surface_pro",
                name="Surface Pro (Mobile Command)",
                platform="windows_11",
                host="surface-pro.local",
                port=8097,
                tailscale_ip=os.getenv("NODE_SURFACE_IP"),
                capabilities=NodeCapabilities(
                    ram_gb=16,
                    cpu_cores=8,
                    always_on=False,
                    max_parallel_tasks=3,
                    tags=[
                        CapabilityTag.MONITORING,
                        CapabilityTag.AUTOMATION,
                    ],
                ),
            ),
        ]
        for reg in defaults:
            initial = self._initial_status(reg.capabilities)
            node = CoordinatorNode(
                registration=reg,
                health=NodeHealth(node_id=reg.node_id, status=initial),
            )
            self.nodes[reg.node_id] = node
            logger.info(f"[COORD] Registered node: {reg.node_id} ({reg.name}) status={initial.value}")

    # ------------------------------------------------------------------
    # Node Management
    # ------------------------------------------------------------------

    def register_node(self, reg: NodeRegistration) -> CoordinatorNode:
        node = CoordinatorNode(
            registration=reg,
            health=NodeHealth(node_id=reg.node_id, status=NodeStatus.ONLINE),
        )
        self.nodes[reg.node_id] = node
        logger.info(f"[COORD] Node registered: {reg.node_id}")
        return node

    def update_health(self, health: NodeHealth) -> None:
        node = self.nodes.get(health.node_id)
        if node:
            node.health = health
            logger.debug(f"[COORD] Health updated: {health.node_id} → {health.status.value}")

    def get_node(self, node_id: str) -> CoordinatorNode:
        node = self.nodes.get(node_id)
        if not node:
            raise KeyError(f"Unknown node: {node_id}")
        return node

    def online_nodes(self) -> list[CoordinatorNode]:
        return [
            n for n in self.nodes.values()
            if n.health.status in (NodeStatus.ONLINE, NodeStatus.IDLE, NodeStatus.STANDBY)
        ]

    def best_node_for_task(self, task: CoordinatorTask) -> CoordinatorNode | None:
        """Select the highest-scoring available node for a task."""
        if task.preferred_node and task.preferred_node in self.nodes:
            node = self.nodes[task.preferred_node]
            if node.health.status not in (NodeStatus.OFFLINE, NodeStatus.ERROR):
                return node

        candidates = [
            n for n in self.online_nodes()
            if n.health.active_tasks < n.registration.capabilities.max_parallel_tasks
        ]
        if not candidates:
            return None

        scored = sorted(
            candidates,
            key=lambda n: n.capability_score(task.required_capabilities),
            reverse=True,
        )
        return scored[0]

    # ------------------------------------------------------------------
    # Task Bus
    # ------------------------------------------------------------------

    def submit_task(self, task: CoordinatorTask) -> CoordinatorTask:
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority.value)
        logger.info(f"[COORD] Task submitted: {task.task_id} '{task.title}' priority={task.priority.name}")
        return task

    def split_task(
        self,
        parent_task: CoordinatorTask,
        subtask_specs: list[dict[str, Any]],
    ) -> list[CoordinatorTask]:
        """Divide a large task across multiple nodes for parallel execution."""
        subtasks: list[CoordinatorTask] = []
        for spec in subtask_specs:
            sub = CoordinatorTask(
                parent_task_id=parent_task.task_id,
                **spec,
            )
            parent_task.sub_task_ids.append(sub.task_id)
            self.submit_task(sub)
            subtasks.append(sub)
        logger.info(
            f"[COORD] Task {parent_task.task_id} split into {len(subtasks)} subtasks"
        )
        return subtasks

    async def dispatch_task(self, task: CoordinatorTask) -> bool:
        """Assign and dispatch one task to the best available node."""
        node = self.best_node_for_task(task)
        if not node:
            logger.warning(f"[COORD] No available node for task {task.task_id}")
            return False

        task.assigned_node = node.registration.node_id
        task.status = TaskStatus.ASSIGNED
        task.started_at = datetime.now(timezone.utc).isoformat()

        payload = {
            "task_id": task.task_id,
            "title": task.title,
            "task_type": task.task_type,
            "payload": task.payload,
            "priority": task.priority.value,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{node.reachable_url()}/task/execute"
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    task.status = TaskStatus.RUNNING
                    node.health.active_tasks += 1
                    logger.info(
                        f"[COORD] Task {task.task_id} dispatched → {node.registration.node_id}"
                    )
                    return True
                else:
                    task.status = TaskStatus.FAILED
                    task.error = f"Node returned {resp.status_code}"
                    return False
        except httpx.ConnectError:
            node.health.status = NodeStatus.OFFLINE
            task.status = TaskStatus.QUEUED
            task.assigned_node = None
            logger.warning(
                f"[COORD] Node {node.registration.node_id} unreachable — task requeued"
            )
            return False

    def receive_result(self, result: TaskResult) -> None:
        """Handle task completion reported back from a node."""
        task = next((t for t in self.task_queue if t.task_id == result.task_id), None)
        if not task:
            logger.warning(f"[COORD] Unknown task result: {result.task_id}")
            return

        task.status = result.status
        task.result = result.result
        task.error = result.error
        task.completed_at = result.completed_at

        node = self.nodes.get(result.node_id)
        if node:
            node.health.active_tasks = max(0, node.health.active_tasks - 1)

        self.task_queue.remove(task)
        if result.status == TaskStatus.COMPLETED:
            self.completed_tasks.append(task)
            logger.info(f"[COORD] Task {task.task_id} completed on {result.node_id}")
        else:
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.QUEUED
                task.assigned_node = None
                self.task_queue.append(task)
                logger.info(f"[COORD] Task {task.task_id} retry {task.retry_count}/{task.max_retries}")
            else:
                self.failed_tasks.append(task)
                logger.error(f"[COORD] Task {task.task_id} permanently failed: {task.error}")

    # ------------------------------------------------------------------
    # Dispatch Loop
    # ------------------------------------------------------------------

    async def run_dispatch_loop(self) -> None:
        """Main async loop — continuously dispatch queued tasks."""
        self._running = True
        logger.info("[COORD] Dispatch loop started")
        while self._running:
            pending = [t for t in self.task_queue if t.status == TaskStatus.QUEUED]
            for task in pending:
                await self.dispatch_task(task)
            await asyncio.sleep(TASK_POLL_INTERVAL)

    async def run_heartbeat_loop(self) -> None:
        """Poll each node's health endpoint periodically."""
        while self._running:
            for node_id, node in list(self.nodes.items()):
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        url = f"{node.reachable_url()}/health"
                        resp = await client.get(url)
                        if resp.status_code == 200:
                            data = resp.json()
                            node.health = NodeHealth(
                                node_id=node_id,
                                status=NodeStatus.ONLINE,
                                cpu_pct=data.get("cpu_pct", 0),
                                ram_pct=data.get("ram_pct", 0),
                                active_tasks=data.get("active_tasks", 0),
                                queued_tasks=data.get("queued_tasks", 0),
                                uptime_seconds=data.get("uptime_seconds", 0),
                            )
                        else:
                            node.health.status = NodeStatus.ERROR
                except (httpx.ConnectError, httpx.TimeoutException):
                    node.health.status = NodeStatus.OFFLINE
            await asyncio.sleep(NODE_HEARTBEAT_INTERVAL)

    def stop(self) -> None:
        self._running = False

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def status(self) -> dict[str, Any]:
        queued = [t for t in self.task_queue if t.status == TaskStatus.QUEUED]
        running = [t for t in self.task_queue if t.status == TaskStatus.RUNNING]
        return {
            "nodes": {
                n_id: {
                    "name": n.registration.name,
                    "status": n.health.status.value,
                    "cpu_pct": n.health.cpu_pct,
                    "ram_pct": n.health.ram_pct,
                    "active_tasks": n.health.active_tasks,
                    "capabilities": [t.value for t in n.registration.capabilities.tags],
                    "score": n.capability_score([]),
                }
                for n_id, n in self.nodes.items()
            },
            "tasks": {
                "queued": len(queued),
                "running": len(running),
                "completed": len(self.completed_tasks),
                "failed": len(self.failed_tasks),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Node Agent (runs ON each PC)
# ---------------------------------------------------------------------------


class NodeAgent:
    """
    Runs on each individual PC. Registers with the coordinator,
    executes tasks, reports results, and runs 24/7 automation loops.
    """

    def __init__(
        self,
        node_id: str,
        coordinator_url: str,
        capabilities: NodeCapabilities,
    ) -> None:
        self.node_id = node_id
        self.coordinator_url = coordinator_url
        self.capabilities = capabilities
        self.active_tasks: dict[str, dict[str, Any]] = {}
        self._start_time = time.time()
        self._running = False
        self.automation_loops: list[dict[str, Any]] = []

    async def register(self) -> bool:
        """Register this PC with the coordinator."""
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

        reg = NodeRegistration(
            node_id=self.node_id,
            name=f"Node: {hostname}",
            platform=os.name,
            host=local_ip,
            port=8097,
            capabilities=self.capabilities,
            local_ip=local_ip,
        )
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.coordinator_url}/nodes/register",
                    json=reg.model_dump(),
                )
                if resp.status_code == 200:
                    logger.info(f"[NODE:{self.node_id}] Registered with coordinator")
                    return True
        except Exception as e:
            logger.error(f"[NODE:{self.node_id}] Registration failed: {e}")
        return False

    async def heartbeat(self) -> None:
        """Report health metrics to the coordinator."""
        try:
            import psutil
            cpu_pct = psutil.cpu_percent(interval=1)
            ram_pct = psutil.virtual_memory().percent
        except ImportError:
            cpu_pct = 0.0
            ram_pct = 0.0

        health = NodeHealth(
            node_id=self.node_id,
            status=NodeStatus.BUSY if self.active_tasks else NodeStatus.IDLE,
            cpu_pct=cpu_pct,
            ram_pct=ram_pct,
            active_tasks=len(self.active_tasks),
            uptime_seconds=time.time() - self._start_time,
        )
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{self.coordinator_url}/nodes/health",
                    json=health.model_dump(),
                )
        except Exception:
            pass

    async def execute_task(self, task: dict[str, Any]) -> TaskResult:
        """Execute a dispatched task. Override for custom task handlers."""
        task_id = task["task_id"]
        task_type = task.get("task_type", "general")
        payload = task.get("payload", {})

        self.active_tasks[task_id] = task
        logger.info(f"[NODE:{self.node_id}] Executing task {task_id} type={task_type}")

        try:
            result = await self._dispatch_task_type(task_type, payload)
            del self.active_tasks[task_id]
            return TaskResult(
                task_id=task_id,
                node_id=self.node_id,
                status=TaskStatus.COMPLETED,
                result=result,
            )
        except Exception as e:
            del self.active_tasks[task_id]
            logger.error(f"[NODE:{self.node_id}] Task {task_id} failed: {e}")
            return TaskResult(
                task_id=task_id,
                node_id=self.node_id,
                status=TaskStatus.FAILED,
                error=str(e),
            )

    async def _dispatch_task_type(
        self, task_type: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        handlers = {
            "shell": self._run_shell,
            "build": self._run_build,
            "deploy": self._run_deploy,
            "scrape": self._run_scrape,
            "llm": self._run_llm,
            "monitor": self._run_monitor,
        }
        handler = handlers.get(task_type, self._run_generic)
        return await handler(payload)

    async def _run_shell(self, payload: dict[str, Any]) -> dict[str, Any]:
        import subprocess
        cmd = payload.get("command", "echo no-command")
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return {
            "returncode": proc.returncode,
            "stdout": stdout.decode(),
            "stderr": stderr.decode(),
        }

    async def _run_build(self, payload: dict[str, Any]) -> dict[str, Any]:
        repo = payload.get("repo_path", ".")
        build_cmd = payload.get("build_command", "echo no-build-command")
        result = await self._run_shell({"command": f"cd {repo} && {build_cmd}"})
        return {"type": "build", **result}

    async def _run_deploy(self, payload: dict[str, Any]) -> dict[str, Any]:
        service = payload.get("service", "unknown")
        deploy_cmd = payload.get("deploy_command", "echo no-deploy-command")
        result = await self._run_shell({"command": deploy_cmd})
        return {"type": "deploy", "service": service, **result}

    async def _run_scrape(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = payload.get("url", "")
        return {"type": "scrape", "url": url, "status": "queued_for_playwright"}

    async def _run_llm(self, payload: dict[str, Any]) -> dict[str, Any]:
        prompt = payload.get("prompt", "")
        model = payload.get("model", "llama3")
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    "http://localhost:11434/api/generate",
                    json={"model": model, "prompt": prompt, "stream": False},
                )
                return {"type": "llm", "response": resp.json().get("response", "")}
        except Exception as e:
            return {"type": "llm", "error": str(e)}

    async def _run_monitor(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            import psutil
            return {
                "type": "monitor",
                "cpu_pct": psutil.cpu_percent(),
                "ram_pct": psutil.virtual_memory().percent,
                "disk_pct": psutil.disk_usage("/").percent,
            }
        except ImportError:
            return {"type": "monitor", "status": "psutil_not_installed"}

    async def _run_generic(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"type": "generic", "payload_echo": payload, "status": "acknowledged"}

    def add_automation_loop(
        self,
        name: str,
        task_type: str,
        payload: dict[str, Any],
        interval_seconds: int = 3600,
    ) -> None:
        self.automation_loops.append({
            "name": name,
            "task_type": task_type,
            "payload": payload,
            "interval_seconds": interval_seconds,
            "last_run": 0.0,
        })
        logger.info(f"[NODE:{self.node_id}] Automation loop registered: {name} every {interval_seconds}s")

    async def run_automation_loops(self) -> None:
        """Run registered automation loops on schedule."""
        while self._running:
            now = time.time()
            for loop in self.automation_loops:
                if now - loop["last_run"] >= loop["interval_seconds"]:
                    loop["last_run"] = now
                    logger.info(f"[NODE:{self.node_id}] Running loop: {loop['name']}")
                    asyncio.create_task(
                        self._dispatch_task_type(loop["task_type"], loop["payload"])
                    )
            await asyncio.sleep(60)

    async def run(self) -> None:
        """Start the node agent — register, heartbeat, and automation loops."""
        self._running = True
        await self.register()
        await asyncio.gather(
            self._heartbeat_loop(),
            self.run_automation_loops(),
        )

    async def _heartbeat_loop(self) -> None:
        while self._running:
            await self.heartbeat()
            await asyncio.sleep(NODE_HEARTBEAT_INTERVAL)


# ---------------------------------------------------------------------------
# FastAPI — Coordinator Service
# ---------------------------------------------------------------------------

coordinator = MultiPCCoordinator()

app = FastAPI(
    title="ARK95X Multi-PC Coordinator",
    description="Sovereign multi-node coordinator. Each PC is an autonomous agent.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    asyncio.create_task(coordinator.run_dispatch_loop())
    asyncio.create_task(coordinator.run_heartbeat_loop())
    logger.info("[COORD] Multi-PC Coordinator started")


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "service": "multi_pc_coordinator",
        "status": "operational",
        "nodes_registered": len(coordinator.nodes),
        "nodes_online": len(coordinator.online_nodes()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/status")
async def status() -> dict[str, Any]:
    return coordinator.status()


@app.post("/nodes/register")
async def register_node(reg: NodeRegistration) -> dict[str, Any]:
    node = coordinator.register_node(reg)
    return {"status": "registered", "node_id": reg.node_id, "score": node.capability_score([])}


@app.post("/nodes/health")
async def update_health(health: NodeHealth) -> dict[str, str]:
    coordinator.update_health(health)
    return {"status": "updated"}


@app.get("/nodes")
async def list_nodes() -> dict[str, Any]:
    return {
        node_id: {
            "name": node.registration.name,
            "platform": node.registration.platform,
            "status": node.health.status.value,
            "capabilities": [t.value for t in node.registration.capabilities.tags],
        }
        for node_id, node in coordinator.nodes.items()
    }


@app.post("/tasks/submit")
async def submit_task(task: CoordinatorTask) -> dict[str, Any]:
    submitted = coordinator.submit_task(task)
    return {"task_id": submitted.task_id, "status": submitted.status.value}


@app.post("/tasks/result")
async def task_result(result: TaskResult) -> dict[str, str]:
    coordinator.receive_result(result)
    return {"status": "received"}


@app.get("/tasks")
async def list_tasks() -> dict[str, Any]:
    return {
        "queued": [
            {"task_id": t.task_id, "title": t.title, "status": t.status.value}
            for t in coordinator.task_queue
        ],
        "completed": len(coordinator.completed_tasks),
        "failed": len(coordinator.failed_tasks),
    }


@app.post("/tasks/split")
async def split_task_endpoint(
    parent_id: str,
    subtasks: list[dict[str, Any]],
) -> dict[str, Any]:
    parent = next(
        (t for t in coordinator.task_queue if t.task_id == parent_id), None
    )
    if not parent:
        raise HTTPException(404, f"Parent task not found: {parent_id}")
    subs = coordinator.split_task(parent, subtasks)
    return {"parent_id": parent_id, "subtask_ids": [s.task_id for s in subs]}


@app.get("/nodes/{node_id}/assign")
async def best_node_for_capability(capabilities: str = "") -> dict[str, Any]:
    tags = [CapabilityTag(c) for c in capabilities.split(",") if c]
    dummy_task = CoordinatorTask(title="probe", required_capabilities=tags)
    node = coordinator.best_node_for_task(dummy_task)
    if not node:
        return {"node": None, "reason": "No available node with those capabilities"}
    return {
        "node_id": node.registration.node_id,
        "name": node.registration.name,
        "score": node.capability_score(tags),
        "status": node.health.status.value,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("core.multi_pc_coordinator:app", host="0.0.0.0", port=COORDINATOR_PORT, reload=True)
