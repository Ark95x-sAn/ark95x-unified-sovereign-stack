"""Calculate observed customer time-value; missing evidence never becomes proof.

This calculator verifies arithmetic and input structure, not the truth of supplied
measurements. Dollar-valued time is not demonstrated cash income or cost savings.
Run: python tools/n95_value_check.py observations.json
"""
from __future__ import annotations

import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


class EvidenceError(ValueError):
    pass


def number(value, name):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise EvidenceError(f"{name} must be a finite nonnegative number")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise EvidenceError(f"{name} is not numeric") from exc
    if not result.is_finite() or result < 0 or result > Decimal("1000000000"):
        raise EvidenceError(f"{name} is outside the supported range")
    return result


def evaluate(data):
    if not isinstance(data, dict):
        raise EvidenceError("input must be an object")
    price = number(data.get("price_usd", 100), "price_usd")
    if price != 100:
        raise EvidenceError("this offer's price must be 100 USD")
    rows = data.get("paired_observations", [])
    if not isinstance(rows, list) or len(rows) > 10000:
        raise EvidenceError("paired_observations must contain at most 10000 rows")
    result = {
        "schema": "n95-customer-value/1",
        "verdict": "INSUFFICIENT_EVIDENCE",
        "price_usd": "100.00",
        "observed_pairs": len(rows),
        "basis": "Reported job times only; quality and comparability are separate gates. No extrapolation.",
        "measurement_authenticity_verified": False,
        "cash_savings_proven": False,
        "customer_value_proven": False,
        "missing_or_failed_gates": [],
    }
    gates = result["missing_or_failed_gates"]
    if data.get("evidence_kind") != "actual_customer_measurements":
        gates.append("actual_customer_measurements_missing")
    if len(rows) < 10:
        gates.append("at_least_10_comparable_pairs_required")
    for key in ("all_attempts_included", "same_quality_target", "customer_acceptance_recorded",
                "customer_hourly_value_agreed", "installation_passed"):
        if data.get(key) is not True:
            gates.append(key)
    required = ("customer_hourly_value_usd", "customer_setup_minutes", "extra_customer_cost_usd",
                "extra_customer_support_minutes", "nonoverlapping_customer_evaluation_minutes")
    for key in required:
        if data.get(key) is None:
            gates.append(key)
    saved = Decimal(0)
    ids = set()
    for row in rows:
        if not isinstance(row, dict):
            raise EvidenceError("each observation must be an object")
        job_id = row.get("job_id")
        if not isinstance(job_id, str) or not job_id.strip() or len(job_id) > 200 or job_id in ids:
            raise EvidenceError("job_id must be unique, nonempty, and at most 200 characters")
        ids.add(job_id)
        baseline = number(row.get("best_free_alternative_seconds"), "best_free_alternative_seconds")
        assisted = number(row.get("workflow_total_seconds"), "workflow_total_seconds")
        # Assisted time includes gathering/formatting, running, reading, correction,
        # retry, and any support time paid by the customer's attention.
        saved += baseline - assisted
        if row.get("comparable") is not True or row.get("quality_passed") is not True:
            gates.append(f"quality_or_comparability:{job_id}")
        if not isinstance(row.get("measurement_record"), str) or not row["measurement_record"].strip():
            gates.append(f"measurement_record:{job_id}")
    result["observed_net_minutes_before_setup"] = str((saved / 60).quantize(Decimal("0.01")))
    if gates:
        return result
    hourly = number(data["customer_hourly_value_usd"], "customer_hourly_value_usd")
    setup = number(data["customer_setup_minutes"], "customer_setup_minutes")
    support = number(data["extra_customer_support_minutes"], "extra_customer_support_minutes")
    evaluation = number(data["nonoverlapping_customer_evaluation_minutes"], "nonoverlapping_customer_evaluation_minutes")
    extra = number(data["extra_customer_cost_usd"], "extra_customer_cost_usd")
    benefit = ((saved / 60 - setup - support - evaluation) / 60 * hourly) - extra
    surplus = benefit - price
    result.update({
        "observed_time_value_after_customer_overhead_usd": str(benefit.quantize(Decimal("0.01"))),
        "observed_time_value_after_price_usd": str(surplus.quantize(Decimal("0.01"))),
        "unrounded_time_value_after_overhead_usd": str(benefit),
        "unrounded_time_value_after_price_usd": str(surplus),
        "comparison": "Strictly positive unrounded surplus; rounded dollar display is informational.",
        "verdict": "REPORTED_TIME_VALUE_EXCEEDS_PRICE" if surplus > 0 else "DOES_NOT_EXCEED_PRICE",
        "limitations": [
            "Measurements and acceptance are supplied assertions until their records are audited.",
            "This is customer-valued time, not verified cash savings or guaranteed future benefit.",
            "No nine-reviewer vote, test score, forecast, or model agreement is used as customer evidence.",
        ],
    })
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("observations", type=Path)
    args = parser.parse_args()
    try:
        with args.observations.open("rb") as stream:
            raw = stream.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise EvidenceError("observation file exceeds 2 MiB")
        output = evaluate(json.loads(raw))
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"verdict": "INVALID_EVIDENCE", "error": str(exc)}))
        return 2
    print(json.dumps(output, indent=2))
    return 0 if output["verdict"] == "REPORTED_TIME_VALUE_EXCEEDS_PRICE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
