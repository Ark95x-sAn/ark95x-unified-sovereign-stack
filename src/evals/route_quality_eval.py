"""ARC X route quality evaluator."""

from __future__ import annotations

from typing import Any, Dict, List

REQUIRED_KEYS = [
    "request_id", "domain", "selected_model", "reason", "risk_level",
    "review_required", "route_score", "next_action", "memory_patch",
]


def evaluate_route(route: Dict[str, Any]) -> Dict[str, Any]:
    """Return a simple auditable quality report for a route decision."""
    missing = [key for key in REQUIRED_KEYS if key not in route]
    score = 100
    notes: List[str] = []

    if missing:
        score -= 10 * len(missing)
        notes.append(f"Missing required keys: {missing}")

    if route.get("risk_level") in {"medium", "high"} and not route.get("review_required"):
        score -= 35
        notes.append("Medium/high risk route must require review.")

    if not route.get("selected_model"):
        score -= 20
        notes.append("No selected model.")

    if not route.get("selected_agents"):
        score -= 10
        notes.append("No agent route selected.")

    if not route.get("selected_tools"):
        score -= 10
        notes.append("No tool route selected.")

    if not route.get("memory_patch"):
        score -= 10
        notes.append("No memory patch generated.")

    return {
        "quality_score": max(0, min(100, score)),
        "pass": score >= 80,
        "notes": notes or ["Route decision passed basic checks."],
    }


if __name__ == "__main__":
    demo = {
        "request_id": "demo",
        "domain": "client_delivery",
        "selected_model": "gpt-5.5-thinking-pro",
        "reason": "demo",
        "risk_level": "medium",
        "review_required": True,
        "route_score": 92,
        "next_action": "stage_output_for_review",
        "selected_agents": ["lead_leak_agent"],
        "selected_tools": ["approval_queue"],
        "memory_patch": {"domain": "model_routing"},
    }
    print(evaluate_route(demo))
