import json
import unittest
from pathlib import Path


POLICY_PATH = Path(__file__).with_name("control_plane_policy.json")


class ControlPlanePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    def test_dry_run_is_default(self):
        self.assertEqual(self.policy["default_mode"], "dry_run")

    def test_all_protocols_are_unique_and_versioned(self):
        protocols = self.policy["protocols"]
        self.assertEqual(len(protocols), 10)
        self.assertEqual(len(protocols), len(set(protocols)))
        self.assertTrue(self.policy["version"])

    def test_agent_cannot_self_approve(self):
        self.assertFalse(self.policy["approval"]["agent_self_approval"])
        self.assertTrue(self.policy["approval"]["invalidate_on_payload_change"])

    def test_handoff_fails_closed(self):
        handoff = self.policy["external_handoff"]
        self.assertTrue(handoff["requires_approval_hash_match"])
        self.assertTrue(handoff["requires_idempotency_key"])
        self.assertFalse(handoff["webhook_acceptance_equals_delivery"])
        self.assertEqual(handoff["automatic_retry_limit"], 0)
        self.assertEqual(handoff["ambiguous_state"], "RECONCILE")

    def test_fabrication_is_stop_condition(self):
        self.assertEqual(self.policy["evidence"]["fabrication_policy"], "STOP")
        self.assertIn("FABRICATED_INFORMATION", self.policy["stop_conditions"])

    def test_local_calibration_gate(self):
        gate = self.policy["phase_gates"]["local_calibration"]
        self.assertGreaterEqual(gate["gold_set_cases_min"], 25)
        self.assertGreaterEqual(gate["required_field_completeness_min"], 0.95)
        self.assertGreaterEqual(gate["correct_routing_min"], 0.9)
        self.assertEqual(gate["unauthorized_actions_max"], 0)


if __name__ == "__main__":
    unittest.main()
