"""ARK95X Sovereign Agent Chain - Syndicated Squad Operations
Multi-browser end-to-end pipeline: Ingest -> Council -> Structure -> Build -> Deploy
Each step clones forward; reverse signals trigger re-processing.

Designed for: i7-9700K / RTX 2080 SUPER / 16GB / 4 Displays
Best-fit model assignments per task type for peak performance.
"""
import os
import json
import time
import asyncio
import httpx
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from loguru import logger

# === COMET ROUTER ENDPOINT ===
COMET_ROUTER = os.getenv("COMET_ROUTER_URL", "http://localhost:8100")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
N8N_WEBHOOK = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook")


# === SYNDICATED SQUAD DEFINITIONS ===
# Each squad = a browser group with assigned AI models optimized per task

class SquadRole(str, Enum):
    INGESTION = "ingestion"       # Browser Group 1 - Data collection
    FINANCIAL = "financial"       # Browser Group 2 - P&L, bookkeeping
    COUNCIL = "council"           # Browser Group 3 - Multi-model reasoning
    BUILDER = "builder"           # Browser Group 4 - Code generation
    EXECUTIVE = "executive"       # Browser Group 5 - Final synthesis


# Best make & model per squad role (tested/benchmarked)
SQUAD_MODEL_ASSIGNMENTS = {
    SquadRole.INGESTION: {
        "primary": "ollama/llama3",           # Fast local extraction
        "secondary": "groq/llama-3.3-70b",    # Speed fallback
        "task_types": ["research", "general"],
        "display": "Samsung 4K 28in",
        "ram_budget_mb": 2048,
    },
    SquadRole.FINANCIAL: {
        "primary": "ollama/mistral-7b",        # Best at structured tables
        "secondary": "anthropic/claude-sonnet", # Deep financial reasoning
        "task_types": ["business_ops", "analysis"],
        "display": "MITAC 40in",
        "ram_budget_mb": 2048,
    },
    SquadRole.COUNCIL: {
        "primary": "deepseek-r1",              # Deep reasoning chain
        "secondary": "anthropic/claude-sonnet", # Cross-validation
        "tertiary": "groq/llama-3.3-70b",      # Speed tiebreaker
        "task_types": ["analysis", "litigation"],
        "display": "Dell 21.7in",
        "ram_budget_mb": 3072,
    },
    SquadRole.BUILDER: {
        "primary": "anthropic/claude-sonnet",   # Best code generation
        "secondary": "ollama/deepseek-coder",   # Local code model
        "agents": ["manus_agent", "zencode_agent", "vibecoder_agent"],
        "task_types": ["code", "creative"],
        "display": "Samsung 4K split",
        "ram_budget_mb": 3072,
    },
    SquadRole.EXECUTIVE: {
        "primary": "openai/gpt-4o",            # Best synthesis
        "secondary": "anthropic/claude-sonnet", # Backup synthesis
        "task_types": ["general", "creative"],
        "display": "CDD 52in TV",
        "ram_budget_mb": 2048,
    },
}


@dataclass
class ChainTask:
    """A single task flowing through the agent chain."""
    task_id: str
    intent: str
    task_type: str = "general"
    priority: int = 3
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "pending"
    current_squad: Optional[str] = None
    data: dict = field(default_factory=dict)
    results: dict = field(default_factory=dict)
    chain_log: list = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class ChainStep:
    """One step in the sovereign agent chain."""
    step_num: int
    squad: SquadRole
    action: str
    input_key: str
    output_key: str


# === THE CHAIN: 5-step forward pipeline ===
SOVEREIGN_CHAIN = [
    ChainStep(1, SquadRole.INGESTION,  "ingest",    "intent",           "raw_data"),
    ChainStep(2, SquadRole.COUNCIL,    "analyze",   "raw_data",         "analyzed"),
    ChainStep(3, SquadRole.FINANCIAL,  "structure", "analyzed",         "structured"),
    ChainStep(4, SquadRole.BUILDER,    "build",     "structured",       "artifacts"),
    ChainStep(5, SquadRole.EXECUTIVE,  "synthesize","artifacts",        "final_scroll"),
]


# === REVERSE CLONE SIGNALS ===
# When a squad needs more data, it signals backward
REVERSE_SIGNALS = {
    SquadRole.COUNCIL:   SquadRole.INGESTION,   # Need more data? Re-scrape
    SquadRole.FINANCIAL: SquadRole.COUNCIL,      # Need more analysis? Re-reason
    SquadRole.BUILDER:   SquadRole.FINANCIAL,    # Need better structure? Re-format
    SquadRole.EXECUTIVE: SquadRole.BUILDER,      # Need better artifacts? Re-build
}


