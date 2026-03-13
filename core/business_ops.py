"""
ARK95X Business Operations Matrix
===================================
Manages 4 business verticals with model routing, automation triggers,
KPI metrics, and a decision governance framework (L1–L4).

Verticals:
    - nordskog_properties — Real estate management
    - leland_bar — Restaurant / bar operations
    - network_95 — Network and consulting services
    - legal_ops — Legal operations and compliance

Governance Levels:
    L1 Auto      — Fully automated, no human review
    L2 Notify    — Automated with notification to operator
    L3 Approve   — Requires Flame Signature approval
    L4 Council   — Requires multi-model council consensus
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from loguru import logger
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class GovernanceLevel(str, Enum):
    L1_AUTO = "L1"
    L2_NOTIFY = "L2"
    L3_APPROVE = "L3"
    L4_COUNCIL = "L4"


class DecisionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    ESCALATED = "escalated"
    EXECUTED = "executed"


class VerticalId(str, Enum):
    NORDSKOG_PROPERTIES = "nordskog_properties"
    LELAND_BAR = "leland_bar"
    NETWORK_95 = "network_95"
    LEGAL_OPS = "legal_ops"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

N8N_BASE_URL = os.getenv("N8N_URL", "http://localhost:5678")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class AutomationTrigger(BaseModel):
    """An n8n webhook-based automation trigger."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    webhook_url: str
    event: str = Field(..., description="Event that fires this trigger")
    governance_level: GovernanceLevel = GovernanceLevel.L1_AUTO
    enabled: bool = True


class KPIMetric(BaseModel):
    """A key performance indicator for a business vertical."""

    name: str
    current_value: float = 0.0
    target_value: float = 0.0
    unit: str = ""
    period: str = "monthly"
    trend: str = "stable"  # up, down, stable

    @property
    def attainment(self) -> float:
        if self.target_value == 0:
            return 0.0
        return round(self.current_value / self.target_value, 3)


class ModelRouting(BaseModel):
    """Maps task types to recommended AI models for a vertical."""

    task_type: str
    primary_models: list[str]
    fallback_models: list[str] = Field(default_factory=list)
    governance_level: GovernanceLevel = GovernanceLevel.L1_AUTO


class BusinessVertical(BaseModel):
    """A business vertical with its complete operational config."""

    id: VerticalId
    name: str
    description: str
    model_routing: list[ModelRouting] = Field(default_factory=list)
    automation_triggers: list[AutomationTrigger] = Field(default_factory=list)
    kpi_metrics: list[KPIMetric] = Field(default_factory=list)
    governance_level: GovernanceLevel = GovernanceLevel.L2_NOTIFY
    active: bool = True


