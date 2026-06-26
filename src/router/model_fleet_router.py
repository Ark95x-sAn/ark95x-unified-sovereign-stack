"""ARC X model fleet router.

Purpose:
    Select the best available model/agent/tool path for a request.

This module is intentionally minimal and auditable. It does not call external
models directly. It returns a route decision object that a caller can execute
only after governance and approval checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List
import uuid


@dataclass
class ModelProfile:
    model_id: str
    model_type: str
    strengths: List[str]
    best_tasks: List[str]
    privacy_level: str = "unknown"
    cost: str = "unknown"
    speed: str = "unknown"
    context_capacity: str = "unknown"
    last_eval_score: float = 50.0
    enabled: bool = True
    do_not_use_for: List[str] = field(default_factory=list)


DEFAULT_MODEL_FLEET: List[ModelProfile] = [
    ModelProfile(
        model_id="gpt-5.5-thinking-pro",
        model_type="reasoning",
        strengths=["long_context", "planning", "cross_domain_reasoning", "eval"],
        best_tasks=["strategy", "architecture", "client_delivery", "reasoning", "governance"],
        privacy_level="public_api",
        cost="high",
        speed="medium",
        context_capacity="huge",
        last_eval_score=92,
    ),
    ModelProfile(
        model_id="codex",
        model_type="code",
        strengths=["repo_work", "debugging", "tests", "implementation"],
        best_tasks=["code", "github", "tests", "refactor"],
        privacy_level="public_api",
        cost="medium",
        speed="medium",
        context_capacity="large",
        last_eval_score=88,
    ),
    ModelProfile(
        model_id="local-small-fast",
        model_type="local",
        strengths=["privacy", "speed", "drafting", "classification"],
        best_tasks=["classification", "tagging", "quick_summary", "private_draft"],
        privacy_level="local",
        cost="low",
        speed="fast",
        context_capacity="medium",
        last_eval_score=70,
    ),
]

DOMAIN_KEYWORDS = {
    "code": ["code", "repo", "github", "bug", "test", "python", "typescript", "codex", "build", "deploy", "package", "pypi", "npm"],
    "vision": ["image", "photo", "screenshot", "visual", "picture"],
    "research": ["research", "source", "market", "current", "news", "verify", "search", "analyze", "dark pool", "funding", "options flow", "intelligence"],
    "client_delivery": ["client", "diagnostic", "leak map", "delivery", "dashboard"],
    "security": ["security", "risk", "harden", "incident", "audit", "vulnerability", "vulnerabilities", "secure", "threat"],
    "automation": ["n8n", "workflow", "automation", "zapier", "make", "webhook", "teams", "office", "schedule", "message", "send"],
}

RISK_KEYWORDS = [
    "send", "publish", "delete", "payment", "refund", "legal", "medical", "private",
    "password", "credential", "hack", "bypass", "surveillance", "track", "exploit",
]


def classify_domain(raw_signal: str) -> str:
    text = raw_signal.lower()
    scores = {domain: sum(1 for kw in kws if kw in text) for domain, kws in DOMAIN_KEYWORDS.items()}
    best_domain, score = max(scores.items(), key=lambda item: item[1])
    return best_domain if score > 0 else "general"


def classify_risk(raw_signal: str) -> str:
    text = raw_signal.lower()
    hits = sum(1 for kw in RISK_KEYWORDS if kw in text)
    if hits >= 3:
        return "high"
    if hits >= 1:
        return "medium"
    return "low"


def model_fit_score(model: ModelProfile, domain: str, risk_level: str, requested_privacy: str = "unknown") -> float:
    if not model.enabled:
        return -1

    score = model.last_eval_score
    if domain in model.best_tasks:
        score += 20
    if domain == "code" and model.model_type == "code":
        score += 25
    if domain == "vision" and model.model_type in {"vision", "reasoning"}:
        score += 10
    if domain in {"client_delivery", "general"} and model.model_type == "reasoning":
        score += 15
    if risk_level == "high" and model.privacy_level == "local":
        score += 12
    if requested_privacy == "local" and model.privacy_level != "local":
        score -= 30
    return max(0, min(100, score))


def route_request(request: Dict[str, Any], fleet: List[ModelProfile] | None = None) -> Dict[str, Any]:
    fleet = fleet or DEFAULT_MODEL_FLEET
    raw_signal = str(request.get("raw_signal", ""))
    requested_privacy = str(request.get("privacy", "unknown"))
    domain = classify_domain(raw_signal)
    risk_level = classify_risk(raw_signal)

    ranked = sorted(
        fleet,
        key=lambda m: model_fit_score(m, domain, risk_level, requested_privacy),
        reverse=True,
    )
    selected = ranked[0]
    fallback = [m.model_id for m in ranked[1:3]]
    review_required = risk_level != "low" or request.get("approval_mode") == "require_review"

    return {
        "request_id": request.get("request_id", str(uuid.uuid4())),
        "domain": domain,
        "selected_model": selected.model_id,
        "fallback_models": fallback,
        "selected_agents": _agents_for_domain(domain),
        "selected_tools": _tools_for_domain(domain),
        "reason": f"Selected {selected.model_id} for domain={domain}, risk={risk_level}.",
        "evidence_level": "mixed",
        "risk_level": risk_level,
        "review_required": review_required,
        "route_score": model_fit_score(selected, domain, risk_level, requested_privacy),
        "next_action": "stage_output_for_review" if review_required else "generate_draft",
        "memory_patch": {
            "domain": "model_routing",
            "store_action": "store",
            "tags": [domain, risk_level, selected.model_id],
        },
    }


def _agents_for_domain(domain: str) -> List[str]:
    return {
        "code": ["code_agent", "review_agent"],
        "vision": ["visual_due_diligence_agent", "defensive_governor"],
        "research": ["research_agent", "truth_lens"],
        "client_delivery": ["lead_leak_agent", "client_delivery_agent", "guard"],
        "security": ["security_learning_cell", "defensive_governor"],
        "automation": ["automation_builder", "guard"],
        "general": ["apex_coordinator", "intention_interpreter"],
    }.get(domain, ["apex_coordinator"])


def _tools_for_domain(domain: str) -> List[str]:
    return {
        "code": ["github", "codex"],
        "vision": ["visual_intake", "memory"],
        "research": ["web_research", "citations"],
        "client_delivery": ["notion_or_sheet", "google_drive", "approval_queue"],
        "security": ["checklist", "audit_log"],
        "automation": ["n8n", "webhook", "approval_queue"],
        "general": ["memory", "approval_queue"],
    }.get(domain, ["memory"])


if __name__ == "__main__":
    sample = {"raw_signal": "Build the client diagnostic dashboard and lead leak workflow", "approval_mode": "auto_draft"}
    print(route_request(sample))