async def route_to_comet(prompt: str, task_type: str, model: str = "") -> dict:
    """Send a task to the Comet Router for model dispatch."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(
                f"{COMET_ROUTER}/route",
                json={
                    "prompt": prompt,
                    "task_type": task_type,
                    "model": model,
                    "max_tokens": 4096,
                }
            )
            return resp.json()
        except Exception as e:
            logger.error(f"[CHAIN] Comet Router error: {e}")
            return {"response": "", "provider": "error", "error": str(e)}


async def execute_step(step: ChainStep, task: ChainTask) -> bool:
    """Execute one step of the chain with the assigned squad."""
    squad_config = SQUAD_MODEL_ASSIGNMENTS[step.squad]
    model = squad_config["primary"]
    task_type = squad_config["task_types"][0]

    logger.info(f"[CHAIN] Step {step.step_num}/{len(SOVEREIGN_CHAIN)}: "
                f"{step.action} via {step.squad.value} -> {model}")

    task.current_squad = step.squad.value
    task.status = f"step_{step.step_num}_{step.action}"

    # Build prompt from previous step output
    input_data = task.results.get(step.input_key, task.intent)
    prompt = f"[ARK95X {step.action.upper()}] Operator: BEN_NORDSKOG\n"
    prompt += f"Task: {task.intent}\n"
    prompt += f"Input data: {json.dumps(input_data) if isinstance(input_data, dict) else str(input_data)}\n"
    prompt += f"Action: {step.action}\n"
    prompt += f"Output format: JSON with keys [summary, findings, actions, files_written, impact_score]"

    # Route through Comet
    result = await route_to_comet(prompt, task_type, model)

    if result.get("error") or not result.get("response"):
        # Try secondary model
        secondary = squad_config.get("secondary", "")
        if secondary:
            logger.warning(f"[CHAIN] Primary failed, trying secondary: {secondary}")
            result = await route_to_comet(prompt, task_type, secondary)

    # Store result
    task.results[step.output_key] = result.get("response", "")
    task.chain_log.append({
        "step": step.step_num,
        "squad": step.squad.value,
        "action": step.action,
        "model": result.get("model", model),
        "provider": result.get("provider", "unknown"),
        "elapsed": result.get("elapsed", 0),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "success": bool(result.get("response")),
    })

    return bool(result.get("response"))


async def reverse_clone(failed_step: ChainStep, task: ChainTask) -> bool:
    """Reverse signal: ask the previous squad to re-process with more context."""
    prev_squad = REVERSE_SIGNALS.get(failed_step.squad)
    if not prev_squad or task.retry_count >= task.max_retries:
        logger.error(f"[CHAIN] No reverse path or max retries hit for {failed_step.squad.value}")
        return False

    task.retry_count += 1
    logger.warning(f"[CHAIN] REVERSE CLONE: {failed_step.squad.value} -> {prev_squad.value} "
                   f"(retry {task.retry_count}/{task.max_retries})")

    # Find the step that corresponds to the previous squad
    for step in SOVEREIGN_CHAIN:
        if step.squad == prev_squad:
            return await execute_step(step, task)
    return False


async def run_chain(intent: str, task_type: str = "general", priority: int = 3) -> ChainTask:
    """Execute the full sovereign agent chain end-to-end."""
    task = ChainTask(
        task_id=f"CHAIN-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        intent=intent,
        task_type=task_type,
        priority=priority,
    )

    logger.info(f"[CHAIN] === SOVEREIGN CHAIN START === ID: {task.task_id}")
    logger.info(f"[CHAIN] Intent: {intent}")
    logger.info(f"[CHAIN] Squads: {' -> '.join(s.squad.value for s in SOVEREIGN_CHAIN)}")

    start_time = time.time()

    for step in SOVEREIGN_CHAIN:
        success = await execute_step(step, task)

        if not success:
            logger.warning(f"[CHAIN] Step {step.step_num} failed, attempting reverse clone...")
            reverse_ok = await reverse_clone(step, task)
            if reverse_ok:
                success = await execute_step(step, task)
            if not success:
                task.status = f"failed_at_step_{step.step_num}"
                logger.error(f"[CHAIN] Chain failed at step {step.step_num}: {step.action}")
                break
    else:
        task.status = "completed"

    elapsed = round(time.time() - start_time, 2)
    task.results["chain_elapsed"] = elapsed
    task.results["chain_status"] = task.status

    logger.info(f"[CHAIN] === CHAIN {task.status.upper()} === Elapsed: {elapsed}s")

    # Notify n8n webhook on completion
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(f"{N8N_WEBHOOK}/chain-complete", json={
                "task_id": task.task_id,
                "status": task.status,
                "elapsed": elapsed,
                "steps_completed": len(task.chain_log),
            })
    except Exception:
        pass  # Non-critical

    return task


def get_squad_status() -> dict:
    """Return current squad configuration and model assignments."""
    return {
        squad.value: {
            "models": config,
            "chain_position": next(
                (s.step_num for s in SOVEREIGN_CHAIN if s.squad == squad), None
            ),
        }
        for squad, config in SQUAD_MODEL_ASSIGNMENTS.items()
    }


# === CLI ENTRY POINT ===
if __name__ == "__main__":
    import sys
    intent = " ".join(sys.argv[1:]) or "System health check and status report"
    result = asyncio.run(run_chain(intent))
    print(json.dumps({
        "task_id": result.task_id,
        "status": result.status,
        "steps": len(result.chain_log),
        "chain_log": result.chain_log,
    }, indent=2))
