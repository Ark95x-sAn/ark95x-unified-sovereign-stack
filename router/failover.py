"""ARK95X Credit-Proof Failover Router
Reads the todo_queue in ARK-STATE.json and dispatches the next available
task to whichever backend is reachable: Claude, local Ollama (:11434),
Groq, or Gemini. Claude running out of credits becomes a routing event,
not a stop -- the next available backend picks up the same task from the
same genome file.
"""
import os
import json
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("ark95x.router.failover")

DEFAULT_STATE_PATH = "ARK-STATE.json"

HANDOFF_PROMPT_TEMPLATE = """You are resuming the ARK95X Command Ledger build.
Read ARK-STATE.json (the build genome) and HANDOFF.md in this repo for full
context before doing anything else.

Next pending task:
  id: {task_id}
  phase: {phase}
  title: {title}

Execute this task, then update its entry in ARK-STATE.json's todo_queue to
status "done" and bump updated_at/updated_by before you stop."""


class BackendAdapter(ABC):
    name: str
    priority: int

    @abstractmethod
    async def is_available(self) -> bool:
        ...

    @abstractmethod
    async def dispatch(self, prompt: str) -> str:
        ...


class ClaudeBackend(BackendAdapter):
    name = "claude"
    priority = 1

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

    async def is_available(self) -> bool:
        return bool(self.api_key)

    async def dispatch(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            r.raise_for_status()
            return r.json()["content"][0]["text"]


class OllamaBackend(BackendAdapter):
    name = "ollama"
    priority = 2

    def __init__(self):
        self.endpoint = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3")

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                r = await client.get(f"{self.endpoint}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    async def dispatch(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                f"{self.endpoint}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
            )
            r.raise_for_status()
            return r.json().get("response", "")


class GroqBackend(BackendAdapter):
    name = "groq"
    priority = 3

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    async def is_available(self) -> bool:
        return bool(self.api_key)

    async def dispatch(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": [{"role": "user", "content": prompt}]},
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]


class GeminiBackend(BackendAdapter):
    name = "gemini"
    priority = 4

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    async def is_available(self) -> bool:
        return bool(self.api_key)

    async def dispatch(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
                params={"key": self.api_key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            r.raise_for_status()
            data = r.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]


def default_backends() -> List[BackendAdapter]:
    backends = [ClaudeBackend(), OllamaBackend(), GroqBackend(), GeminiBackend()]
    return sorted(backends, key=lambda b: b.priority)


class FailoverRouter:
    """Dispatches the next pending ARK-STATE.json task to an available backend.

    This is arc_x's real "route_agents"/"simulate" job (docs/control-plane-pass-1.md:
    "ARC X ... Final dispatch and cross-agent priority"). When a control_plane is
    supplied, every dispatch decision is requested and reported through it as
    arc_x, under its `routing` authority scope -- routing is not in
    control_plane.APPROVAL_REQUIRED_ACTION_CLASSES, so it auto-queues and proceeds
    without blocking on a human, matching arc_x's role as the coordinator, not a
    second approval gate.
    """

    def __init__(
        self,
        state_path: str = DEFAULT_STATE_PATH,
        backends: Optional[List[BackendAdapter]] = None,
        control_plane: Optional[Any] = None,
    ):
        self.state_path = Path(state_path)
        self.backends = backends if backends is not None else default_backends()
        self.control_plane = control_plane

    def load_state(self) -> Dict[str, Any]:
        return json.loads(self.state_path.read_text())

    def save_state(self, state: Dict[str, Any]):
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.state_path.write_text(json.dumps(state, indent=2) + "\n")

    @staticmethod
    def find_next_task(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """First todo_queue entry that is pending with all dependencies done."""
        done_ids = {t["id"] for t in state.get("todo_queue", []) if t.get("status") == "done"}
        for task in state.get("todo_queue", []):
            if task.get("status") != "pending":
                continue
            if all(dep in done_ids for dep in task.get("depends_on", [])):
                return task
        return None

    async def select_backend(self) -> Optional[BackendAdapter]:
        for backend in self.backends:
            if await backend.is_available():
                return backend
        return None

    async def dispatch_next(self) -> Dict[str, Any]:
        state = self.load_state()
        task = self.find_next_task(state)
        if task is None:
            self._report_arc_x(status="idle", payload={"result": "no_pending_tasks"})
            return {"status": "no_pending_tasks"}

        backend = await self.select_backend()
        if backend is None:
            self._report_arc_x(status="no_backend", payload={"task_id": task["id"]})
            return {"status": "no_backend_available", "task_id": task["id"]}

        # arc_x's real routing decision: which backend gets this task, and
        # why (priority-ordered availability). Routing is in arc_x's
        # authority scope and not approval-required, so this proceeds
        # immediately -- it is evidence of the decision, not a block.
        self._request_arc_x_route(task_id=task["id"], backend=backend.name)

        prompt = HANDOFF_PROMPT_TEMPLATE.format(
            task_id=task["id"], phase=task.get("phase"), title=task["title"]
        )
        try:
            response = await backend.dispatch(prompt)
        except Exception as e:
            logger.error(f"Backend {backend.name} failed to dispatch task {task['id']}: {e}")
            self._report_arc_x(
                status="dispatch_failed",
                payload={"task_id": task["id"], "backend": backend.name, "error": str(e)},
            )
            return {
                "status": "dispatch_failed",
                "task_id": task["id"],
                "backend": backend.name,
                "error": str(e),
            }

        task["status"] = "in_progress"
        task["assigned_backend"] = backend.name
        task["assigned_at"] = datetime.now(timezone.utc).isoformat()
        state["updated_by"] = backend.name
        self.save_state(state)

        logger.info(f"Task {task['id']} dispatched to {backend.name}")
        self._report_arc_x(
            status="routed",
            payload={"task_id": task["id"], "backend": backend.name, "evidence_ref": task["id"]},
        )
        return {
            "status": "dispatched",
            "task_id": task["id"],
            "backend": backend.name,
            "response": response,
        }

    def _request_arc_x_route(self, task_id: str, backend: str) -> Optional[Dict[str, Any]]:
        if self.control_plane is None:
            return None
        return self.control_plane.request_action(
            agent_id="arc_x",
            action=f"route_task:{task_id}",
            action_class="routing",
            payload={"task_id": task_id, "selected_backend": backend},
        )

    def _report_arc_x(self, status: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.control_plane is None:
            return None
        return self.control_plane.report(
            agent_id="arc_x",
            status=status,
            payload={**payload, "observed_at": datetime.now(timezone.utc).isoformat()},
        )


async def main():
    logging.basicConfig(level=logging.INFO)
    router = FailoverRouter()
    result = await router.dispatch_next()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
