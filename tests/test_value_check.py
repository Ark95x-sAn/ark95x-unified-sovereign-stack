"""Boundary tests for the financial-value claim; fixtures are not customer proof."""
import copy
import unittest

from tools.n95_value_check import EvidenceError, evaluate


def fixture():
    return {
        "price_usd": 100,
        "evidence_kind": "actual_customer_measurements",
        "all_attempts_included": True,
        "same_quality_target": True,
        "customer_acceptance_recorded": True,
        "customer_hourly_value_agreed": True,
        "installation_passed": True,
        "customer_hourly_value_usd": 30,
        "customer_setup_minutes": 30,
        "extra_customer_support_minutes": 0,
        "nonoverlapping_customer_evaluation_minutes": 0,
        "extra_customer_cost_usd": 5,
        "paired_observations": [
            {"job_id": str(i), "best_free_alternative_seconds": 2400,
             "workflow_total_seconds": 600, "comparable": True, "quality_passed": True,
             "measurement_record": "synthetic-test-only"}
            for i in range(10)
        ]
    }


class ValueChecks(unittest.TestCase):
    def test_empty_evidence_never_passes(self):
        result = evaluate({})
        self.assertEqual(result["verdict"], "INSUFFICIENT_EVIDENCE")
        self.assertFalse(result["customer_value_proven"])

    def test_observed_arithmetic_includes_setup_cash_and_price(self):
        result = evaluate(fixture())
        self.assertEqual(result["observed_time_value_after_customer_overhead_usd"], "130.00")
        self.assertEqual(result["observed_time_value_after_price_usd"], "30.00")
        self.assertEqual(result["verdict"], "REPORTED_TIME_VALUE_EXCEEDS_PRICE")
        self.assertFalse(result["measurement_authenticity_verified"])

    def test_exact_price_is_not_more_than_price(self):
        data = fixture()
        data["extra_customer_cost_usd"] = 35
        self.assertEqual(evaluate(data)["verdict"], "DOES_NOT_EXCEED_PRICE")

    def test_subcent_comparison_retains_unrounded_evidence(self):
        data = fixture()
        data["extra_customer_cost_usd"] = "34.9999"
        result = evaluate(data)
        self.assertEqual(result["unrounded_time_value_after_price_usd"], "0.0001")
        self.assertEqual(result["verdict"], "REPORTED_TIME_VALUE_EXCEEDS_PRICE")

    def test_customer_support_and_evaluation_count_once(self):
        data = fixture()
        data["extra_customer_support_minutes"] = 10
        data["nonoverlapping_customer_evaluation_minutes"] = 20
        self.assertEqual(evaluate(data)["observed_time_value_after_price_usd"], "15.00")

    def test_synthetic_and_missing_gates_cannot_pass(self):
        for key, value in [("evidence_kind", "synthetic"), ("all_attempts_included", False),
                           ("installation_passed", "true"), ("customer_hourly_value_usd", None)]:
            with self.subTest(key=key):
                data = fixture()
                data[key] = value
                self.assertEqual(evaluate(data)["verdict"], "INSUFFICIENT_EVIDENCE")

    def test_failed_quality_or_missing_record_blocks_value_claim(self):
        for key, value in [("quality_passed", False), ("comparable", False), ("measurement_record", "")]:
            with self.subTest(key=key):
                data = fixture()
                data["paired_observations"][0][key] = value
                self.assertEqual(evaluate(data)["verdict"], "INSUFFICIENT_EVIDENCE")

    def test_lost_time_counts_against_benefit(self):
        data = fixture()
        data["paired_observations"][0]["workflow_total_seconds"] = 24000
        self.assertEqual(evaluate(data)["verdict"], "DOES_NOT_EXCEED_PRICE")

    def test_duplicate_jobs_and_nonfinite_values_rejected(self):
        data = fixture()
        data["paired_observations"].append(copy.deepcopy(data["paired_observations"][0]))
        with self.assertRaises(EvidenceError):
            evaluate(data)
        for value in [float("inf"), float("nan"), -1, True]:
            with self.subTest(value=value):
                data = fixture()
                data["paired_observations"][0]["workflow_total_seconds"] = value
                with self.assertRaises(EvidenceError):
                    evaluate(data)


if __name__ == "__main__":
    unittest.main()
