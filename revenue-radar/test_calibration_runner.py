import json
import unittest
from pathlib import Path

import calibration_runner


HERE = Path(__file__).resolve().parent


class CalibrationRunnerTests(unittest.TestCase):
    def test_example_gold_set_has_25_cases_and_passes_automated_checks(self):
        cases = calibration_runner.load_cases(HERE / "gold_set.example.json")
        report = calibration_runner.run_calibration(cases)
        self.assertEqual(report["automated_metrics"]["case_count"], 25)
        self.assertEqual(report["automated_metrics"]["passed_cases"], 25)
        self.assertTrue(report["automated_gate_passed"])
        self.assertFalse(report["phase_promotion_allowed"])
        self.assertIsNone(report["gate_results"]["substantial_rewrite_rate"])

    def test_duplicate_case_is_detected_and_similar_case_stays_separate(self):
        cases = calibration_runner.load_cases(HERE / "gold_set.example.json")
        report = calibration_runner.run_calibration(cases)
        by_id = {item["case_id"]: item for item in report["results"]}
        self.assertEqual(by_id["RR-023"]["duplicate_of"], "RR-001")
        self.assertIsNone(by_id["RR-024"]["duplicate_of"])

    def test_report_is_json_serializable(self):
        cases = calibration_runner.load_cases(HERE / "gold_set.example.json")
        report = calibration_runner.run_calibration(cases)
        json.dumps(report)


if __name__ == "__main__":
    unittest.main()
