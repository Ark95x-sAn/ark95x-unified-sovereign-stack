"""Regression tests for prototype crew outcomes; no device or provider calls."""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest

from command.unified_crew import (
    AgentRole, BaseAgent, CrewTask, SharedMemory, UnifiedCrew,
)


class CrewOutcomeTests(unittest.TestCase):
    def test_default_workers_do_not_complete_tasks_or_invent_tool_use(self):
        crew = UnifiedCrew()
        for role in (AgentRole.MANUS, AgentRole.ZENCODE, AgentRole.VIBECODER):
            task = CrewTask(role.value, "fixture request", role)
            result = crew.conductor.dispatch(task)
            self.assertEqual(task.status, "not_implemented")
            self.assertIs(task.executed, False)
            self.assertIs(task.verified, False)
            self.assertIn("NOT_IMPLEMENTED", result)
            self.assertNotIn("complete", result.lower())
            record = crew.memory.read(f"{role.value}:{task.task_id}")
            self.assertEqual(record["status"], "not_implemented")
            self.assertIs(record["verified"], False)

    def test_unknown_worker_is_recorded_as_blocked(self):
        crew = UnifiedCrew()
        task = CrewTask("missing", "fixture request", AgentRole.CONDUCTOR)
        crew.conductor.dispatch(task)
        self.assertEqual(task.status, "blocked")
        self.assertIs(task.executed, False)
        self.assertIs(task.verified, False)
        self.assertIn("No agent", task.result)

    def test_worker_exception_does_not_erase_later_task_outcomes(self):
        class BrokenAgent(BaseAgent):
            def execute(self, task):
                raise RuntimeError("fixture failure")

        crew = UnifiedCrew()
        crew.conductor.register(BrokenAgent(AgentRole.MANUS, crew.memory))
        tasks = [CrewTask("broken", "fixture", AgentRole.MANUS),
                 CrewTask("later", "fixture", AgentRole.ZENCODE)]
        with contextlib.redirect_stdout(io.StringIO()):
            results = crew.kickoff(tasks)
        self.assertEqual(len(results), 2)
        self.assertEqual(tasks[0].status, "failed")
        self.assertIsNone(tasks[0].executed)
        self.assertIn("fixture failure", results[0])
        self.assertEqual(tasks[1].status, "not_implemented")

    def test_worker_cannot_promote_its_own_success_to_verified(self):
        class SelfCertifyingAgent(BaseAgent):
            def execute(self, task):
                task.status = "done"
                task.executed = True
                task.verified = True
                return "worker says complete"

        crew = UnifiedCrew()
        crew.conductor.register(SelfCertifyingAgent(AgentRole.MANUS, crew.memory))
        task = CrewTask("self-report", "fixture", AgentRole.MANUS)
        crew.conductor.dispatch(task)
        self.assertEqual(task.status, "reported")
        self.assertIsNone(task.executed)
        self.assertIs(task.verified, False)
        self.assertIs(crew.memory.read("manus:self-report")["verified"], False)

    def test_malformed_worker_result_fails_visibly(self):
        class MalformedAgent(BaseAgent):
            def execute(self, task):
                return None

        crew = UnifiedCrew()
        crew.conductor.register(MalformedAgent(AgentRole.MANUS, crew.memory))
        task = CrewTask("malformed", "fixture", AgentRole.MANUS)
        crew.conductor.dispatch(task)
        self.assertEqual(task.status, "failed")
        self.assertIs(task.verified, False)

    def test_batch_retains_each_outcome_and_calls_the_single_task_hooks(self):
        from command.dispatcher import Dispatcher, DispatchRequest

        dispatcher = Dispatcher(crew=UnifiedCrew(), fury=False)
        observed = []
        dispatcher.add_hook(lambda task, result: observed.append(task.task_id))
        requests = [DispatchRequest("fixture A", "research", priority=1, task_id="a"),
                    DispatchRequest("fixture B", "code", priority=9, task_id="b")]
        results = dispatcher.batch_route(requests)
        self.assertEqual(len(results), 2)
        self.assertEqual(observed, ["b", "a"])
        self.assertEqual([row["task_id"] for row in dispatcher.history], ["b", "a"])
        self.assertTrue(all(row["status"] == "not_implemented" for row in dispatcher.history))
        self.assertEqual(dispatcher.summary()["by_status"], {"not_implemented": 2})
        self.assertEqual(dispatcher.summary()["verified_tasks"], 0)

    def test_empty_batch_does_not_invent_completion(self):
        from command.dispatcher import Dispatcher

        dispatcher = Dispatcher(crew=UnifiedCrew(), fury=False)
        self.assertEqual(dispatcher.batch_route([]), [])
        self.assertEqual(dispatcher.summary()["total_dispatched"], 0)
        self.assertEqual(dispatcher.summary()["verified_tasks"], 0)

    def test_cli_reports_unimplemented_work_with_nonzero_exit(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "-m", "command.run_crew", "--mode", "quick", "--quiet"],
            cwd=root, text=True, capture_output=True, timeout=15,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("All tasks complete", result.stdout)
        self.assertNotIn("STACK LIVE", result.stdout)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["by_status"], {"not_implemented": 3})
        self.assertEqual(summary["verified_tasks"], 0)


if __name__ == "__main__":
    unittest.main()
