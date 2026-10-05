"""Offline Sintra budget planning. Does not invoke or control Sintra."""
from __future__ import annotations

import argparse
import json
from decimal import Decimal, InvalidOperation, ROUND_DOWN

VERSION = "0.2"


def quantity(value, name):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{name} must be a finite nonnegative number") from None
    if not number.is_finite() or number < 0:
        raise ValueError(f"{name} must be a finite nonnegative number")
    return number


def rounded(value):
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_DOWN))


def plan(balance=None, days=None, spent_today=None, reserve=None,
         pending=0, daily_ceiling=20, next_task=None):
    base = {"version": VERSION, "scope": "offline planning only",
            "native_usage_enforced": False}
    if balance is None or days is None or spent_today is None:
        return dict(base, status="HOLD", reason="Supply current workspace balance, days to reset, and all known credits spent today.")
    try:
        b = quantity(balance, "balance")
        spent = quantity(spent_today, "spent_today")
        p = quantity(pending, "pending")
        ceiling = quantity(daily_ceiling, "daily_ceiling")
        d = quantity(days, "days")
        if d < 1 or d != d.to_integral_value():
            raise ValueError("days must be a positive whole number; include the current day")
        r = quantity(reserve, "reserve") if reserve is not None else b * Decimal("0.10")
        estimate = quantity(next_task, "next_task") if next_task is not None else None
        if ceiling > 20:
            raise ValueError("daily_ceiling cannot exceed the requested 20-credit limit")
        if estimate is not None and estimate == 0:
            raise ValueError("A zero estimate cannot authorize a paid Helper task")
    except ValueError as exc:
        return dict(base, status="HOLD", reason=str(exc))
    # Balance is current, after spent_today has already been charged.
    # Reconstruct today's starting pool for pacing, then subtract today's use.
    paced_today = max(Decimal(0), (b - r + spent) / d)
    available = max(Decimal(0), min(ceiling - spent - p,
                                    paced_today - spent - p,
                                    b - r - p))
    available = Decimal(str(rounded(available)))
    result = dict(base, current_balance=rounded(b), reserve=rounded(r),
                  days_to_reset=int(d), spent_today=rounded(spent),
                  pending_commitments=rounded(p), daily_ceiling=rounded(ceiling),
                  paced_daily_total=rounded(min(ceiling, paced_today)),
                  maximum_next_spend=rounded(available),
                  allocation={"delivery": rounded(available * Decimal("0.6")),
                              "check": rounded(available * Decimal("0.2")),
                              "unused_buffer": rounded(available * Decimal("0.2"))})
    if available == 0:
        return dict(result, status="HOLD", reason="No room remains after today's usage, pending work, reserve, and pacing.")
    if estimate is None:
        return dict(result, status="BUDGET_ONLY", reason="Enter a task estimate; verify native before/after usage. This result authorizes no account action.")
    if estimate > available:
        return dict(result, status="HOLD", next_task_estimate=rounded(estimate), reason="Task estimate exceeds the remaining envelope.")
    return dict(result, status="FITS_ESTIMATE", next_task_estimate=rounded(estimate),
                reason="Estimate fits. Actual native charges may differ; reconcile them before another task.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--balance", help="Current measured workspace credits, after today's charges")
    parser.add_argument("--days", help="Whole days to reset, including today")
    parser.add_argument("--spent-today", help="All workspace credits charged today, including other members/tasks")
    parser.add_argument("--reserve", help="Fixed credits to retain; defaults to 10%% of current balance")
    parser.add_argument("--pending", default="0", help="Credits committed to work not yet charged")
    parser.add_argument("--daily-ceiling", default="20")
    parser.add_argument("--next-task", help="Positive conservative estimate of this task's credits")
    args = vars(parser.parse_args())
    result = plan(**args)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 2 if result["status"] == "HOLD" else 0


if __name__ == "__main__":
    raise SystemExit(main())

