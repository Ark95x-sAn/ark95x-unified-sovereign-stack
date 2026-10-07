"""Local protocol outcomes; no transport, optional dependencies, or live calls."""
import asyncio
import unittest
from unittest.mock import AsyncMock

from command.protocol_router import (
    AgentCard, MessagePriority, ProtocolMessage, ProtocolRouter, ProtocolType,
)


class ProtocolOutcomeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.router = ProtocolRouter()

    def message(self, protocol=ProtocolType.MCP, **overrides):
        fields = {
            "protocol": protocol, "sender": "fixture-controller",
            "recipient": "fixture-worker", "action": "inspect",
            "payload": {"fixture": "input"}, "correlation_id": "attempt-17",
        }
        fields.update(overrides)
        return ProtocolMessage(**fields)

    def register_agent(self, agent_id="fixture-worker"):
        self.router.register_agent(AgentCard(
            agent_id=agent_id, name=agent_id, description="Synthetic card only",
            skills=["inspect"], protocols=["mcp", "a2a", "acp"],
            endpoint=f"https://invalid.example/{agent_id}",
        ))

    def assert_no_delivery(self, result, message):
        self.assertIs(result["delivered"], False)
        self.assertIs(result["transport_verified"], False)
        self.assertNotEqual(result["status"], "delivered")
        for key in ("sender", "recipient", "action", "correlation_id"):
            self.assertEqual(result[key], getattr(message, key))
        entry = self.router.message_log[-1]
        for key in ("sender", "recipient", "action", "correlation_id", "status",
                    "delivered", "transport_verified"):
            self.assertEqual(entry[key], result[key])
        self.assertIn("finished_at", entry)

    async def test_unimplemented_protocols_are_failures_even_with_a_known_agent(self):
        self.register_agent()
        for protocol in ProtocolType:
            with self.subTest(protocol=protocol):
                message = self.message(protocol)
                result = await self.router.route(message)
                self.assertEqual(result["status"], "not_implemented")
                self.assertEqual(result["evidence_scope"], "none")
                self.assert_no_delivery(result, message)
        self.assertEqual(self.router.metrics["messages_routed"], 3)
        self.assertEqual(self.router.metrics["errors"], 3)
        self.assertEqual(self.router.metrics["local_handler_returns"], 0)
        self.assertEqual(self.router.metrics["by_protocol"], {"mcp": 1, "a2a": 1, "acp": 1})

    async def test_unknown_a2a_agent_retains_failure_and_identity(self):
        message = self.message(ProtocolType.A2A)
        result = await self.router.route(message)
        self.assertEqual(result["status"], "agent_not_found")
        self.assert_no_delivery(result, message)
        self.assertEqual(self.router.metrics["errors"], 1)

    async def test_registered_handler_returns_local_output_without_promoting_its_claims(self):
        reported = {
            "status": "delivered", "delivered": True, "transport_verified": True,
            "recipient": "wrong-recipient", "correlation_id": "wrong-attempt",
            "value": [1, 2, 3],
        }
        handler = AsyncMock(return_value=reported)
        self.router.register_handler("inspect", handler)
        message = self.message()
        result = await self.router.route(message)
        handler.assert_awaited_once_with(message.payload)
        self.assertEqual(result["status"], "local_handler_returned")
        self.assertEqual(result["evidence_scope"], "local_handler")
        self.assertEqual(result["handler_result"], reported)
        self.assert_no_delivery(result, message)
        self.assertEqual(self.router.metrics["errors"], 0)
        self.assertEqual(self.router.metrics["local_handler_returns"], 1)
        # Neither caller nor handler can change the retained outcome afterward.
        reported["value"].append(4)
        result["handler_result"]["value"].append(5)
        result["recipient"] = "rewritten"
        self.assertEqual(self.router.message_log[-1]["handler_result"]["value"], [1, 2, 3])
        self.assertEqual(self.router.message_log[-1]["recipient"], message.recipient)

    async def test_explicit_handler_failures_are_retained_and_counted(self):
        reports = [
            {"status": "FAILED", "details": "fixture refusal"},
            {"status": "blocked"}, {"status": "unknown"},
            {"success": False}, {"isError": True},
            {"error": {"code": "FIXTURE_ERROR", "detail": "rejected"}},
        ]
        for report in reports:
            with self.subTest(report=report):
                self.router.register_handler("inspect", AsyncMock(return_value=report))
                message = self.message()
                result = await self.router.route(message)
                self.assertEqual(result["status"], "error")
                self.assertEqual(result["handler_result"], report)
                self.assert_no_delivery(result, message)
        self.assertEqual(self.router.metrics["errors"], len(reports))
        self.assertEqual(self.router.metrics["local_handler_returns"], 0)

    async def test_raised_handler_failure_is_not_a_delivery(self):
        self.router.register_handler("inspect", AsyncMock(side_effect=RuntimeError("fixture refusal")))
        message = self.message()
        result = await self.router.route(message)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "fixture refusal")
        self.assertEqual(result["error_type"], "RuntimeError")
        self.assert_no_delivery(result, message)
        self.assertEqual(self.router.metrics["errors"], 1)

    async def test_malformed_handler_results_fail_closed(self):
        cyclic = {}
        cyclic["cycle"] = cyclic
        reports = [
            None, [], "success", 1, True, {"output": {1, 2}},
            {"value": float("nan")}, cyclic, {"status": None},
            {"status": ["success"]}, {"success": "false"}, {"isError": 0},
        ]
        for index, report in enumerate(reports):
            with self.subTest(index=index):
                self.router.register_handler("inspect", AsyncMock(return_value=report))
                message = self.message()
                result = await self.router.route(message)
                self.assertEqual(result["status"], "error")
                self.assert_no_delivery(result, message)
        self.assertEqual(self.router.metrics["errors"], len(reports))

    async def test_malformed_payload_never_invokes_local_handler(self):
        handler = AsyncMock(return_value={"value": "fixture output"})
        self.router.register_handler("inspect", handler)
        message = self.message(payload="not-an-object")
        result = await self.router.route(message)
        self.assertEqual(result["status"], "error")
        handler.assert_not_awaited()
        self.assert_no_delivery(result, message)

    async def test_nonstring_json_object_keys_are_rejected_at_every_depth(self):
        reports = [
            {1: "first", "1": "second"},
            {"nested": {None: "coerced"}},
            {"items": [{"deeper": {False: "coerced"}}]},
            {"items": ({"deeper": {1.5: "coerced"}},)},
        ]
        for index, report in enumerate(reports):
            with self.subTest(index=index):
                self.router.register_handler("inspect", AsyncMock(return_value=report))
                message = self.message()
                result = await self.router.route(message)
                self.assertEqual(result["status"], "error")
                self.assertIn("object keys must be strings", result["error"])
                self.assert_no_delivery(result, message)
        self.assertEqual(self.router.metrics["errors"], len(reports))
        self.assertEqual(self.router.metrics["local_handler_returns"], 0)

    async def test_invalid_protocol_is_an_accounted_failure(self):
        message = self.message(protocol="unsupported")
        result = await self.router.route(message)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["protocol"], "unsupported")
        self.assert_no_delivery(result, message)
        self.assertEqual(self.router.metrics["messages_routed"], 1)
        self.assertEqual(self.router.metrics["errors"], 1)

    async def test_cancellation_propagates_with_correlated_log_and_later_route_usable(self):
        started = asyncio.Event()
        stopped = asyncio.Event()

        async def wait_for_cancel(payload):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                stopped.set()

        self.router.register_handler("inspect", wait_for_cancel)
        message = self.message()
        task = asyncio.create_task(self.router.route(message))
        await asyncio.wait_for(started.wait(), timeout=1)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertTrue(stopped.is_set())
        self.assertEqual(self.router.message_log[-1]["status"], "cancelled")
        self.assert_no_delivery(self.router.message_log[-1], message)
        self.assertEqual(self.router.metrics["cancelled"], 1)
        self.assertEqual(self.router.metrics["errors"], 0)
        self.router.register_handler("inspect", AsyncMock(return_value={"value": "next"}))
        next_result = await self.router.route(self.message(correlation_id="attempt-18"))
        self.assertEqual(next_result["status"], "local_handler_returned")
        self.assertEqual(next_result["correlation_id"], "attempt-18")

    async def test_broadcast_preserves_correlation_ttl_timestamp_and_priority(self):
        self.register_agent("fixture-a")
        self.register_agent("fixture-b")
        message = self.message(
            ProtocolType.A2A, priority=MessagePriority.HIGH,
            timestamp="2026-10-07T00:00:00+00:00", ttl_seconds=7,
        )
        original_route = self.router.route
        attempted = []

        async def record_attempt(candidate):
            attempted.append(candidate)
            return await original_route(candidate)

        self.router.route = record_attempt
        results = await self.router.broadcast(message)
        self.assertEqual([r["recipient"] for r in results], ["fixture-a", "fixture-b"])
        self.assertEqual([m.recipient for m in attempted], ["fixture-a", "fixture-b"])
        for candidate, result, log in zip(attempted, results, self.router.message_log):
            self.assertEqual(result["status"], "not_implemented")
            self.assertIs(result["delivered"], False)
            self.assertIs(result["transport_verified"], False)
            self.assertEqual(log["correlation_id"], message.correlation_id)
            for key in ("sender", "action", "payload", "correlation_id", "timestamp", "ttl_seconds", "priority"):
                self.assertEqual(getattr(candidate, key), getattr(message, key))
        self.assertEqual(self.router.metrics["errors"], 2)

    async def test_handler_mutation_cannot_rewrite_request_identity_or_original_payload(self):
        message = self.message(payload={"values": ["original"]})

        async def mutating_handler(payload):
            payload["values"].append("handler edit")
            message.correlation_id = "attempt-injected"
            message.recipient = "recipient-injected"
            return {"value": payload}

        self.router.register_handler("inspect", mutating_handler)
        result = await self.router.route(message)
        self.assertEqual(message.payload, {"values": ["original"]})
        self.assertEqual(result["recipient"], "fixture-worker")
        self.assertEqual(result["correlation_id"], "attempt-17")
        self.assertEqual(self.router.message_log[-1]["recipient"], "fixture-worker")
        self.assertEqual(self.router.message_log[-1]["correlation_id"], "attempt-17")

    async def test_broadcast_payload_and_context_are_frozen_per_recipient(self):
        self.register_agent("fixture-a")
        self.register_agent("fixture-b")
        message = self.message(payload={"values": ["original"]})
        seen = []

        async def mutating_handler(payload):
            seen.append(list(payload["values"]))
            payload["values"].append("handler edit")
            message.correlation_id = "attempt-injected"
            message.action = "action-injected"
            return {"value": payload}

        self.router.register_handler("inspect", mutating_handler)
        results = await self.router.broadcast(message)
        self.assertEqual(seen, [["original"], ["original"]])
        self.assertEqual(message.payload, {"values": ["original"]})
        for result in results:
            self.assertEqual(result["correlation_id"], "attempt-17")
            self.assertEqual(result["action"], "inspect")
            self.assertEqual(result["status"], "local_handler_returned")


if __name__ == "__main__":
    unittest.main()
