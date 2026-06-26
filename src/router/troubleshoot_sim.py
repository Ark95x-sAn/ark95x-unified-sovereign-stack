"""
ARK95X Routing Troubleshooter + Simulator
==========================================
Simulate, review, and diagnose the full routing stack without
making live API calls. Runs every request through the algorithm
and stacks the decision data for review.

Use this to:
    - Test routing before going live
    - Debug why a request went to the wrong model/chain/node
    - Validate that PC nodes would receive tasks correctly
    - Generate a routing report for any batch of intents
    - Stress-test the coordinator with simulated node failures
"""

from __future__ import annotations

import json
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

# Import the routing components
try:
    from core.ai_provider_chain import (
        classify_intent_to_chain,
        simulate_chain_routing,
        ALL_CHAINS,
        ProviderFamily,
        SMART_HOME_KEYWORDS,
    )
    from core.multi_pc_coordinator import (
        MultiPCCoordinator,
        CoordinatorTask,
        TaskPriority,
        CapabilityTag,
        NodeStatus,
    )
    from src.router.model_fleet_router import (
        route_request,
        classify_domain,
        classify_risk,
    )
    IMPORTS_OK = True
except ImportError as e:
    logger.warning(f"[SIM] Some imports failed (run from project root): {e}")
    IMPORTS_OK = False


# ---------------------------------------------------------------------------
# Simulation Models
# ---------------------------------------------------------------------------


@dataclass
class SimulatedRequest:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    raw_signal: str = ""
    expected_chain: str = ""
    expected_domain: str = ""
    expected_node: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class SimResult:
    request_id: str
    raw_signal: str
    chain_decision: dict[str, Any]
    fleet_decision: dict[str, Any]
    coordinator_decision: dict[str, Any]
    pass_fail: str
    latency_ms: float
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Test Suite
# ---------------------------------------------------------------------------


TEST_REQUESTS: list[SimulatedRequest] = [
    SimulatedRequest(
        raw_signal="Build a Python package and publish it to PyPI",
        expected_chain="openai",
        expected_domain="code",
        expected_node="codex",
        tags=["build", "python", "pypi"],
    ),
    SimulatedRequest(
        raw_signal="Search Google for the latest AI funding news",
        expected_chain="google",
        expected_domain="research",
        expected_node="google_search",
        tags=["search", "research"],
    ),
    SimulatedRequest(
        raw_signal="Turn on the living room lights",
        expected_chain="amazon",
        expected_domain="general",
        expected_node="alexa",
        tags=["smart_home", "iot"],
    ),
    SimulatedRequest(
        raw_signal="Send a Teams message to the restaurant staff about the schedule",
        expected_chain="microsoft",
        expected_domain="automation",
        expected_node="microsoft_graph",
        tags=["office", "teams"],
    ),
    SimulatedRequest(
        raw_signal="Review this code for security vulnerabilities",
        expected_chain="anthropic",
        expected_domain="security",
        expected_node="claude_pro",
        tags=["security", "code_review"],
    ),
    SimulatedRequest(
        raw_signal="Run this locally with Ollama — no cloud",
        expected_chain="local",
        expected_domain="general",
        expected_node="ollama_head",
        tags=["local", "private"],
    ),
    SimulatedRequest(
        raw_signal="Analyze dark pool activity and flag unusual options flow",
        expected_chain="openai",
        expected_domain="research",
        expected_node="chatgpt_pro",
        tags=["trading", "finance"],
    ),
    SimulatedRequest(
        raw_signal="Generate 100 passive income product ideas as a JSON list",
        expected_chain="openai",
        expected_domain="general",
        expected_node="chatgpt_pro",
        tags=["ideas", "business"],
    ),
    SimulatedRequest(
        raw_signal="Deploy the n8n workflow to production Docker stack",
        expected_chain="openai",
        expected_domain="automation",
        expected_node="codex",
        tags=["deploy", "n8n", "docker"],
    ),
    SimulatedRequest(
        raw_signal="Set the thermostat to 72 degrees",
        expected_chain="amazon",
        expected_domain="general",
        expected_node="alexa",
        tags=["smart_home", "thermostat"],
    ),
]


# ---------------------------------------------------------------------------
# Simulator
# ---------------------------------------------------------------------------


