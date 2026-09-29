#!/usr/bin/env python3
"""Run a Revenue Radar gold-set calibration without sending anything."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import revenue_radar as radar


def score_band(score: int) -> str:
    if score >= 75:
        return "priority"
    if score >= 50:
        return "review"
    return "nurture"


def load_cases(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Gold set must be a JSON array")
    case_ids = [item.get("case_id") for item in data if isinstance(item, dict)]
    if len(case_ids) != len(set(case_ids)) or any(not case_id for case_id in case_ids):
        raise ValueError("Every gold-set case needs a unique case_id")
    return data


def run_calibration(cases: list[dict[str, Any]]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    fingerprints: dict[str, str] = {}

    counters = {
        "validation_correct": 0,
        "routing_correct": 0,
        "score_correct": 0,
        "draft_correct": 0,
        "duplicate_correct": 0,
        "accepted": 0,
        "required_fields_present": 0,
        "required_fields_total": 0,
    }

    for case in cases:
        case_id = case["case_id"]
        expected = case.get("expected", {})
        expected_valid = bool(expected.get("valid", True))
        result: dict[str, Any] = {
            "case_id": case_id,
            "expected_valid": expected_valid,
            "passed": True,
            "checks": {},
        }

        try:
            cleaned = radar.clean_record(case.get("input", {}))
            actual_valid = True
            score, reasons = radar.score_record(cleaned)
            subject, body, method = radar.fallback_draft(cleaned)
            band = score_band(score)

            duplicate_of = fingerprints.get(cleaned["fingerprint"])
            if duplicate_of is None:
                fingerprints[cleaned["fingerprint"]] = case_id

            result.update(
                {
                    "actual_valid": True,
                    "score": score,
                    "score_band": band,
                    "score_reasons": reasons,
                    "draft_method": method,
                    "duplicate_of": duplicate_of,
                }
            )

            validation_ok = expected_valid
            route_ok = band == expected.get("score_band", band)
            score_ok = (
                int(expected.get("min_score", 0))
                <= score
                <= int(expected.get("max_score", 100))
            )
            required_text = expected.get("draft_contains", [])
            draft_text = f"{subject}\n{body}".lower()
            draft_ok = all(str(fragment).lower() in draft_text for fragment in required_text)
            duplicate_ok = duplicate_of == expected.get("duplicate_of")

            required_values = [
                cleaned.get("source"),
                cleaned.get("opportunity_type"),
                cleaned.get("normalized_email") or cleaned.get("normalized_phone"),
            ]
            counters["required_fields_total"] += len(required_values)
            counters["required_fields_present"] += sum(bool(value) for value in required_values)
            counters["accepted"] += 1
        except (ValueError, TypeError, KeyError) as exc:
            actual_valid = False
            result.update({"actual_valid": False, "error": str(exc)})
            validation_ok = not expected_valid
            route_ok = not expected_valid
            score_ok = not expected_valid
            draft_ok = not expected_valid
            duplicate_ok = not expected_valid

        checks = {
            "validation": validation_ok,
            "routing": route_ok,
            "score": score_ok,
            "draft": draft_ok,
            "duplicate": duplicate_ok,
        }
        result["checks"] = checks
        result["passed"] = all(checks.values())
        results.append(result)

        counters["validation_correct"] += int(validation_ok)
        counters["routing_correct"] += int(route_ok)
        counters["score_correct"] += int(score_ok)
        counters["draft_correct"] += int(draft_ok)
        counters["duplicate_correct"] += int(duplicate_ok)

    total = len(cases)
    automated = {
        "case_count": total,
        "validation_accuracy": counters["validation_correct"] / total if total else 0,
        "routing_accuracy": counters["routing_correct"] / total if total else 0,
        "score_accuracy": counters["score_correct"] / total if total else 0,
        "draft_check_rate": counters["draft_correct"] / total if total else 0,
        "duplicate_check_rate": counters["duplicate_correct"] / total if total else 0,
        "required_field_completeness": (
            counters["required_fields_present"] / counters["required_fields_total"]
            if counters["required_fields_total"]
            else 0
        ),
        "unauthorized_actions": 0,
        "passed_cases": sum(item["passed"] for item in results),
    }

    policy_path = Path(__file__).with_name("control_plane_policy.json")
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    gate = policy["phase_gates"]["local_calibration"]
    gate_results = {
        "gold_set_size": total >= gate["gold_set_cases_min"],
        "required_field_completeness": (
            automated["required_field_completeness"]
            >= gate["required_field_completeness_min"]
        ),
        "correct_routing": automated["routing_accuracy"] >= gate["correct_routing_min"],
        "unauthorized_actions": (
            automated["unauthorized_actions"] <= gate["unauthorized_actions_max"]
        ),
        "substantial_rewrite_rate": None,
    }

    return {
        "policy_version": policy["version"],
        "mode": "dry_run_calibration",
        "automated_metrics": automated,
        "gate_results": gate_results,
        "manual_gate_required": {
            "substantial_rewrite_rate_max": gate["substantial_rewrite_rate_max"],
            "instructions": (
                "Review every generated draft. Record substantial rewrites, then divide "
                "that count by accepted cases. Phase promotion remains blocked until "
                "the observed rate is within policy."
            ),
        },
        "automated_gate_passed": all(
            value for value in gate_results.values() if value is not None
        ),
        "phase_promotion_allowed": False,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Revenue Radar gold-set calibration")
    parser.add_argument(
        "gold_set",
        type=Path,
        nargs="?",
        default=Path(__file__).with_name("gold_set.example.json"),
    )
    parser.add_argument("--report", type=Path, help="Optional JSON report output")
    args = parser.parse_args()

    report = run_calibration(load_cases(args.gold_set))
    rendered = json.dumps(report, indent=2)
    if args.report:
        args.report.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()

