"""ARK95X Credit-Proof Failover Router - Unit Tests
Uses fake backends so no real network calls are made; verifies task
selection, backend fallback ordering, and ARK-STATE.json read/write.
"""
import asyncio
import json

import pytest

from router.failover import FailoverRouter, BackendAdapter


class FakeBackend(BackendAdapter):
    def __init__(self, name, priority, available=True, response="ok", raises=False):
        self.name = name
        self.priority = priority
        self._available = available
        self._response = response
        self._raises = raises
        self.dispatch_calls = []

    async def is_available(self) -> bool:
        return self._available

    async def dispatch(self, prompt: str) -> str:
        self.dispatch_calls.append(prompt)
        if self._raises:
            raise RuntimeError("backend exploded")
        return self._response


def write_state(path, todo_queue):
    state = {
        "updated_at": "2026-01-01T00:00:00Z",
        "updated_by": "test",
        "todo_queue": todo_queue,
    }
    path.write_text(json.dumps(state))
    return state


class TestFindNextTask:
    def test_returns_first_pending_with_satisfied_deps(self, tmp_path):
        state = {
            "todo_queue": [
                {"id": "T1", "status": "done", "depends_on": []},
                {"id": "T2", "status": "pending", "depends_on": ["T1"]},
                {"id": "T3", "status": "pending", "depends_on": ["T2"]},
            ]
        }
        task = FailoverRouter.find_next_task(state)
        assert task["id"] == "T2"

    def test_skips_tasks_with_unmet_dependencies(self):
        state = {
            "todo_queue": [
                {"id": "T1", "status": "pending", "depends_on": ["T0"]},
                {"id": "T2", "status": "pending", "depends_on": []},
            ]
        }
        task = FailoverRouter.find_next_task(state)
        assert task["id"] == "T2"

    def test_returns_none_when_nothing_pending(self):
        state = {"todo_queue": [{"id": "T1", "status": "done", "depends_on": []}]}
        assert FailoverRouter.find_next_task(state) is None


class TestSelectBackend:
    def test_picks_first_available_in_priority_order(self):
        b1 = FakeBackend("claude", 1, available=False)
        b2 = FakeBackend("ollama", 2, available=True)
        b3 = FakeBackend("groq", 3, available=True)
        router = FailoverRouter(state_path="unused.json", backends=[b1, b2, b3])
        backend = asyncio.run(router.select_backend())
        assert backend.name == "ollama"

    def test_returns_none_if_all_unavailable(self):
        b1 = FakeBackend("claude", 1, available=False)
        b2 = FakeBackend("ollama", 2, available=False)
        router = FailoverRouter(state_path="unused.json", backends=[b1, b2])
        assert asyncio.run(router.select_backend()) is None


class TestDispatchNext:
    def test_no_pending_tasks(self, tmp_path):
        state_path = tmp_path / "ARK-STATE.json"
        write_state(state_path, [{"id": "T1", "status": "done", "depends_on": []}])
        router = FailoverRouter(state_path=str(state_path), backends=[FakeBackend("claude", 1)])
        result = asyncio.run(router.dispatch_next())
        assert result["status"] == "no_pending_tasks"

    def test_no_backend_available(self, tmp_path):
        state_path = tmp_path / "ARK-STATE.json"
        write_state(state_path, [{"id": "T1", "status": "pending", "depends_on": []}])
        router = FailoverRouter(
            state_path=str(state_path),
            backends=[FakeBackend("claude", 1, available=False)],
        )
        result = asyncio.run(router.dispatch_next())
        assert result["status"] == "no_backend_available"
        assert result["task_id"] == "T1"

    def test_dispatches_and_updates_state(self, tmp_path):
        state_path = tmp_path / "ARK-STATE.json"
        write_state(state_path, [{"id": "T1", "status": "pending", "depends_on": [], "phase": 4, "title": "do the thing"}])
        fake = FakeBackend("ollama", 2, available=True, response="I did it")
        router = FailoverRouter(state_path=str(state_path), backends=[fake])

        result = asyncio.run(router.dispatch_next())

        assert result["status"] == "dispatched"
        assert result["backend"] == "ollama"
        assert result["response"] == "I did it"
        assert len(fake.dispatch_calls) == 1
        assert "T1" in fake.dispatch_calls[0]
        assert "do the thing" in fake.dispatch_calls[0]

        saved = json.loads(state_path.read_text())
        task = saved["todo_queue"][0]
        assert task["status"] == "in_progress"
        assert task["assigned_backend"] == "ollama"
        assert "assigned_at" in task
        assert saved["updated_by"] == "ollama"

    def test_dispatch_failure_is_reported_not_raised(self, tmp_path):
        state_path = tmp_path / "ARK-STATE.json"
        write_state(state_path, [{"id": "T1", "status": "pending", "depends_on": [], "phase": 4, "title": "x"}])
        fake = FakeBackend("groq", 3, available=True, raises=True)
        router = FailoverRouter(state_path=str(state_path), backends=[fake])

        result = asyncio.run(router.dispatch_next())

        assert result["status"] == "dispatch_failed"
        assert result["backend"] == "groq"
        # state must be untouched -- task remains pending for the next attempt
        saved = json.loads(state_path.read_text())
        assert saved["todo_queue"][0]["status"] == "pending"

    def test_falls_through_to_next_backend_when_first_unavailable(self, tmp_path):
        state_path = tmp_path / "ARK-STATE.json"
        write_state(state_path, [{"id": "T1", "status": "pending", "depends_on": [], "phase": 4, "title": "x"}])
        claude = FakeBackend("claude", 1, available=False)
        ollama = FakeBackend("ollama", 2, available=True, response="picked up by ollama")
        router = FailoverRouter(state_path=str(state_path), backends=[claude, ollama])

        result = asyncio.run(router.dispatch_next())

        assert result["backend"] == "ollama"
        assert len(claude.dispatch_calls) == 0
        assert len(ollama.dispatch_calls) == 1