class RoutingSimulator:
    """
    Dry-runs every routing decision across chain, fleet, and coordinator layers.
    Returns stacked analysis for review.
    """

    def __init__(self) -> None:
        self.results: list[SimResult] = []
        self._coordinator: MultiPCCoordinator | None = None
        if IMPORTS_OK:
            self._coordinator = MultiPCCoordinator()

    def simulate_request(self, req: SimulatedRequest) -> SimResult:
        start = time.time()
        notes: list[str] = []

        # Layer 1: AI Provider Chain routing
        chain_decision: dict[str, Any] = {}
        if IMPORTS_OK:
            chain_decision = simulate_chain_routing(req.raw_signal)
        else:
            chain_decision = {"error": "imports_unavailable", "raw_signal": req.raw_signal}

        # Layer 2: Model Fleet routing
        fleet_decision: dict[str, Any] = {}
        if IMPORTS_OK:
            fleet_decision = route_request({
                "raw_signal": req.raw_signal,
                "request_id": req.request_id,
            })

        # Layer 3: Coordinator node selection
        coordinator_decision: dict[str, Any] = {}
        if IMPORTS_OK and self._coordinator:
            required_caps = self._tags_to_capabilities(req.tags)
            task = CoordinatorTask(
                task_id=req.request_id,
                title=req.raw_signal[:60],
                required_capabilities=required_caps,
                priority=TaskPriority.NORMAL,
            )
            best_node = self._coordinator.best_node_for_task(task)
            if best_node:
                coordinator_decision = {
                    "selected_node": best_node.registration.node_id,
                    "node_name": best_node.registration.name,
                    "capability_score": best_node.capability_score(required_caps),
                    "status": best_node.health.status.value,
                }
            else:
                coordinator_decision = {"selected_node": None, "reason": "no_nodes_online"}

        # Pass/fail check
        chain_ok = chain_decision.get("selected_family") == req.expected_chain if req.expected_chain else True
        fleet_ok = fleet_decision.get("domain") == req.expected_domain if req.expected_domain else True

        if not chain_ok:
            notes.append(
                f"CHAIN MISMATCH: expected={req.expected_chain} "
                f"got={chain_decision.get('selected_family')}"
            )
        if not fleet_ok:
            notes.append(
                f"DOMAIN MISMATCH: expected={req.expected_domain} "
                f"got={fleet_decision.get('domain')}"
            )
        if not chain_decision.get("api_key_set", True):
            notes.append(
                f"UNCONFIGURED: {chain_decision.get('api_key_required')} not set in env"
            )
        if coordinator_decision.get("selected_node") is None:
            notes.append("NO NODE AVAILABLE: all coordinator nodes offline")

        pass_fail = "PASS" if chain_ok and fleet_ok else "FAIL"
        latency_ms = round((time.time() - start) * 1000, 1)

        return SimResult(
            request_id=req.request_id,
            raw_signal=req.raw_signal,
            chain_decision=chain_decision,
            fleet_decision=fleet_decision,
            coordinator_decision=coordinator_decision,
            pass_fail=pass_fail,
            latency_ms=latency_ms,
            notes=notes,
        )

    def run_test_suite(self) -> dict[str, Any]:
        """Run all test requests and return a stacked diagnostic report."""
        logger.info(f"[SIM] Running {len(TEST_REQUESTS)} routing simulations")
        self.results = [self.simulate_request(req) for req in TEST_REQUESTS]

        passed = [r for r in self.results if r.pass_fail == "PASS"]
        failed = [r for r in self.results if r.pass_fail == "FAIL"]

        chain_distribution: dict[str, int] = {}
        domain_distribution: dict[str, int] = {}
        node_distribution: dict[str, int] = {}

        for r in self.results:
            chain = r.chain_decision.get("selected_family", "unknown")
            domain = r.fleet_decision.get("domain", "unknown")
            node = r.coordinator_decision.get("selected_node", "no_node")
            chain_distribution[chain] = chain_distribution.get(chain, 0) + 1
            domain_distribution[domain] = domain_distribution.get(domain, 0) + 1
            node_distribution[node] = node_distribution.get(node, 0) + 1

        avg_latency = sum(r.latency_ms for r in self.results) / len(self.results)

        report = {
            "summary": {
                "total": len(self.results),
                "passed": len(passed),
                "failed": len(failed),
                "pass_rate_pct": round(len(passed) / len(self.results) * 100, 1),
                "avg_latency_ms": round(avg_latency, 1),
            },
            "distribution": {
                "chains": chain_distribution,
                "domains": domain_distribution,
                "nodes": node_distribution,
            },
            "failures": [
                {
                    "request_id": r.request_id,
                    "signal": r.raw_signal[:80],
                    "notes": r.notes,
                }
                for r in failed
            ],
            "results": [
                {
                    "id": r.request_id,
                    "signal": r.raw_signal[:60],
                    "chain": r.chain_decision.get("selected_family"),
                    "domain": r.fleet_decision.get("domain"),
                    "model": r.fleet_decision.get("selected_model"),
                    "node": r.coordinator_decision.get("selected_node"),
                    "pass_fail": r.pass_fail,
                    "latency_ms": r.latency_ms,
                    "notes": r.notes,
                }
                for r in self.results
            ],
        }
        return report

    def simulate_node_failure(self, node_id: str) -> dict[str, Any]:
        """Simulate a PC node going offline and test failover routing."""
        if not IMPORTS_OK or not self._coordinator:
            return {"error": "coordinator not available"}

        node = self._coordinator.nodes.get(node_id)
        if not node:
            return {"error": f"node {node_id} not found"}

        original_status = node.health.status
        node.health.status = NodeStatus.OFFLINE
        logger.info(f"[SIM] Simulating offline: {node_id}")

        failover_results: list[dict[str, Any]] = []
        for req in TEST_REQUESTS[:5]:
            caps = self._tags_to_capabilities(req.tags)
            task = CoordinatorTask(
                task_id=req.request_id,
                title=req.raw_signal[:40],
                required_capabilities=caps,
            )
            best = self._coordinator.best_node_for_task(task)
            failover_results.append({
                "request": req.raw_signal[:50],
                "failover_node": best.registration.node_id if best else None,
                "score": best.capability_score(caps) if best else 0,
            })

        node.health.status = original_status
        logger.info(f"[SIM] Node {node_id} restored to {original_status.value}")

        return {
            "simulated_failure": node_id,
            "failover_results": failover_results,
            "all_covered": all(r["failover_node"] is not None for r in failover_results),
        }

    def stress_test(self, n_requests: int = 100) -> dict[str, Any]:
        """Generate N random requests and measure routing distribution."""
        signals = [
            "Build a React app",
            "Search for competitors",
            "Turn off the lights",
            "Send a Teams message",
            "Review security of this code",
            "Run locally on Ollama",
            "Deploy Docker stack",
            "Analyze options flow",
            "Set thermostat to 68",
            "Write marketing copy",
        ]
        start = time.time()
        chain_counts: dict[str, int] = {}
        domain_counts: dict[str, int] = {}
        node_counts: dict[str, int] = {}

        for _ in range(n_requests):
            signal = random.choice(signals)
            req = SimulatedRequest(raw_signal=signal)
            result = self.simulate_request(req)
            c = result.chain_decision.get("selected_family", "unknown")
            d = result.fleet_decision.get("domain", "unknown")
            n = result.coordinator_decision.get("selected_node", "no_node")
            chain_counts[c] = chain_counts.get(c, 0) + 1
            domain_counts[d] = domain_counts.get(d, 0) + 1
            node_counts[n] = node_counts.get(n, 0) + 1

        elapsed = round((time.time() - start) * 1000, 1)
        return {
            "n_requests": n_requests,
            "total_ms": elapsed,
            "avg_ms": round(elapsed / n_requests, 2),
            "throughput_rps": round(n_requests / (elapsed / 1000), 0),
            "chain_distribution": chain_counts,
            "domain_distribution": domain_counts,
            "node_distribution": node_counts,
        }

    def diagnose_single(self, raw_signal: str) -> dict[str, Any]:
        """Deep-dive single request through all routing layers."""
        req = SimulatedRequest(raw_signal=raw_signal)
        result = self.simulate_request(req)
        return {
            "input": raw_signal,
            "LAYER_1_AI_CHAIN": {
                "family": result.chain_decision.get("selected_family"),
                "chain_name": result.chain_decision.get("chain_name"),
                "head_model": result.chain_decision.get("head"),
                "body_model": result.chain_decision.get("body"),
                "memory_store": result.chain_decision.get("memory"),
                "voice_hub": result.chain_decision.get("voice"),
                "smart_home": result.chain_decision.get("smart_home_trigger"),
                "api_ready": result.chain_decision.get("api_key_set"),
                "offline_fallback": result.chain_decision.get("offline_fallback"),
            },
            "LAYER_2_MODEL_FLEET": {
                "domain": result.fleet_decision.get("domain"),
                "risk_level": result.fleet_decision.get("risk_level"),
                "selected_model": result.fleet_decision.get("selected_model"),
                "fallback_models": result.fleet_decision.get("fallback_models"),
                "agents": result.fleet_decision.get("selected_agents"),
                "tools": result.fleet_decision.get("selected_tools"),
                "review_required": result.fleet_decision.get("review_required"),
            },
            "LAYER_3_PC_COORDINATOR": {
                "assigned_node": result.coordinator_decision.get("selected_node"),
                "node_name": result.coordinator_decision.get("node_name"),
                "capability_score": result.coordinator_decision.get("capability_score"),
            },
            "VERDICT": result.pass_fail,
            "NOTES": result.notes,
            "latency_ms": result.latency_ms,
        }

    @staticmethod
    def _tags_to_capabilities(tags: list[str]) -> list[CapabilityTag]:
        if not IMPORTS_OK:
            return []
        mapping = {
            "gpu": CapabilityTag.GPU,
            "docker": CapabilityTag.DOCKER,
            "build": CapabilityTag.BUILD,
            "deploy": CapabilityTag.DEPLOY,
            "scraping": CapabilityTag.SCRAPING,
            "trading": CapabilityTag.TRADING,
            "monitor": CapabilityTag.MONITORING,
            "automation": CapabilityTag.AUTOMATION,
            "local": CapabilityTag.LOCAL_LLM,
            "private": CapabilityTag.LOCAL_LLM,
            "n8n": CapabilityTag.AUTOMATION,
        }
        caps: list[CapabilityTag] = []
        for tag in tags:
            cap = mapping.get(tag.lower())
            if cap and cap not in caps:
                caps.append(cap)
        return caps


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    sim = RoutingSimulator()

    print("=" * 60)
    print("ARK95X ROUTING TROUBLESHOOTER")
    print("=" * 60)

    # Full test suite
    report = sim.run_test_suite()
    print(f"\nTest Suite: {report['summary']['passed']}/{report['summary']['total']} passed "
          f"({report['summary']['pass_rate_pct']}%)")
    print(f"Avg latency: {report['summary']['avg_latency_ms']}ms")

    if report["failures"]:
        print(f"\nFailures ({len(report['failures'])}):")
        for f in report["failures"]:
            print(f"  ✗ {f['signal']}")
            for note in f["notes"]:
                print(f"    → {note}")

    print("\nChain distribution:")
    for chain, count in sorted(report["distribution"]["chains"].items(), key=lambda x: -x[1]):
        bar = "█" * count
        print(f"  {chain:<15} {bar} ({count})")

    print("\nNode distribution:")
    for node, count in sorted(report["distribution"]["nodes"].items(), key=lambda x: -x[1]):
        print(f"  {node:<20} {count}")

    # Deep-dive a single signal
    print("\n" + "=" * 60)
    print("DEEP DIAGNOSIS: 'Run Ollama locally for privacy'")
    print("=" * 60)
    diag = sim.diagnose_single("Run this model locally on Ollama for privacy")
    print(json.dumps(diag, indent=2))

    # Stress test
    print("\n" + "=" * 60)
    print("STRESS TEST: 100 requests")
    stress = sim.stress_test(100)
    print(f"  {stress['n_requests']} requests in {stress['total_ms']}ms "
          f"({stress['throughput_rps']:.0f} req/s)")

    # Node failure simulation
    print("\n" + "=" * 60)
    print("FAILOVER SIM: pc_win11 goes offline")
    failover = sim.simulate_node_failure("pc_win11")
    print(f"  All tasks covered by failover: {failover.get('all_covered')}")
    for r in failover.get("failover_results", []):
        print(f"  '{r['request'][:40]}' → {r['failover_node']} (score={r['score']:.1f})")
