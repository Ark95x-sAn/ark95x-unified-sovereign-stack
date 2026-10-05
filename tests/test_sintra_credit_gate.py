"""Behavior checks for actual budget failure boundaries, not account integration."""
import unittest
import json
import subprocess
import sys
from pathlib import Path
from tools.sintra_credit_gate import plan


class CreditGateTests(unittest.TestCase):
    def test_unknown_account_holds(self):
        self.assertEqual(plan()["status"], "HOLD")

    def test_monthly_pool_paces_below_ceiling(self):
        result = plan(250, 30, 0, reserve=25, next_task=5)
        self.assertEqual(result["maximum_next_spend"], 7.5)
        self.assertEqual(result["status"], "FITS_ESTIMATE")

    def test_daily_ceiling_applies_to_larger_pool(self):
        self.assertEqual(plan(1000, 30, 0, reserve=100)["maximum_next_spend"], 20)

    def test_used_credits_count_once(self):
        result = plan(245, 30, 5, reserve=25, next_task=2)
        self.assertEqual(result["maximum_next_spend"], 2.5)
        self.assertEqual(result["status"], "FITS_ESTIMATE")

    def test_pending_native_work_reduces_envelope(self):
        self.assertEqual(plan(250, 30, 0, reserve=25, pending=3)["maximum_next_spend"], 4.5)

    def test_oversized_estimate_holds(self):
        self.assertEqual(plan(250, 30, 0, reserve=25, next_task=20)["status"], "HOLD")

    def test_daily_use_exhausted_holds(self):
        self.assertEqual(plan(1000, 30, 20, reserve=100, next_task=1)["status"], "HOLD")

    def test_reserve_is_not_spendable(self):
        self.assertEqual(plan(25, 1, 0, reserve=25, next_task=1)["status"], "HOLD")

    def test_bad_or_unbounded_inputs_hold(self):
        cases = [dict(balance=-1), dict(balance="NaN"), dict(balance="Infinity"),
                 dict(days=0), dict(days=2.5), dict(pending=-1),
                 dict(daily_ceiling=21), dict(next_task=0)]
        for change in cases:
            kwargs = dict(balance=250, days=30, spent_today=0, reserve=25, next_task=1)
            kwargs.update(change)
            with self.subTest(change=change):
                self.assertEqual(plan(**kwargs)["status"], "HOLD")

    def test_no_estimate_is_only_budget_information(self):
        self.assertEqual(plan(250, 30, 0, reserve=25)["status"], "BUDGET_ONLY")

    def test_cli_unknown_usage_returns_hold_exit(self):
        tool = Path(__file__).resolve().parents[1] / "tools" / "sintra_credit_gate.py"
        result = subprocess.run([sys.executable, str(tool)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "HOLD")

    def test_cli_example_reports_paced_envelope(self):
        tool = Path(__file__).resolve().parents[1] / "tools" / "sintra_credit_gate.py"
        result = subprocess.run([sys.executable, str(tool), "--balance", "250", "--days", "30", "--spent-today", "0", "--reserve", "25", "--next-task", "5"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertEqual(output["maximum_next_spend"], 7.5)
        self.assertFalse(output["native_usage_enforced"])



if __name__ == "__main__":
    unittest.main()
