"""
ARK95X Shared Session State Schema
Canonical state object shared across all 3 crews and the meta-team.
Access via run_context.session_state in any tool or agent.
"""
from datetime import datetime, timezone
from agno.run import RunContext

# ─────────────────────────────────────────────
# INITIAL SESSION STATE — injected at Team init
# ─────────────────────────────────────────────
ARK95X_SESSION_STATE = {
    # INTEL CREW outputs
    "intel": {
        "signals": [],          # [{asset, signal, confidence, source, ts}]
        "whale_moves": [],      # [{wallet, action, amount, chain, ts}]
        "prices": {},           # {symbol: {price_usd, source, ts, confidence}}
        "social_sentiment": {}, # {topic: {score, volume, ts}}
        "last_intel_run": None,
    },
    # OPS CREW outputs
    "ops": {
        "portfolio": {},        # {asset: {qty, value_usd, chain}}
        "pending_routes": [],   # [{from_chain, to_chain, asset, amount, status}]
        "treasury_balance": 0.0,
        "rebalance_targets": {},
        "last_ops_run": None,
    },
    # STRATEGY CREW outputs
    "strategy": {
        "legal_flags": [],      # [{case_ref, flag_type, asset_id, severity}]
        "deployments": [],      # [{service, version, status, ts}]
        "evolution_log": [],    # [{model, change, rationale, ts}]
        "active_plan": None,
        "last_strategy_run": None,
    },
    # META-TEAM tracking
    "meta": {
        "cycle_count": 0,
        "last_full_run": None,
        "autonomous_score": 0.0,  # 0.0-1.0 autonomy rating
        "blockers": [],           # items requiring human approval
    },
}


# ─────────────────────────────────────────────
# SHARED STATE TOOLS (RunContext pattern)
# Used by any agent/team member
# ─────────────────────────────────────────────

def record_intel_signal(run_context: RunContext, asset: str, signal: str,
                        confidence: str, source: str) -> str:
    """Record an intel signal from any crew member into shared state."""
    entry = {
        "asset": asset,
        "signal": signal,
        "confidence": confidence,
        "source": source,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    run_context.session_state["intel"]["signals"].append(entry)
    run_context.session_state["intel"]["last_intel_run"] = entry["ts"]
    return f"Signal recorded: {signal} for {asset} [{confidence}]"


def update_price(run_context: RunContext, symbol: str, price_usd: float,
                 source: str, confidence: str) -> str:
    """Update a price entry in shared state."""
    run_context.session_state["intel"]["prices"][symbol] = {
        "price_usd": price_usd,
        "source": source,
        "confidence": confidence,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    return f"Price updated: {symbol} = ${price_usd} [{confidence}]"


def record_portfolio_position(run_context: RunContext, asset: str, qty: float,
                               value_usd: float, chain: str) -> str:
    """Update portfolio position in shared ops state."""
    run_context.session_state["ops"]["portfolio"][asset] = {
        "qty": qty,
        "value_usd": value_usd,
        "chain": chain,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    return f"Portfolio updated: {asset} qty={qty} value=${value_usd}"


def add_legal_flag(run_context: RunContext, case_ref: str, flag_type: str,
                   asset_id: str, severity: str) -> str:
    """Record a legal flag from Legal/Compliance agent."""
    flag = {
        "case_ref": case_ref,
        "flag_type": flag_type,
        "asset_id": asset_id,
        "severity": severity,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    run_context.session_state["strategy"]["legal_flags"].append(flag)
    if severity == "HIGH":
        run_context.session_state["meta"]["blockers"].append(
            f"LEGAL HOLD: {case_ref} -> {asset_id}"
        )
    return f"Legal flag recorded: {flag_type} on {asset_id} [{severity}]"


def log_deployment(run_context: RunContext, service: str, version: str,
                   status: str) -> str:
    """Log a deployment event from Deployment agent."""
    entry = {
        "service": service,
        "version": version,
        "status": status,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    run_context.session_state["strategy"]["deployments"].append(entry)
    return f"Deployment logged: {service} v{version} -> {status}"


def get_full_state(run_context: RunContext) -> str:
    """Return a summary of all state sections for meta-team synthesis."""
    import json
    state = run_context.session_state
    return json.dumps({
        "intel_signals": len(state["intel"]["signals"]),
        "prices_tracked": len(state["intel"]["prices"]),
        "portfolio_assets": len(state["ops"]["portfolio"]),
        "legal_flags": len(state["strategy"]["legal_flags"]),
        "deployments": len(state["strategy"]["deployments"]),
        "cycle_count": state["meta"]["cycle_count"],
        "autonomous_score": state["meta"]["autonomous_score"],
        "blockers": state["meta"]["blockers"],
    }, indent=2)
