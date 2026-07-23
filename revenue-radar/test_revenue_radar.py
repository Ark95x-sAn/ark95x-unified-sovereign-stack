import tempfile
import unittest
from pathlib import Path

import revenue_radar as app


BASE = {
    "first_name": "  Alex  ",
    "last_name": "Rivera",
    "company": "Example Holdings",
    "email": " ALEX@EXAMPLE.COM ",
    "phone": "(641) 555-0101",
    "opportunity_type": "real_estate",
    "property_address": "101 Main Street",
    "source": "referral",
    "estimated_value": "25000",
    "urgency_days": "7",
    "notes": "Interested in a property review.",
}


class RevenueRadarTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        app.DB_PATH = Path(self.tmp.name) / "test.db"
        app.DRY_RUN = True
        app.USE_OLLAMA = False
        app.SEND_WEBHOOK_URL = ""
        app.init_db()

    def tearDown(self):
        self.tmp.cleanup()

    def count(self, table):
        with app.db_connect() as conn:
            return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    def test_capture_cleans_scores_and_drafts(self):
        item, duplicate = app.capture_opportunity(dict(BASE))
        self.assertFalse(duplicate)
        self.assertEqual(item["normalized_email"], "alex@example.com")
        self.assertEqual(item["normalized_phone"], "6415550101")
        self.assertEqual(item["status"], "drafted")
        self.assertGreaterEqual(item["score"], 80)
        self.assertTrue(item["draft_subject"])
        self.assertTrue(item["score_reasons"])

    def test_exact_duplicate_is_merged_idempotently(self):
        first, _ = app.capture_opportunity(dict(BASE))
        changed = dict(BASE, notes="Second confirmed detail", estimated_value="30000")
        second, duplicate = app.capture_opportunity(changed)
        self.assertTrue(duplicate)
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(self.count("opportunities"), 1)
        self.assertIn("Second confirmed detail", second["notes"])
        self.assertEqual(second["estimated_value"], 30000)

    def test_same_contact_different_opportunity_is_flagged_not_merged(self):
        first, _ = app.capture_opportunity(dict(BASE))
        other = dict(BASE, opportunity_type="grant_service", property_address="Grant 2026")
        second, duplicate = app.capture_opportunity(other)
        self.assertFalse(duplicate)
        self.assertEqual(second["duplicate_of"], first["id"])
        self.assertEqual(self.count("opportunities"), 2)

    def test_send_fails_closed_without_approval(self):
        item, _ = app.capture_opportunity(dict(BASE))
        with self.assertRaises(PermissionError):
            app.send_opportunity(item["id"])

    def test_approval_is_bound_to_exact_draft(self):
        item, _ = app.capture_opportunity(dict(BASE))
        app.approve_opportunity(item["id"])
        with app.db_connect() as conn:
            conn.execute("UPDATE opportunities SET draft_body = 'changed later' WHERE id = ?", (item["id"],))
        with self.assertRaises(PermissionError):
            app.send_opportunity(item["id"])

    def test_dry_run_never_marks_sent_and_is_idempotent(self):
        item, _ = app.capture_opportunity(dict(BASE))
        app.approve_opportunity(item["id"])
        first = app.send_opportunity(item["id"])
        second = app.send_opportunity(item["id"])
        self.assertEqual(first["status"], "simulated")
        self.assertIsNone(first["sent_at"])
        self.assertEqual(second["status"], "simulated")
        with app.db_connect() as conn:
            simulated = conn.execute(
                "SELECT COUNT(*) FROM audit_log WHERE event_type='send_simulated'"
            ).fetchone()[0]
        self.assertEqual(simulated, 1)

    def test_outcome_requires_send_step(self):
        item, _ = app.capture_opportunity(dict(BASE))
        app.approve_opportunity(item["id"])
        with self.assertRaises(PermissionError):
            app.log_outcome(item["id"], {"outcome": "won", "outcome_value": 1000})
        app.send_opportunity(item["id"])
        result = app.log_outcome(item["id"], {"outcome": "won", "outcome_value": 1000})
        self.assertEqual(result["status"], "won")
        self.assertEqual(result["outcome_value"], 1000)

    def test_score_is_deterministic(self):
        cleaned = app.clean_record(dict(BASE))
        self.assertEqual(app.score_record(cleaned), app.score_record(cleaned))

    def test_invalid_contact_is_rejected(self):
        bad = dict(BASE, email="not-an-email", phone="")
        with self.assertRaises(ValueError):
            app.capture_opportunity(bad)


if __name__ == "__main__":
    unittest.main()
