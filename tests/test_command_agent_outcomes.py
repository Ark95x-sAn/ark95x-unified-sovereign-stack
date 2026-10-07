"""Local-only command outcome tests; no models, services, or network required."""
import asyncio
from copy import deepcopy
import json
import unittest
from unittest.mock import AsyncMock

from command.agents import (
    CommandCenter, ManusAgent, ManusTask, OutputFormat, VibeCoderAgent, ZenCodeAgent,
)


class AgentOutcomeTests(unittest.IsolatedAsyncioTestCase):
    def assert_unimplemented(self, result):
        self.assertEqual(result["status"], "not_implemented")
        self.assertIs(result["executed"], False)
        self.assertIs(result["verified"], False)
        self.assertNotIn("score", result)
        self.assertNotIn("vulnerabilities", result)
        self.assertNotIn("findings", result)

    async def test_all_manus_defaults_are_unimplemented(self):
        agent = ManusAgent()
        for skill_name in agent.SKILLS:
            with self.subTest(skill=skill_name):
                task = ManusTask(skill_name, skill_name, "fixture-only", {})
                result = await agent.execute(task)
                self.assert_unimplemented(result)
                self.assert_unimplemented(result["result"])
                self.assertEqual(task.status, "not_implemented")
        self.assertEqual(agent.metrics["tasks_completed"], 0)
        self.assertEqual(agent.completed, [])
        self.assertEqual(agent.active_tasks, {})

    async def test_all_zen_defaults_and_architecture_remain_unimplemented(self):
        agent = ZenCodeAgent()
        for skill_name in agent.SKILLS:
            with self.subTest(skill=skill_name):
                result = await agent.analyze("fixture-only", skill_name)
                self.assert_unimplemented(result)
                self.assert_unimplemented(result["result"])
        self.assert_unimplemented(await agent.analyze("fixture-only"))
        self.assert_unimplemented(await agent.design_architecture({"name": "fixture-only"}))
        self.assertEqual((await agent.deep_think("fixture-only"))["status"], "blocked")
        self.assertEqual(agent.analysis_cache, {})
        self.assertEqual(agent.architecture_registry, {})
        self.assertEqual(agent.quality_scores, {})
        for key in ("analyses_completed", "architectures_designed", "reviews_completed"):
            self.assertEqual(agent.metrics[key], 0)

    async def test_vibe_defaults_preserve_input_and_count_no_builds(self):
        agent = VibeCoderAgent()
        description = ("Keep this entire input.\n界 — ") * 30
        for skill in agent.SKILLS.values():
            with self.subTest(skill=skill.name):
                result = await getattr(agent, skill.handler)(description)
                self.assert_unimplemented(result)
                self.assertEqual(result["target"], description)
        project_ids = []
        for output_format in OutputFormat:
            result = await agent.vibe_create(description, output_format)
            self.assert_unimplemented(result)
            project_ids.append(result["project_id"])
        self.assertEqual(len(set(project_ids)), len(OutputFormat))
        self.assertEqual(agent.status()["active_projects"], 0)
        self.assertTrue(all(project.status == "not_implemented" for project in agent.projects.values()))
        rapid = await agent.rapid_build([{"description": description}, None, {}])
        self.assertEqual(rapid["built"], 0)
        self.assertEqual(rapid["results_count"], 3)
        self.assertEqual(rapid["status"], "blocked")
        self.assertEqual((await agent.rapid_build([]))["status"], "empty")
        self.assertEqual((await agent.flow_state(description))["status"], "blocked")
        for key in ("prototypes_built", "code_generated_lines", "creative_solutions"):
            self.assertEqual(agent.metrics[key], 0)

    async def test_custom_success_is_reported_without_completed_credit(self):
        claimed = {"status": "success", "executed": True, "verified": True,
                   "artifact": "fixture://self-reported"}
        manus = ManusAgent()
        manus._skill_code_gen = AsyncMock(return_value=claimed)
        task = ManusTask("m1", "code_generation", "fixture-only", {})
        result = await manus.execute(task)
        self.assertEqual(result["status"], "reported")
        self.assertIsNone(result["executed"])
        self.assertIs(result["verified"], False)
        self.assertEqual(result["result"], claimed)
        self.assertEqual(task.status, "reported")
        self.assertEqual(manus.metrics["tasks_completed"], 0)
        self.assertEqual(manus.completed, [])

        zen = ZenCodeAgent()
        zen._skill_code_review = AsyncMock(return_value=claimed)
        first = await zen.analyze("same-target-label", "code_review")
        second = await zen.analyze("same-target-label", "code_review")
        self.assertEqual(zen._skill_code_review.await_count, 2)
        self.assertEqual(first["status"], second["status"])
        self.assertEqual(second["status"], "reported")
        self.assertIs(second["verified"], False)
        self.assertEqual(zen.metrics["analyses_completed"], 0)
        self.assertEqual(zen.analysis_cache, {})

        vibe = VibeCoderAgent()
        vibe._skill_nl_to_code = AsyncMock(return_value=claimed)
        result = await vibe.vibe_create("fixture-only")
        self.assertEqual(result["status"], "reported")
        self.assertIs(result["verified"], False)
        self.assertEqual(vibe.projects[result["project_id"]].status, "reported")
        self.assertEqual(vibe.metrics["prototypes_built"], 0)

    async def test_manus_exception_runs_once_and_retains_uncertain_effects(self):
        agent = ManusAgent()
        agent._skill_file_ops = AsyncMock(side_effect=RuntimeError("failed after attempted effect"))
        task = ManusTask("m1", "file_operations", "fixture-only", {}, max_retries=20)
        result = await agent.execute(task)
        self.assertEqual(agent._skill_file_ops.await_count, 1)
        self.assertEqual(task.retries, 0)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error_type"], "RuntimeError")
        self.assertEqual(result["error"], "failed after attempted effect")
        self.assertIsNone(result["executed"])
        self.assertIs(result["verified"], False)
        self.assertEqual(task.status, "failed")
        self.assertEqual(agent.active_tasks, {})
        self.assertEqual(agent.metrics["tasks_failed"], 1)

    async def test_unknown_requests_do_not_fallback_to_another_operation(self):
        manus = ManusAgent()
        manus._default_handler = AsyncMock()
        outcome = await manus.execute(ManusTask("m1", "unknown-operation", "fixture-only", {}))
        self.assertEqual(outcome["status"], "blocked")
        manus._default_handler.assert_not_awaited()
        zen = ZenCodeAgent()
        zen._skill_pattern_analysis = AsyncMock()
        self.assertEqual((await zen.analyze("fixture-only", "unknown-analysis"))["status"], "blocked")
        zen._skill_pattern_analysis.assert_not_awaited()
        vibe = VibeCoderAgent()
        vibe._generate = AsyncMock()
        self.assertEqual((await vibe.vibe_create("fixture-only", "unknown-format"))["status"], "blocked")
        self.assertEqual((await vibe.vibe_create("   "))["status"], "blocked")
        vibe._generate.assert_not_awaited()

    async def test_malformed_handler_returns_fail_without_completing(self):
        malformed = [None, "complete", [], {}, {"status": []}, {"status": "invented"},
                     {"status": "success", "verified": "yes"},
                     {"status": "success", "error": "also failed"},
                     {"status": "success", "success": False},
                     {"status": "success", "isError": True},
                     {"status": "success", "success": 1},
                     {"status": "success", "isError": "false"},
                     {"status": "not_implemented", "executed": True}]
        for raw in malformed:
            with self.subTest(result=raw):
                agent = ManusAgent()
                agent._skill_code_gen = AsyncMock(return_value=raw)
                outcome = await agent.execute(ManusTask("m1", "code_generation", "fixture-only", {}))
                self.assertEqual(outcome["status"], "failed")
                self.assertEqual(outcome["error_type"], "invalid_result")
                self.assertEqual(outcome["result"], raw)
                self.assertEqual(agent.metrics["tasks_completed"], 0)
                self.assertEqual(agent.completed, [])

    async def test_retained_handler_output_is_detached_from_original_object(self):
        agent = ManusAgent()
        raw = {"status": "success", "payload": {"lines": ["original"]}}
        agent._skill_code_gen = AsyncMock(return_value=raw)
        result = await agent.execute(ManusTask("m1", "code_generation", "fixture-only", {}))
        raw["status"] = "failed"
        raw["payload"]["lines"].append("late mutation")
        self.assertEqual(result["result"]["status"], "success")
        self.assertEqual(result["result"]["payload"]["lines"], ["original"])


class CommandBatchOutcomeTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty_batch_has_no_fabricated_result(self):
        center = CommandCenter()
        result = await center.fury_deploy([])
        self.assertEqual(result["status"], "empty")
        self.assertEqual(result["fury_deploy"], "empty")
        self.assertEqual(result["results_count"], 0)
        self.assertEqual(result["dispatched_count"], 0)
        self.assertEqual(result["results"], [])
        self.assertIs(result["executed"], False)
        self.assertIs(result["verified"], False)

    async def test_default_mixed_batch_preserves_each_input_in_order(self):
        tasks = [
            {"id": "v1", "agent": "vibecoder", "description": "fixture prototype"},
            {"id": "m1", "agent": "manus", "action": "system_audit", "target": "fixture-audit"},
            {"id": "z1", "agent": "zencode", "type": "security_scan", "target": "fixture-scan"},
            {"id": "m2", "agent": "manus", "action": "documentation", "target": "fixture-docs"},
        ]
        result = await CommandCenter().fury_deploy(tasks)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["fury_deploy"], "blocked")
        self.assertEqual(result["results_count"], len(tasks))
        self.assertEqual(result["requested_count"], len(tasks))
        self.assertEqual([r["index"] for r in result["results"]], list(range(len(tasks))))
        self.assertEqual([r["task_id"] for r in result["results"]], [t["id"] for t in tasks])
        self.assertEqual([r["input"] for r in result["results"]], tasks)
        self.assertTrue(all(r["status"] == "not_implemented" for r in result["results"]))
        self.assertIs(result["executed"], False)
        self.assertIs(result["verified"], False)

    async def test_bad_requests_remain_visible_and_are_never_dispatched(self):
        center = CommandCenter()
        center.manus.execute = AsyncMock()
        center.zencode.analyze = AsyncMock()
        center.vibecoder.vibe_create = AsyncMock()
        tasks = [None, "task", {}, {"agent": "unknown"}, {"agent": []},
                 {"agent": "manus", "id": "missing-fields"},
                 {"agent": "manus", "id": "bad-params", "action": "system_audit", "target": "x", "params": []},
                 {"agent": "manus", "id": "unknown-skill", "action": "unknown", "target": "x"},
                 {"agent": "zencode", "target": "x", "type": "unknown"},
                 {"agent": "zencode", "target": "x", "type": []},
                 {"agent": "vibecoder", "description": " "},
                 {"agent": "vibecoder", "id": [], "description": "x"}]
        result = await center.fury_deploy(tasks)
        self.assertEqual(result["results_count"], len(tasks))
        self.assertEqual(result["dispatched_count"], 0)
        self.assertEqual([r["input"] for r in result["results"]], tasks)
        self.assertTrue(all(r["status"] == "blocked" for r in result["results"]))
        center.manus.execute.assert_not_awaited()
        center.zencode.analyze.assert_not_awaited()
        center.vibecoder.vibe_create.assert_not_awaited()

    async def test_mixed_reports_exceptions_unknowns_and_bad_results_are_retained(self):
        center = CommandCenter()
        claimed = {"status": "success", "verified": True, "executed": True}

        async def manus(task):
            await asyncio.sleep(0)
            return claimed if task.task_id == "m1" else "malformed output"

        center.manus.execute = manus
        center.zencode.analyze = AsyncMock(side_effect=RuntimeError("fixture boom"))
        center.vibecoder.vibe_create = AsyncMock(return_value={"status": "blocked", "executed": False})
        tasks = [
            {"id": "m1", "agent": "manus", "action": "system_audit", "target": "fixture"},
            {"id": "x1", "agent": "missing-worker"},
            {"id": "z1", "agent": "zencode", "target": "fixture"},
            {"id": "v1", "agent": "vibecoder", "description": "fixture"},
            {"id": "m2", "agent": "manus", "action": "system_audit", "target": "fixture"},
        ]
        result = await center.fury_deploy(tasks)
        records = result["results"]
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["results_count"], 5)
        self.assertEqual(result["dispatched_count"], 4)
        self.assertEqual([r["task_id"] for r in records], [t["id"] for t in tasks])
        self.assertEqual([r["status"] for r in records], ["reported", "blocked", "failed", "blocked", "failed"])
        self.assertEqual(records[0]["result"], claimed)
        self.assertTrue(all(r["verified"] is False for r in records))
        self.assertEqual(records[2]["error_type"], "RuntimeError")
        self.assertEqual(records[2]["error"], "fixture boom")
        self.assertEqual(records[4]["error_type"], "invalid_result")
        self.assertEqual(records[4]["result"], "malformed output")

    async def test_batch_status_never_upgrades_reports_to_verified_completion(self):
        cases = [(["success", "completed"], "reported"),
                 (["failed", "failed"], "failed"),
                 (["blocked", "not_implemented"], "blocked"),
                 (["success", "failed"], "partial"),
                 (["partial"], "partial"),
                 (["running", "queued"], "blocked")]
        for states, expected in cases:
            with self.subTest(states=states):
                center = CommandCenter()
                center.vibecoder.vibe_create = AsyncMock(side_effect=[{"status": state} for state in states])
                result = await center.fury_deploy([{"agent": "vibecoder", "description": str(i)} for i in range(len(states))])
                self.assertEqual(result["status"], expected)
                self.assertEqual(result["fury_deploy"], expected)
                self.assertIs(result["verified"], False)
                self.assertNotIn(result["status"], {"complete", "completed", "success"})

    async def test_worker_mutation_cannot_rewrite_caller_input_or_task_identity(self):
        center = CommandCenter()
        tasks = [{"id": "original-id", "agent": "manus", "action": "code_generation",
                  "target": "keep\nall\nlines", "params": {"nested": {"values": ["original"]}}}]
        before = deepcopy(tasks)

        async def mutate(task):
            task.params["nested"]["values"].append("handler edit")
            task.task_id = "handler rewrite"
            return {"status": "success"}

        center.manus._skill_code_gen = mutate
        result = await center.fury_deploy(tasks)
        self.assertEqual(tasks, before)
        self.assertEqual(result["results"][0]["input"], before[0])
        self.assertEqual(result["results"][0]["task_id"], "original-id")
        self.assertEqual(center.manus.active_tasks, {})

    async def test_duplicate_ids_block_every_occurrence_before_execution(self):
        center = CommandCenter()
        center.manus.execute = AsyncMock()
        task = {"id": "duplicate", "agent": "manus", "action": "system_audit", "target": "fixture"}
        result = await center.fury_deploy([task, deepcopy(task)])
        self.assertEqual(result["results_count"], 2)
        self.assertEqual(result["dispatched_count"], 0)
        self.assertTrue(all(r["status"] == "blocked" for r in result["results"]))
        center.manus.execute.assert_not_awaited()

    async def test_cancelled_child_is_an_explicit_failure_record(self):
        center = CommandCenter()
        center.zencode.analyze = AsyncMock(side_effect=asyncio.CancelledError())
        result = await center.fury_deploy([{"agent": "zencode", "target": "fixture"}])
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["results_count"], 1)
        self.assertEqual(result["results"][0]["error_type"], "CancelledError")
        self.assertIsNone(result["results"][0]["executed"])

    async def test_returned_task_id_mismatch_is_failed_and_preserved(self):
        center = CommandCenter()
        raw = {"status": "success", "task_id": "wrong-id"}
        center.manus.execute = AsyncMock(return_value=raw)
        result = await center.fury_deploy([
            {"id": "requested-id", "agent": "manus", "action": "system_audit", "target": "fixture"}])
        record = result["results"][0]
        self.assertEqual(record["task_id"], "requested-id")
        self.assertEqual(record["status"], "failed")
        self.assertEqual(record["error_type"], "invalid_result")
        self.assertEqual(record["result"], raw)

    async def test_invalid_batch_container_is_blocked(self):
        center = CommandCenter()
        center.manus.execute = AsyncMock()
        for tasks in (None, "tasks", {"agent": "manus"}):
            with self.subTest(tasks=tasks):
                result = await center.fury_deploy(tasks)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["results_count"], 0)
                self.assertEqual(result["dispatched_count"], 0)
        center.manus.execute.assert_not_awaited()

    async def test_unserializable_or_unbounded_handler_output_has_safe_failure_record(self):
        circular = {"status": "success"}
        circular["self"] = circular
        bad_outputs = [object(), {"status": "success", "payload": set()},
                       {"status": "success", "callback": lambda: None},
                       {"status": "success", "number": float("nan")},
                       {"status": "success", "number": float("inf")}, circular,
                       {"status": "success", "payload": "x" * 1048577}]
        for raw in bad_outputs:
            with self.subTest(result_type=type(raw).__name__):
                center = CommandCenter()
                center.vibecoder.vibe_create = AsyncMock(return_value=raw)
                result = await center.fury_deploy([{"agent": "vibecoder", "description": "fixture"}])
                self.assertEqual(result["status"], "failed")
                record = result["results"][0]
                self.assertEqual(record["error_type"], "invalid_result")
                self.assertEqual(record["result_type"], type(raw).__name__)
                self.assertNotIn("result", record)
                json.dumps(result, allow_nan=False)

    async def test_invalid_json_input_is_blocked_without_losing_its_index(self):
        center = CommandCenter()
        center.manus.execute = AsyncMock()
        tasks = [{"id": "m1", "agent": "manus", "action": "system_audit",
                  "target": "fixture", "params": {"object": object()}},
                 {"agent": "vibecoder", "description": "valid fixture"}]
        result = await center.fury_deploy(tasks)
        self.assertEqual(result["results_count"], 2)
        self.assertEqual(result["results"][0]["index"], 0)
        self.assertEqual(result["results"][0]["status"], "blocked")
        self.assertEqual(result["results"][0]["input_type"], "dict")
        self.assertIsNone(result["results"][0]["input"])
        self.assertEqual(result["results"][1]["input"], tasks[1])
        center.manus.execute.assert_not_awaited()
        json.dumps(result, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
