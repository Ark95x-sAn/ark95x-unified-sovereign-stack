"""Handoff privacy/authority regressions; the Core compatibility run is separate."""
import hashlib
import tempfile
from pathlib import Path
import unittest

from n95_native.bridge import canonical, init_state
from n95_native.core_handoff import prepare


class CoreHandoffTests(unittest.TestCase):
    def test_empty_transport_state_does_not_claim_deployment_or_execute(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / "state"
            init_state(state)
            packet = prepare(state)
            self.assertEqual(packet["status"], "PREPARED_NOT_SUBMITTED")
            self.assertFalse(packet["observation"]["physical_deployment_verified"])
            self.assertFalse(packet["observation"]["execution_authority_granted"])
            self.assertEqual(packet["mission"]["mode"], "draft")
            self.assertEqual(packet["observation"]["evidence_coverage"]["verified_checks"], 0)
            self.assertTrue(all(not node["online"] for node in packet["observation"]["nodes"].values()))

    def test_draft_binds_source_and_does_not_include_credentials(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / "state"
            init_state(state)
            packet = prepare(state)
            encoded = canonical(packet)
            digest = hashlib.sha256(canonical(packet["observation"]).encode()).hexdigest()
            self.assertEqual(digest, packet["source_sha256"])
            self.assertIn("observation_sha256=" + digest, packet["mission"]["constraints"])
            for key in state.rglob("*.key"):
                self.assertNotIn(key.read_text().strip(), encoded)
            self.assertIn("historical", packet["observation"]["validity"])
            self.assertIsInstance(packet["observation"]["observed_at"], (float, int))


if __name__ == "__main__":
    unittest.main()