class DecisionRequest(BaseModel):
    """A decision request flowing through the governance framework."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    vertical: VerticalId
    action: str
    description: str
    governance_level: GovernanceLevel
    status: DecisionStatus = DecisionStatus.PENDING
    requested_by: str = "system"
    flame_signature: str | None = None
    council_result: dict[str, Any] | None = None
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    resolved_at: str | None = None


# ---------------------------------------------------------------------------
# Vertical Definitions
# ---------------------------------------------------------------------------


VERTICALS: dict[VerticalId, BusinessVertical] = {
    VerticalId.NORDSKOG_PROPERTIES: BusinessVertical(
        id=VerticalId.NORDSKOG_PROPERTIES,
        name="Nordskog Properties",
        description="Real estate portfolio management, tenant relations, maintenance",
        governance_level=GovernanceLevel.L2_NOTIFY,
        model_routing=[
            ModelRouting(
                task_type="tenant_communication",
                primary_models=["chatgpt_pro", "claude_pro"],
                governance_level=GovernanceLevel.L1_AUTO,
            ),
            ModelRouting(
                task_type="lease_review",
                primary_models=["claude_pro"],
                fallback_models=["chatgpt_pro"],
                governance_level=GovernanceLevel.L3_APPROVE,
            ),
            ModelRouting(
                task_type="maintenance_scheduling",
                primary_models=["n8n", "chatgpt_pro"],
                governance_level=GovernanceLevel.L1_AUTO,
            ),
            ModelRouting(
                task_type="financial_analysis",
                primary_models=["chatgpt_pro", "claude_pro"],
                fallback_models=["perplexity_comet"],
                governance_level=GovernanceLevel.L2_NOTIFY,
            ),
            ModelRouting(
                task_type="legal_compliance",
                primary_models=["claude_pro"],
                governance_level=GovernanceLevel.L4_COUNCIL,
            ),
        ],
        automation_triggers=[
            AutomationTrigger(
                name="rent_reminder",
                webhook_url=f"{N8N_BASE_URL}/webhook/nordskog/rent-reminder",
                event="rent_due_3_days",
                governance_level=GovernanceLevel.L1_AUTO,
            ),
            AutomationTrigger(
                name="maintenance_alert",
                webhook_url=f"{N8N_BASE_URL}/webhook/nordskog/maintenance",
                event="maintenance_request_created",
                governance_level=GovernanceLevel.L1_AUTO,
            ),
            AutomationTrigger(
                name="lease_expiry_warning",
                webhook_url=f"{N8N_BASE_URL}/webhook/nordskog/lease-expiry",
                event="lease_expiry_30_days",
                governance_level=GovernanceLevel.L2_NOTIFY,
            ),
        ],
        kpi_metrics=[
            KPIMetric(name="occupancy_rate", target_value=0.95, unit="ratio", period="monthly"),
            KPIMetric(name="rent_collection_rate", target_value=0.98, unit="ratio", period="monthly"),
            KPIMetric(name="maintenance_response_time", target_value=24.0, unit="hours", period="monthly"),
            KPIMetric(name="tenant_satisfaction", target_value=4.5, unit="score_5", period="quarterly"),
        ],
    ),
    VerticalId.LELAND_BAR: BusinessVertical(
        id=VerticalId.LELAND_BAR,
        name="Leland Bar",
        description="Restaurant and bar operations, POS, inventory, staffing",
        governance_level=GovernanceLevel.L2_NOTIFY,
        model_routing=[
            ModelRouting(
                task_type="menu_optimization",
                primary_models=["chatgpt_pro", "claude_pro"],
                governance_level=GovernanceLevel.L2_NOTIFY,
            ),
            ModelRouting(
                task_type="inventory_management",
                primary_models=["n8n", "chatgpt_pro"],
                governance_level=GovernanceLevel.L1_AUTO,
            ),
            ModelRouting(
                task_type="staff_scheduling",
                primary_models=["chatgpt_pro"],
                fallback_models=["claude_pro"],
                governance_level=GovernanceLevel.L1_AUTO,
            ),
            ModelRouting(
                task_type="customer_feedback",
                primary_models=["claude_pro", "chatgpt_pro"],
                governance_level=GovernanceLevel.L1_AUTO,
            ),
            ModelRouting(
                task_type="pos_analytics",
                primary_models=["chatgpt_pro"],
                fallback_models=["perplexity_comet"],
                governance_level=GovernanceLevel.L2_NOTIFY,
            ),
        ],
        automation_triggers=[
            AutomationTrigger(
                name="low_inventory_alert",
                webhook_url=f"{N8N_BASE_URL}/webhook/leland/inventory-low",
                event="inventory_below_threshold",
                governance_level=GovernanceLevel.L1_AUTO,
            ),
            AutomationTrigger(
                name="daily_sales_report",
                webhook_url=f"{N8N_BASE_URL}/webhook/leland/daily-sales",
                event="end_of_business_day",
                governance_level=GovernanceLevel.L1_AUTO,
            ),
            AutomationTrigger(
                name="review_response",
                webhook_url=f"{N8N_BASE_URL}/webhook/leland/review-response",
                event="new_google_review",
                governance_level=GovernanceLevel.L2_NOTIFY,
            ),
        ],
        kpi_metrics=[
            KPIMetric(name="daily_revenue", target_value=5000.0, unit="usd", period="daily"),
            KPIMetric(name="food_cost_ratio", target_value=0.30, unit="ratio", period="weekly"),
            KPIMetric(name="labor_cost_ratio", target_value=0.25, unit="ratio", period="weekly"),
            KPIMetric(name="avg_ticket_size", target_value=35.0, unit="usd", period="daily"),
            KPIMetric(name="google_rating", target_value=4.7, unit="score_5", period="monthly"),
        ],
    ),
    VerticalId.NETWORK_95: BusinessVertical(
        id=VerticalId.NETWORK_95,
        name="Network 95",
        description="Technology consulting, AI services, network infrastructure",
        governance_level=GovernanceLevel.L2_NOTIFY,
        model_routing=[
            ModelRouting(
                task_type="client_proposal",
                primary_models=["claude_pro", "chatgpt_pro"],
                governance_level=GovernanceLevel.L3_APPROVE,
            ),
            ModelRouting(
                task_type="code_development",
                primary_models=["codex", "claude_pro"],
                fallback_models=["ollama_codellama", "copilot"],
                governance_level=GovernanceLevel.L1_AUTO,
            ),
            ModelRouting(
                task_type="research",
                primary_models=["perplexity_comet", "chatgpt_pro"],
                governance_level=GovernanceLevel.L1_AUTO,
            ),
            ModelRouting(
                task_type="infrastructure",
                primary_models=["claude_pro", "n8n", "docker_conductor"],
                governance_level=GovernanceLevel.L2_NOTIFY,
            ),
            ModelRouting(
                task_type="strategic_planning",
                primary_models=["claude_pro", "chatgpt_pro"],
                fallback_models=["grok_xai"],
                governance_level=GovernanceLevel.L3_APPROVE,
            ),
        ],
        automation_triggers=[
            AutomationTrigger(
                name="deployment_pipeline",
                webhook_url=f"{N8N_BASE_URL}/webhook/network95/deploy",
                event="code_merged_to_main",
                governance_level=GovernanceLevel.L2_NOTIFY,
            ),
            AutomationTrigger(
                name="client_followup",
                webhook_url=f"{N8N_BASE_URL}/webhook/network95/followup",
                event="proposal_sent_7_days",
                governance_level=GovernanceLevel.L1_AUTO,
            ),
            AutomationTrigger(
                name="uptime_alert",
                webhook_url=f"{N8N_BASE_URL}/webhook/network95/uptime",
                event="service_health_degraded",
                governance_level=GovernanceLevel.L1_AUTO,
            ),
        ],
        kpi_metrics=[
            KPIMetric(name="monthly_recurring_revenue", target_value=15000.0, unit="usd", period="monthly"),
            KPIMetric(name="client_retention_rate", target_value=0.90, unit="ratio", period="quarterly"),
            KPIMetric(name="project_completion_rate", target_value=0.95, unit="ratio", period="monthly"),
            KPIMetric(name="uptime_sla", target_value=0.999, unit="ratio", period="monthly"),
        ],
    ),
    VerticalId.LEGAL_OPS: BusinessVertical(
        id=VerticalId.LEGAL_OPS,
        name="Legal Operations",
        description="Legal compliance, contracts, IP protection, regulatory filings",
        governance_level=GovernanceLevel.L3_APPROVE,
        model_routing=[
            ModelRouting(
                task_type="contract_review",
                primary_models=["claude_pro"],
                fallback_models=["chatgpt_pro"],
                governance_level=GovernanceLevel.L4_COUNCIL,
            ),
            ModelRouting(
                task_type="compliance_check",
                primary_models=["claude_pro", "chatgpt_pro"],
                governance_level=GovernanceLevel.L3_APPROVE,
            ),
            ModelRouting(
                task_type="ip_filing",
                primary_models=["claude_pro"],
                governance_level=GovernanceLevel.L4_COUNCIL,
            ),
            ModelRouting(
                task_type="legal_research",
                primary_models=["perplexity_comet", "claude_pro"],
                fallback_models=["chatgpt_pro"],
                governance_level=GovernanceLevel.L2_NOTIFY,
            ),
            ModelRouting(
                task_type="document_drafting",
                primary_models=["claude_pro", "chatgpt_pro"],
                governance_level=GovernanceLevel.L3_APPROVE,
            ),
        ],
        automation_triggers=[
            AutomationTrigger(
                name="contract_expiry_alert",
                webhook_url=f"{N8N_BASE_URL}/webhook/legal/contract-expiry",
                event="contract_expiry_60_days",
                governance_level=GovernanceLevel.L2_NOTIFY,
            ),
            AutomationTrigger(
                name="compliance_deadline",
                webhook_url=f"{N8N_BASE_URL}/webhook/legal/compliance-deadline",
                event="filing_deadline_30_days",
                governance_level=GovernanceLevel.L2_NOTIFY,
            ),
        ],
        kpi_metrics=[
            KPIMetric(name="contract_review_time", target_value=48.0, unit="hours", period="monthly"),
            KPIMetric(name="compliance_score", target_value=1.0, unit="ratio", period="quarterly"),
            KPIMetric(name="active_contracts", target_value=0.0, unit="count", period="monthly"),
            KPIMetric(name="dispute_resolution_rate", target_value=0.95, unit="ratio", period="quarterly"),
        ],
    ),
}


# ---------------------------------------------------------------------------
# Decision Governance Engine
# ---------------------------------------------------------------------------


class GovernanceEngine:
    """Processes decisions through the L1–L4 governance framework."""

    def __init__(self) -> None:
        self._log: list[DecisionRequest] = []
        logger.info("GovernanceEngine initialized")

    def submit(self, request: DecisionRequest) -> DecisionRequest:
        """Submit a decision through the governance pipeline."""
        self._log.append(request)

        if request.governance_level == GovernanceLevel.L1_AUTO:
            request.status = DecisionStatus.EXECUTED
            request.resolved_at = datetime.now(timezone.utc).isoformat()
            logger.info(f"[L1 AUTO] Decision {request.id}: {request.action} — executed")

        elif request.governance_level == GovernanceLevel.L2_NOTIFY:
            request.status = DecisionStatus.EXECUTED
            request.resolved_at = datetime.now(timezone.utc).isoformat()
            logger.info(f"[L2 NOTIFY] Decision {request.id}: {request.action} — executed + notification sent")

        elif request.governance_level == GovernanceLevel.L3_APPROVE:
            if request.flame_signature:
                request.status = DecisionStatus.APPROVED
                request.resolved_at = datetime.now(timezone.utc).isoformat()
                logger.info(f"[L3 APPROVE] Decision {request.id}: {request.action} — approved via Flame Signature")
            else:
                request.status = DecisionStatus.PENDING
                logger.info(f"[L3 APPROVE] Decision {request.id}: {request.action} — awaiting Flame Signature")

        elif request.governance_level == GovernanceLevel.L4_COUNCIL:
            if request.council_result:
                agreement = request.council_result.get("agreement_score", 0)
                if agreement >= 0.6:
                    request.status = DecisionStatus.APPROVED
                    request.resolved_at = datetime.now(timezone.utc).isoformat()
                    logger.info(f"[L4 COUNCIL] Decision {request.id}: {request.action} — approved (agreement: {agreement})")
                else:
                    request.status = DecisionStatus.ESCALATED
                    logger.info(f"[L4 COUNCIL] Decision {request.id}: {request.action} — escalated (agreement: {agreement})")
            else:
                request.status = DecisionStatus.PENDING
                logger.info(f"[L4 COUNCIL] Decision {request.id}: {request.action} — awaiting council vote")

        return request

    def get_pending(self) -> list[DecisionRequest]:
        return [d for d in self._log if d.status == DecisionStatus.PENDING]

    def get_log(self, vertical: VerticalId | None = None) -> list[DecisionRequest]:
        if vertical:
            return [d for d in self._log if d.vertical == vertical]
        return list(self._log)

    def stats(self) -> dict[str, Any]:
        return {
            "total_decisions": len(self._log),
            "pending": sum(1 for d in self._log if d.status == DecisionStatus.PENDING),
            "approved": sum(1 for d in self._log if d.status == DecisionStatus.APPROVED),
            "executed": sum(1 for d in self._log if d.status == DecisionStatus.EXECUTED),
            "denied": sum(1 for d in self._log if d.status == DecisionStatus.DENIED),
            "escalated": sum(1 for d in self._log if d.status == DecisionStatus.ESCALATED),
        }


# ---------------------------------------------------------------------------
# Business Operations Manager
# ---------------------------------------------------------------------------


class BusinessOpsManager:
    """Central manager for all business vertical operations."""

    def __init__(self) -> None:
        self.verticals = VERTICALS.copy()
        self.governance = GovernanceEngine()
        logger.info(f"BusinessOpsManager initialized with {len(self.verticals)} verticals")

    def get_vertical(self, vertical_id: VerticalId) -> BusinessVertical | None:
        return self.verticals.get(vertical_id)

    def list_verticals(self) -> list[BusinessVertical]:
        return list(self.verticals.values())

    def get_routing(
        self, vertical_id: VerticalId, task_type: str
    ) -> ModelRouting | None:
        """Find the model routing config for a task type within a vertical."""
        vertical = self.verticals.get(vertical_id)
        if not vertical:
            return None
        for routing in vertical.model_routing:
            if routing.task_type == task_type:
                return routing
        return None

    def get_all_triggers(self) -> list[dict[str, Any]]:
        """Get all automation triggers across verticals."""
        triggers = []
        for vid, vertical in self.verticals.items():
            for trigger in vertical.automation_triggers:
                triggers.append({
                    "vertical": vid.value,
                    "trigger": trigger.model_dump(),
                })
        return triggers

    def kpi_dashboard(self) -> dict[str, Any]:
        """Generate a KPI dashboard across all verticals."""
        dashboard: dict[str, Any] = {}
        for vid, vertical in self.verticals.items():
            dashboard[vid.value] = {
                "name": vertical.name,
                "metrics": [
                    {
                        "name": m.name,
                        "current": m.current_value,
                        "target": m.target_value,
                        "attainment": m.attainment,
                        "unit": m.unit,
                        "trend": m.trend,
                    }
                    for m in vertical.kpi_metrics
                ],
            }
        return dashboard

    def submit_decision(
        self,
        vertical_id: VerticalId,
        action: str,
        description: str,
        governance_level: GovernanceLevel | None = None,
        flame_signature: str | None = None,
        council_result: dict[str, Any] | None = None,
    ) -> DecisionRequest:
        """Submit a decision through the governance framework."""
        vertical = self.verticals.get(vertical_id)
        level = governance_level or (vertical.governance_level if vertical else GovernanceLevel.L2_NOTIFY)

        request = DecisionRequest(
            vertical=vertical_id,
            action=action,
            description=description,
            governance_level=level,
            flame_signature=flame_signature,
            council_result=council_result,
        )
        return self.governance.submit(request)

    def summary(self) -> dict[str, Any]:
        """Full operational summary."""
        return {
            "verticals": {
                v.id.value: {
                    "name": v.name,
                    "active": v.active,
                    "governance_level": v.governance_level.value,
                    "model_routes": len(v.model_routing),
                    "triggers": len(v.automation_triggers),
                    "kpis": len(v.kpi_metrics),
                }
                for v in self.verticals.values()
            },
            "governance": self.governance.stats(),
        }


# Singleton
ops = BusinessOpsManager()
