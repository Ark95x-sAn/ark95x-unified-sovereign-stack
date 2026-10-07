"""Independent adversarial review of the command outcome boundary.

These fixtures run local Python objects only.  They do not contact a service,
invoke a model, scan a target, or establish physical Windows verification.
Run with: python -m unittest discover -s tests -p 'test_command_review_outcomes.py' -v
"""

import asyncio
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from command.protocol_router import (
    AgentCard,
    MessagePriority,
    ProtocolMessage,
    ProtocolRouter,
    ProtocolType,
    create_default_router,
)
from command.unified_crew import AgentRole, BaseAgent, CrewTask, UnifiedCrew


LONG_INPUT = (
    "Preserve the whole instruction: "
    + "detail " * 60
    + "\nDO NOT send, delete, deploy, or alter authority.\n"
    + "Unicode: — → é Ω; literal shell text: $(not_a_command) `literal`."
)


class SyncOutcomeReview(unittest.TestCase):
    def test_default_roles_keep_input_and_never_claim_execution(self):
        crew = UnifiedCrew(fury=False)
        for role in (AgentRole.MANUS, AgentRole.ZENCODE, AgentRole.VIBECODER):
            with self.subTest(role=role):
                metadata = {"constraints": ["draft only"], "source": {"text": LONG_INPUT}}
                expected = copy.deepcopy(metadata)
                task = CrewTask(f"review-{role.value}", LONG_INPUT, role, metadata=metadata)
                result = crew.conductor.dispatch(task)
                self.assertIsInstance(result, str)
                self.assertEqual(task.status, "not_implemented")
                self.assertIs(task.executed, False)
                self.assertIs(task.verified, False)
                self.assertEqual(task.description, LONG_INPUT)
                self.assertEqual(task.metadata, expected)
                self.assertEqual(metadata, expected)

    def test_custom_agent_cannot_promote_its_own_result_to_verified(self):
        class SelfPromotingAgent(BaseAgent):
            def execute(self, task):
                task.status = "done"
                task.executed = True
                task.verified = True
                return "Fixture handler reports a local result."

        crew = UnifiedCrew(fury=False)
        crew.conductor.register(SelfPromotingAgent(AgentRole.MANUS, crew.memory))
        task = CrewTask("claim-only", LONG_INPUT, AgentRole.MANUS)
        result = crew.conductor.dispatch(task)
        self.assertIsInstance(result, str)
        self.assertEqual(task.status, "reported")
        self.assertIs(task.verified, False)

    def test_exception_cannot_leave_a_previous_success_state(self):
        class BrokenAgent(BaseAgent):
            def execute(self, task):
                task.status = "done"
                task.verified = True
                raise RuntimeError("fixture failed after self-asserting completion")

        crew = UnifiedCrew(fury=False)
        crew.conductor.register(BrokenAgent(AgentRole.MANUS, crew.memory))
        task = CrewTask("failed-claim", LONG_INPUT, AgentRole.MANUS)
        result = crew.conductor.dispatch(task)
        self.assertIsInstance(result, str)
        self.assertEqual(task.status, "failed")
        self.assertIs(task.verified, False)
        self.assertIn("fixture failed", result)

    def test_unregistered_role_receives_a_blocked_outcome(self):
        crew = UnifiedCrew(fury=False)
        task = CrewTask("unroutable", LONG_INPUT, "unregistered-role")
        result = crew.conductor.dispatch(task)
        self.assertIsInstance(result, str)
        self.assertEqual(task.status, "blocked")
        self.assertIs(task.executed, False)
        self.assertIs(task.verified, False)

    def test_batched_dispatch_has_one_audit_and_hook_per_request(self):
        from command.dispatcher import DispatchRequest, Dispatcher

        crew = UnifiedCrew(fury=False)
        dispatcher = Dispatcher(crew=crew, fury=False)
        seen = []
        dispatcher.add_hook(lambda task, result: seen.append((task.task_id, task.status)))
        requests = [
            DispatchRequest(LONG_INPUT, "research", priority=1, task_id="last"),
            DispatchRequest(LONG_INPUT, "unknown-category", priority=9, task_id="first"),
            DispatchRequest(LONG_INPUT, "ui", priority=5, task_id="middle"),
        ]
        results = dispatcher.batch_route(requests)
        self.assertEqual(len(results), len(requests))
        self.assertEqual([item[0] for item in seen], ["first", "middle", "last"])
        self.assertEqual(len(dispatcher.history), len(requests))
        self.assertEqual(dispatcher.summary()["total_dispatched"], len(requests))
        self.assertEqual(dispatcher.history[0]["status"], "blocked")
        self.assertEqual({row["task_id"] for row in dispatcher.history}, {r.task_id for r in requests})

    def test_worker_mutation_cannot_rewrite_caller_input_or_outcome_identity(self):
        from command.dispatcher import DispatchRequest, Dispatcher

        class MutatingWorker(BaseAgent):
            def execute(self, task):
                task.task_id = "forged-task"
                task.assigned_to = "forged-role"
                task.description = "truncated by worker"
                task.metadata["nested"]["instruction"] = "worker mutation"
                task.status = "done"
                task.verified = True
                return LONG_INPUT

        crew = UnifiedCrew(fury=False)
        crew.conductor.register(MutatingWorker(AgentRole.MANUS, crew.memory))
        dispatcher = Dispatcher(crew=crew, fury=False)
        request = DispatchRequest(
            LONG_INPUT, "research", task_id="source-task",
            metadata={"nested": {"instruction": LONG_INPUT}},
        )
        expected = copy.deepcopy(request)
        self.assertEqual(dispatcher.route(request), LONG_INPUT)
        self.assertEqual(request, expected)
        row = dispatcher.history[0]
        self.assertEqual(row["task_id"], "source-task")
        self.assertEqual(row["agent"], "manus")
        self.assertEqual(row["status"], "reported")
        self.assertIs(row["verified"], False)
        self.assertEqual(row["result"], LONG_INPUT)
        self.assertEqual(row["input"]["description"], LONG_INPUT)
        self.assertEqual(row["input"]["metadata"], expected.metadata)
        request.metadata["nested"]["instruction"] = "caller mutation after return"
        self.assertEqual(row["input"]["metadata"], expected.metadata)

    def test_broken_hook_is_recorded_and_other_hooks_and_requests_continue(self):
        from command.dispatcher import DispatchRequest, Dispatcher

        dispatcher = Dispatcher(crew=UnifiedCrew(fury=False), fury=False)
        seen = []

        def broken_hook(task, result):
            task.status = "done"
            task.verified = True
            raise RuntimeError("fixture audit sink unavailable")

        def observer_hook(task, result):
            seen.append((task.task_id, task.status, task.verified))

        dispatcher.add_hook(broken_hook)
        dispatcher.add_hook(observer_hook)
        results = dispatcher.batch_route([
            DispatchRequest(LONG_INPUT, "research", task_id="first"),
            DispatchRequest(LONG_INPUT, "ui", task_id="second"),
        ])
        self.assertEqual(len(results), 2)
        self.assertEqual(seen, [("first", "not_implemented", False), ("second", "not_implemented", False)])
        self.assertEqual(len(dispatcher.history), 2)
        self.assertEqual(dispatcher.summary()["hook_errors"], 2)
        for row in dispatcher.history:
            self.assertEqual(row["status"], "not_implemented")
            self.assertIs(row["verified"], False)
            self.assertEqual(row["hook_errors"], [{
                "hook_index": 0,
                "error_type": "RuntimeError",
                "error": "fixture audit sink unavailable",
            }])

    def test_custom_failed_status_cannot_assert_execution_or_verification(self):
        class ContradictoryWorker(BaseAgent):
            def execute(self, task):
                task.status = "failed"
                task.executed = True
                task.verified = True
                return "Worker claims both failure and verified execution."

        crew = UnifiedCrew(fury=False)
        crew.conductor.register(ContradictoryWorker(AgentRole.MANUS, crew.memory))
        task = CrewTask("contradictory", LONG_INPUT, AgentRole.MANUS)
        crew.conductor.dispatch(task)
        self.assertEqual(task.status, "failed")
        self.assertIsNone(task.executed)
        self.assertIs(task.verified, False)

    def test_launcher_reports_unimplemented_work_and_nonzero_exit(self):
        root = Path(__file__).resolve().parents[1]
        forms = [
            ["-m", "command.run_crew"],
            [str(root / "command" / "run_crew.py")],
        ]
        for form in forms:
            with self.subTest(form=form):
                result = subprocess.run(
                    [sys.executable, *form, "--mode", "quick", "--quiet"],
                    cwd=root,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
                output = result.stdout.lower()
                self.assertIn("not_implemented", output)
                self.assertNotIn("mission complete", output)
                self.assertNotIn("all tasks complete", output)
                self.assertNotIn("stack live", output)


class ProtocolOutcomeReview(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def message(protocol=ProtocolType.MCP, payload=None):
        return ProtocolMessage(
            protocol=protocol,
            sender="fixture-sender",
            recipient="fixture-recipient",
            action="fixture_action",
            payload={"instruction": LONG_INPUT} if payload is None else payload,
            correlation_id="original-correlation",
            priority=MessagePriority.HIGH,
            ttl_seconds=900,
        )

    async def test_catalogued_endpoints_are_never_delivery_receipts(self):
        router = create_default_router()
        for protocol in ProtocolType:
            with self.subTest(protocol=protocol):
                message = self.message(protocol)
                message.recipient = "manus"
                result = await router.route(message)
                self.assertEqual(result["status"], "not_implemented")
                self.assertIs(result["delivered"], False)
                self.assertIs(result["transport_verified"], False)
                self.assertEqual(result["correlation_id"], "original-correlation")

    async def test_handler_claims_stay_nested_and_cannot_rewrite_identity(self):
        router = ProtocolRouter()
        payload = {"instruction": LONG_INPUT, "nested": {"unchanged": True}}
        expected_payload = copy.deepcopy(payload)
        message = self.message(payload=payload)

        async def claiming_handler(handler_payload):
            handler_payload["nested"]["unchanged"] = False
            message.sender = "mutated-sender"
            message.recipient = "mutated-recipient"
            message.correlation_id = "mutated-correlation"
            return {
                "status": "success",
                "delivered": True,
                "transport_verified": True,
                "recipient": "forged-recipient",
                "correlation_id": "forged-correlation",
                "output": "fixture output",
            }

        router.register_handler("fixture_action", claiming_handler)
        result = await router.route(message)
        self.assertEqual(result["status"], "local_handler_returned")
        self.assertEqual(result["sender"], "fixture-sender")
        self.assertEqual(result["recipient"], "fixture-recipient")
        self.assertEqual(result["correlation_id"], "original-correlation")
        self.assertIs(result["delivered"], False)
        self.assertIs(result["transport_verified"], False)
        self.assertEqual(result["handler_result"]["recipient"], "forged-recipient")
        self.assertEqual(payload, expected_payload)
        historical_log = copy.deepcopy(router.message_log)
        result["handler_result"]["output"] = "caller rewrote returned object"
        result["recipient"] = "caller forgery"
        self.assertEqual(router.message_log, historical_log)

    async def test_failure_indicators_override_a_success_label(self):
        cases = [
            {"status": "failed"},
            {"status": "cancelled"},
            {"status": "blocked"},
            {"status": "not_implemented"},
            {"status": "success", "success": False},
            {"status": "success", "isError": True},
            {"status": "success", "error": "fixture rejected work"},
        ]
        for response in cases:
            with self.subTest(response=response):
                router = ProtocolRouter()

                async def handler(_):
                    return response

                router.register_handler("fixture_action", handler)
                result = await router.route(self.message())
                self.assertEqual(result["status"], "error")
                self.assertEqual(result["handler_result"], response)
                self.assertIs(result["delivered"], False)
                self.assertIs(result["transport_verified"], False)

    async def test_malformed_or_non_json_handler_returns_are_not_success(self):
        responses = [
            None,
            True,
            ["completed"],
            "completed",
            {"status": []},
            {"status": "success", "success": "false"},
            {"status": "success", "isError": "false"},
            {"status": "success", "not_json": {"a", "b"}},
            {"status": "success", "not_json": float("nan")},
        ]
        for response in responses:
            with self.subTest(response=repr(response)):
                router = ProtocolRouter()

                async def handler(_):
                    return response

                router.register_handler("fixture_action", handler)
                result = await router.route(self.message())
                self.assertEqual(result["status"], "error")
                self.assertIs(result["delivered"], False)
                self.assertIs(result["transport_verified"], False)

    async def test_broadcast_preserves_envelope_and_isolates_recipient_payloads(self):
        router = ProtocolRouter()
        for name in ("first", "second"):
            router.register_agent(AgentCard(name, name, "local fixture", [], ["mcp"], "fixture://unused"))
        payloads = []
        envelopes = []
        original_route = router.route

        async def observe_route(message):
            envelopes.append(copy.deepcopy(message))
            return await original_route(message)

        async def handler(payload):
            payloads.append(copy.deepcopy(payload))
            payload["nested"]["sequence"].append("handler mutation")
            return {"status": "success"}

        router.route = observe_route
        router.register_handler("fixture_action", handler)
        message = self.message(payload={"instruction": LONG_INPUT, "nested": {"sequence": [1]}})
        expected_payload = copy.deepcopy(message.payload)
        results = await router.broadcast(message)
        self.assertEqual(len(results), 2)
        self.assertEqual(payloads, [expected_payload, expected_payload])
        self.assertEqual(message.payload, expected_payload)
        self.assertEqual([row.recipient for row in envelopes], ["first", "second"])
        for row in envelopes:
            self.assertEqual(row.timestamp, message.timestamp)
            self.assertEqual(row.correlation_id, message.correlation_id)
            self.assertEqual(row.ttl_seconds, message.ttl_seconds)
            self.assertEqual(row.priority, message.priority)

    async def test_cancelled_handler_propagates_and_leaves_an_explicit_record(self):
        router = ProtocolRouter()
        started = asyncio.Event()
        cleanup = []

        async def handler(_):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cleanup.append("handler stopped")

        router.register_handler("fixture_action", handler)
        operation = asyncio.create_task(router.route(self.message()))
        await asyncio.wait_for(started.wait(), timeout=1)
        operation.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await operation
        self.assertEqual(cleanup, ["handler stopped"])
        self.assertIn("cancelled", json.dumps(router.message_log).lower())


class AsyncAgentOutcomeReview(unittest.IsolatedAsyncioTestCase):
    async def test_all_default_manus_actions_leave_completion_metrics_zero(self):
        from command.agents import ManusAgent, ManusTask

        agent = ManusAgent()
        for action in agent.SKILLS:
            with self.subTest(action=action):
                params = {"instruction": LONG_INPUT, "nested": {"draft_only": True}}
                expected = copy.deepcopy(params)
                task = ManusTask(f"review-{action}", action, "fixture://unused", params)
                result = await agent.execute(task)
                self.assertEqual(result["status"], "not_implemented")
                self.assertIs(result["executed"], False)
                self.assertIs(result["verified"], False)
                self.assertEqual(params, expected)
        self.assertEqual(agent.metrics["tasks_completed"], 0)
        self.assertEqual(agent.completed, [])
        self.assertEqual(agent.active_tasks, {})

    async def test_manus_self_asserted_completion_is_only_reported(self):
        from command.agents import ManusAgent, ManusTask

        agent = ManusAgent()

        async def claiming_handler(task):
            task.task_id = "worker-changed-id"
            return {"status": "completed", "verified": True, "executed": True, "task_id": "forged"}

        agent._skill_audit = claiming_handler
        task = ManusTask("original-task-id", "system_audit", LONG_INPUT, {})
        result = await agent.execute(task)
        self.assertEqual(result["task_id"], "original-task-id")
        self.assertEqual(result["status"], "reported")
        self.assertIs(result["verified"], False)
        self.assertEqual(agent.active_tasks, {})
        self.assertEqual(agent.metrics["tasks_completed"], 0)

    async def test_manus_handler_exception_is_not_retried_as_another_action(self):
        from command.agents import ManusAgent, ManusTask

        agent = ManusAgent()
        calls = []

        async def failing_handler(task):
            calls.append(task.task_id)
            raise RuntimeError("fixture side effect may already have occurred")

        agent._skill_audit = failing_handler
        task = ManusTask("once-only", "system_audit", LONG_INPUT, {})
        result = await agent.execute(task)
        self.assertEqual(result["status"], "failed")
        self.assertIs(result["verified"], False)
        self.assertEqual(calls, ["once-only"])
        self.assertEqual(agent.metrics["tasks_completed"], 0)
        self.assertEqual(agent.active_tasks, {})

    async def test_cancelled_manus_handler_cleans_up_original_identity(self):
        from command.agents import ManusAgent, ManusTask

        agent = ManusAgent()
        entered = asyncio.Event()

        async def waiting_handler(task):
            task.task_id = "worker-mutated-id"
            entered.set()
            await asyncio.Event().wait()

        agent._skill_audit = waiting_handler
        task = ManusTask("cancel-original", "system_audit", LONG_INPUT, {})
        operation = asyncio.create_task(agent.execute(task))
        await asyncio.wait_for(entered.wait(), timeout=1)
        operation.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await operation
        self.assertEqual(task.status, "cancelled")
        self.assertEqual(agent.active_tasks, {})
        self.assertEqual(agent.metrics["tasks_completed"], 0)

    async def test_mixed_batch_preserves_each_input_and_refuses_forged_identity(self):
        from command.agents import CommandCenter

        center = CommandCenter()
        dispatched = []

        async def manus_execute(task):
            dispatched.append("manus")
            task.params["nested"]["instruction"] = "handler mutation"
            return {"status": "completed", "task_id": "forged-id", "verified": True, "executed": True}

        async def zencode_analyze(target, analysis_type="full"):
            dispatched.append("zencode")
            raise ValueError("fixture analysis failed")

        async def vibe_create(description):
            dispatched.append("vibecoder")
            self.assertEqual(description, LONG_INPUT)
            return {"status": "success", "verified": True}

        center.manus.execute = manus_execute
        center.zencode.analyze = zencode_analyze
        center.vibecoder.vibe_create = vibe_create
        tasks = [
            {"id": "vibe-first", "agent": "vibecoder", "description": LONG_INPUT},
            {"id": "unknown", "agent": "does-not-exist", "description": LONG_INPUT},
            42,
            {"id": "manus-middle", "agent": "manus", "action": "system_audit", "target": "fixture://unused", "params": {"nested": {"instruction": LONG_INPUT}}},
            {"id": "zen-last", "agent": "zencode", "target": LONG_INPUT},
        ]
        expected = copy.deepcopy(tasks)
        batch = await center.fury_deploy(tasks)
        self.assertEqual(batch["status"], "partial")
        self.assertEqual(len(batch["results"]), len(tasks))
        self.assertEqual([row["index"] for row in batch["results"]], list(range(len(tasks))))
        self.assertEqual([row["input"] for row in batch["results"]], expected)
        self.assertEqual([row["status"] for row in batch["results"]], ["reported", "blocked", "blocked", "failed", "failed"])
        self.assertEqual(batch["results"][3]["task_id"], "manus-middle")
        self.assertTrue(all(row["verified"] is False for row in batch["results"]))
        self.assertEqual(tasks, expected)
        self.assertCountEqual(dispatched, ["vibecoder", "manus", "zencode"])
        tasks[3]["params"]["nested"]["instruction"] = "caller mutated after return"
        self.assertEqual(batch["results"][3]["input"], expected[3])

    async def test_contradictory_success_flags_cannot_produce_reported_success(self):
        from command.agents import ManusAgent, ManusTask

        for response in (
            {"status": "success", "success": False},
            {"status": "success", "isError": True},
        ):
            with self.subTest(response=response):
                agent = ManusAgent()

                async def contradictory_handler(task):
                    return response

                agent._skill_audit = contradictory_handler
                result = await agent.execute(ManusTask("contradictory", "system_audit", LONG_INPUT, {}))
                self.assertEqual(result["status"], "failed")
                self.assertIs(result["verified"], False)
                self.assertEqual(agent.metrics["tasks_completed"], 0)

    async def test_handler_cannot_mutate_a_retained_report_after_return(self):
        from command.agents import ManusAgent, ManusTask

        agent = ManusAgent()
        handler_output = {"status": "success", "details": {"source": LONG_INPUT}}

        async def local_handler(task):
            return handler_output

        agent._skill_audit = local_handler
        result = await agent.execute(ManusTask("result-copy", "system_audit", LONG_INPUT, {}))
        expected = copy.deepcopy(result)
        handler_output["status"] = "failed"
        handler_output["details"]["source"] = "mutated after return"
        self.assertEqual(result, expected)
        self.assertEqual(result["status"], "reported")
        self.assertIs(result["verified"], False)

    async def test_non_json_handler_results_produce_serializable_failure_receipts(self):
        from command.agents import CommandCenter, ManusAgent, ManusTask

        cyclic = {"status": "success"}
        cyclic["loop"] = cyclic
        responses = [
            {"status": "success", "payload": {"a", "b"}},
            {"status": "success", "payload": float("nan")},
            cyclic,
        ]
        for index, response in enumerate(responses):
            with self.subTest(index=index):
                agent = ManusAgent()

                async def invalid_handler(task):
                    return response

                agent._skill_audit = invalid_handler
                result = await agent.execute(ManusTask("invalid-json", "system_audit", LONG_INPUT, {}))
                self.assertEqual(result["status"], "failed")
                self.assertIs(result["verified"], False)
                json.dumps(result, allow_nan=False)

                # Identity rejection must pass through the same serialization
                # boundary rather than embedding an unchecked raw result.
                center = CommandCenter()

                async def forged_invalid_handler(task):
                    return {**response, "task_id": "forged-identity"}

                center.manus.execute = forged_invalid_handler
                batch = await center.fury_deploy([
                    {"id": "original-identity", "agent": "manus",
                     "action": "system_audit", "target": "fixture://unused"},
                ])
                self.assertEqual(batch["status"], "failed")
                self.assertEqual(batch["results"][0]["task_id"], "original-identity")
                json.dumps(batch, allow_nan=False)

    async def test_cancelled_child_is_retained_in_its_original_batch_position(self):
        from command.agents import CommandCenter

        center = CommandCenter()

        async def self_cancelled(target, analysis_type="full"):
            raise asyncio.CancelledError("fixture cancelled itself")

        center.zencode.analyze = self_cancelled
        tasks = [{"id": "cancelled-child", "agent": "zencode", "target": LONG_INPUT}]
        batch = await center.fury_deploy(tasks)
        self.assertEqual(batch["status"], "failed")
        self.assertEqual(len(batch["results"]), 1)
        self.assertEqual(batch["results"][0]["task_id"], "cancelled-child")
        self.assertEqual(batch["results"][0]["status"], "failed")
        self.assertIs(batch["results"][0]["verified"], False)
        json.dumps(batch, allow_nan=False)

    async def test_parent_cancellation_propagates_and_waiting_children_stop(self):
        from command.agents import CommandCenter

        center = CommandCenter()
        entered = asyncio.Event()
        cleanup = []

        async def waiting_analyze(target, analysis_type="full"):
            entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                cleanup.append("zencode stopped")

        center.zencode.analyze = waiting_analyze
        operation = asyncio.create_task(center.fury_deploy([
            {"id": "parent-cancel", "agent": "zencode", "target": LONG_INPUT},
        ]))
        await asyncio.wait_for(entered.wait(), timeout=1)
        operation.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await operation
        self.assertEqual(cleanup, ["zencode stopped"])
        self.assertFalse(any(task is not asyncio.current_task() and not task.done() for task in asyncio.all_tasks()))


if __name__ == "__main__":
    unittest.main()
