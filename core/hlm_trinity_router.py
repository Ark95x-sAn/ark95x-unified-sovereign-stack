"""
ARK95X HLM Trinity Stack Router
================================
Production-ready FastAPI service implementing the HLM Trinity Stack model
routing system for 27 AI models across 5 tiers with Obelisk 9R Brain mapping.

Architecture:
    H (Head)    — Reasoning/planning: Claude Opus, o3, Grok, Perplexity
    L (Lateral) — Parallel processing: Sonar, GPT-4o, Ollama, Merlin, Monica
    M (Motor)   — Execution: Codex, CrewAI, n8n, Copilot, Manus, GitHub Actions

Port: 8095
"""

from __future__ import annotations

import os
import re
import time
import asyncio
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import httpx
import yaml
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONFIG_PATH = Path(__file__).parent / "hlm_config.yaml"
APP_PORT = int(os.getenv("HLM_ROUTER_PORT", "8095"))
FLAME_DEFAULT = "sovereign"

# API keys from environment
API_KEYS: dict[str, str | None] = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
    "XAI_API_KEY": os.getenv("XAI_API_KEY"),
    "PERPLEXITY_API_KEY": os.getenv("PERPLEXITY_API_KEY"),
}

START_TIME = time.time()


def _load_config() -> dict[str, Any]:
    """Load the HLM configuration from YAML."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f)
    logger.warning(f"Config not found at {CONFIG_PATH}, using defaults")
    return {}


CONFIG = _load_config()

# ---------------------------------------------------------------------------
# Enums & Constants
# ---------------------------------------------------------------------------


class HLMTier(str, Enum):
    HEAD = "head"
    LATERAL = "lateral"
    MOTOR = "motor"


class ObeliskFunction(str, Enum):
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    STRATEGY = "strategy"
    CREATIVITY = "creativity"
    EXECUTION = "execution"
    MEMORY = "memory"
    PREDICTION = "prediction"
    COMMUNICATION = "communication"
    INTEGRATION = "integration"


class ModelStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


# Classification patterns — keyword → (obelisk_function, hlm_tier)
CLASSIFICATION_RULES: list[tuple[list[str], ObeliskFunction, HLMTier]] = [
    (
        ["code", "build", "deploy", "fix", "implement", "run", "execute",
         "compile", "test", "debug", "push", "commit"],
        ObeliskFunction.EXECUTION, HLMTier.MOTOR,
    ),
    (
        ["research", "find", "search", "compare", "forecast", "predict",
         "trend", "investigate", "discover"],
        ObeliskFunction.PREDICTION, HLMTier.LATERAL,
    ),
    (
        ["plan", "strategy", "decide", "evaluate", "assess", "prioritize",
         "roadmap", "architect"],
        ObeliskFunction.STRATEGY, HLMTier.HEAD,
    ),
    (
        ["write", "draft", "email", "communicate", "message", "respond",
         "compose", "announce"],
        ObeliskFunction.COMMUNICATION, HLMTier.LATERAL,
    ),
    (
        ["create", "design", "brainstorm", "imagine", "innovate", "generate",
         "invent", "concept"],
        ObeliskFunction.CREATIVITY, HLMTier.HEAD,
    ),
    (
        ["analyze", "review", "audit", "check", "inspect", "examine",
         "diagnose"],
        ObeliskFunction.ANALYSIS, HLMTier.HEAD,
    ),
    (
        ["summarize", "combine", "merge", "synthesize", "consolidate",
         "aggregate", "unify"],
        ObeliskFunction.SYNTHESIS, HLMTier.LATERAL,
    ),
    (
        ["remember", "store", "recall", "log", "archive", "save", "document",
         "record"],
        ObeliskFunction.MEMORY, HLMTier.MOTOR,
    ),
    (
        ["connect", "integrate", "wire", "sync", "link", "bridge",
         "orchestrate", "pipeline"],
        ObeliskFunction.INTEGRATION, HLMTier.HEAD,
    ),
]

# Obelisk 9R → model IDs mapping (from config or hardcoded fallback)
OBELISK_MODEL_MAP: dict[ObeliskFunction, list[str]] = {
    ObeliskFunction.ANALYSIS: ["claude_pro", "chatgpt_pro"],
    ObeliskFunction.SYNTHESIS: ["chatgpt_pro", "claude_pro"],
    ObeliskFunction.STRATEGY: ["chatgpt_pro", "claude_pro"],
    ObeliskFunction.CREATIVITY: ["chatgpt_pro", "grok_xai"],
    ObeliskFunction.EXECUTION: ["codex", "crewai", "n8n"],
    ObeliskFunction.MEMORY: ["notion", "github"],
    ObeliskFunction.PREDICTION: ["perplexity_comet", "chatgpt_pro", "grok_xai"],
    ObeliskFunction.COMMUNICATION: ["chatgpt_pro", "claude_pro"],
    ObeliskFunction.INTEGRATION: ["claude_pro", "chatgpt_pro"],
}

# Head-tier models eligible for council consensus
COUNCIL_MODELS = ["claude_pro", "chatgpt_pro", "grok_xai", "perplexity_comet"]

# Flame signature allowlist
FLAME_ALLOWLIST: set[str] = set(
    CONFIG.get("flame_signatures", {}).get("allowlist", ["sovereign", "ark95x"])
)

# Question loop templates
QUESTION_LOOP_TEMPLATES: list[str] = CONFIG.get("question_loop", {}).get(
    "templates",
    [
        "Did this answer the actual question?",
        "What was missed?",
        "What adjacent insight exists?",
        "Should this feed into the knowledge graph?",
    ],
)

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class TaskInput(BaseModel):
    """Incoming task for classification or routing."""
    task: str = Field(..., min_length=1, description="Task description")
    context: str = Field("", description="Additional context")
    priority: int = Field(3, ge=1, le=5, description="Priority 1 (highest) to 5")
    force_model: str | None = Field(None, description="Force a specific model ID")
    force_tier: HLMTier | None = Field(None, description="Force a specific HLM tier")


class ClassificationResult(BaseModel):
    """Result of task classification."""
    task: str
    obelisk_function: ObeliskFunction
    hlm_tier: HLMTier
    recommended_models: list[str]
    confidence: float
    keywords_matched: list[str]
    question_loop: list[str]


class RoutingResult(BaseModel):
    """Result of task routing to a model."""
    task: str
    routed_to: str
    hlm_tier: HLMTier
    obelisk_function: ObeliskFunction
    model_response: str
    elapsed_seconds: float
    fallback_used: bool = False
    question_loop: list[str]


class ModelInfo(BaseModel):
    """Model registry entry for API responses."""
    id: str
    name: str
    tier: int
    tier_name: str
    hlm_role: str
    endpoint: str
    capabilities: list[str]
    status: ModelStatus = ModelStatus.UNKNOWN


class ModelHealthEntry(BaseModel):
    """Health status for a single model."""
    id: str
    name: str
    status: ModelStatus
    latency_ms: float | None = None
    error: str | None = None


class HealthDashboard(BaseModel):
    """Aggregated health of all model endpoints."""
    status: str
    total_models: int
    online: int
    offline: int
    degraded: int
    unknown: int
    uptime_seconds: float
    timestamp: str
    models: list[ModelHealthEntry]


class CouncilRequest(BaseModel):
    """Request for multi-model council consensus."""
    task: str = Field(..., min_length=1)
    context: str = ""
    council_models: list[str] | None = Field(
        None, description="Override default council models"
    )


class CouncilVote(BaseModel):
    """A single council member's response."""
    model_id: str
    response: str
    confidence: float
    elapsed_seconds: float
    error: str | None = None


class CouncilResult(BaseModel):
    """Synthesized consensus from multiple Head models."""
    task: str
    votes: list[CouncilVote]
    consensus: str
    agreement_score: float
    question_loop: list[str]


# ---------------------------------------------------------------------------
# Model Registry
# ---------------------------------------------------------------------------


class ModelRegistry:
    """In-memory registry of all 27 models loaded from config."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.models: dict[str, dict[str, Any]] = {}
        raw_models = config.get("models", {})
        for model_id, model_data in raw_models.items():
            model_data["id"] = model_id
            self.models[model_id] = model_data
        logger.info(f"ModelRegistry loaded {len(self.models)} models")

    def get(self, model_id: str) -> dict[str, Any] | None:
        return self.models.get(model_id)

    def list_all(self) -> list[ModelInfo]:
        result = []
        for mid, m in self.models.items():
            result.append(
                ModelInfo(
                    id=mid,
                    name=m.get("name", mid),
                    tier=m.get("tier", 0),
                    tier_name=m.get("tier_name", "Unknown"),
                    hlm_role=m.get("hlm_role", "unknown"),
                    endpoint=m.get("endpoint", ""),
                    capabilities=m.get("capabilities", []),
                )
            )
        return sorted(result, key=lambda x: (x.tier, x.id))

    def by_tier(self, hlm_tier: HLMTier) -> list[str]:
        return [
            mid for mid, m in self.models.items()
            if m.get("hlm_role") == hlm_tier.value
        ]

    def by_obelisk(self, function: ObeliskFunction) -> list[str]:
        return OBELISK_MODEL_MAP.get(function, [])


REGISTRY = ModelRegistry(CONFIG)

# ---------------------------------------------------------------------------
# Task Classifier
# ---------------------------------------------------------------------------


def classify_task(task: str) -> tuple[ObeliskFunction, HLMTier, float, list[str]]:
    """Classify a task into an Obelisk 9R function and HLM tier.

    Returns (function, tier, confidence, matched_keywords).
    """
    task_lower = task.lower()
    best_function = ObeliskFunction.ANALYSIS
    best_tier = HLMTier.HEAD
    best_score = 0
    best_keywords: list[str] = []

    for keywords, function, tier in CLASSIFICATION_RULES:
        matched = [kw for kw in keywords if re.search(rf"\b{kw}\b", task_lower)]
        score = len(matched)
        if score > best_score:
            best_score = score
            best_function = function
            best_tier = tier
            best_keywords = matched

    # Confidence: scale by how many keywords matched vs total possible
    max_keywords = max(len(rule[0]) for rule in CLASSIFICATION_RULES)
    confidence = min(1.0, best_score / max(max_keywords / 2, 1))
    if best_score == 0:
        confidence = 0.3  # default low confidence for unmatched tasks

    return best_function, best_tier, round(confidence, 3), best_keywords


# ---------------------------------------------------------------------------
# Model Interaction Helpers
# ---------------------------------------------------------------------------


async def _call_openai_compatible(
    endpoint: str,
    api_key: str | None,
    model: str,
    prompt: str,
    timeout: float = 60.0,
) -> str:
    """Call an OpenAI-compatible API (OpenAI, xAI, etc.)."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{endpoint}/chat/completions", headers=headers, json=payload
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def _call_anthropic(
    api_key: str | None,
    model: str,
    prompt: str,
    timeout: float = 60.0,
) -> str:
    """Call the Anthropic API."""
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}],
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages", headers=headers, json=payload
        )
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]


async def _call_ollama(
    model: str,
    prompt: str,
    endpoint: str = "http://localhost:11434",
    timeout: float = 120.0,
) -> str:
    """Call a local Ollama model."""
    payload = {"model": model, "prompt": prompt, "stream": False}
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(f"{endpoint}/api/generate", json=payload)
        resp.raise_for_status()
        return resp.json().get("response", "")


async def _call_perplexity(
    api_key: str | None,
    prompt: str,
    mode: str = "pro_search",
    timeout: float = 60.0,
) -> str:
    """Call the Perplexity API."""
    if not api_key:
        raise ValueError("PERPLEXITY_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    model_map = {
        "pro_search": "sonar-pro",
        "deep_research": "sonar-deep-research",
        "spaces": "sonar",
    }
    payload = {
        "model": model_map.get(mode, "sonar-pro"),
        "messages": [{"role": "user", "content": prompt}],
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def route_to_model(model_id: str, prompt: str) -> str:
    """Route a prompt to a specific model and return its response."""
    model_cfg = REGISTRY.get(model_id)
    if not model_cfg:
        raise ValueError(f"Unknown model: {model_id}")

    endpoint = model_cfg.get("endpoint", "")
    api_key_env = model_cfg.get("api_key_env")
    api_key = os.getenv(api_key_env) if api_key_env else None
    default_model = model_cfg.get("default_model", model_id)

    # Route to the appropriate API
    if model_id == "claude_pro":
        return await _call_anthropic(api_key, default_model, prompt)
    elif model_id in ("chatgpt_pro", "codex"):
        return await _call_openai_compatible(endpoint, api_key, default_model, prompt)
    elif model_id == "grok_xai":
        return await _call_openai_compatible(endpoint, api_key, default_model, prompt)
    elif model_id == "perplexity_comet":
        return await _call_perplexity(api_key, prompt)
    elif model_id.startswith("ollama_"):
        return await _call_ollama(default_model, prompt, endpoint)
    elif model_id == "gpt4all":
        return await _call_openai_compatible(
            endpoint, None, default_model, prompt, timeout=120.0
        )
    elif endpoint in ("internal", "system_native", "browser_extension"):
        return (
            f"[{model_id}] Task queued for {model_cfg.get('name', model_id)}. "
            f"This model operates via {endpoint} and cannot be called directly via API."
        )
    else:
        # For platform models (Notion, GitHub, etc.) — return a delegation notice
        return (
            f"[{model_id}] Task delegated to {model_cfg.get('name', model_id)} "
            f"platform integration at {endpoint}."
        )


async def check_model_health(model_id: str) -> ModelHealthEntry:
    """Check the health of a single model endpoint."""
    model_cfg = REGISTRY.get(model_id)
    if not model_cfg:
        return ModelHealthEntry(
            id=model_id, name=model_id,
            status=ModelStatus.UNKNOWN, error="Not in registry",
        )

    endpoint = model_cfg.get("endpoint", "")
    name = model_cfg.get("name", model_id)

    # Non-HTTP endpoints
    if endpoint in ("internal", "system_native", "browser_extension"):
        return ModelHealthEntry(id=model_id, name=name, status=ModelStatus.UNKNOWN)

    # Check HTTP endpoints
    health_url = endpoint
    if "localhost:11434" in endpoint:
        health_url = f"{endpoint}/api/tags"
    elif "localhost:1000" in endpoint:
        health_url = f"{endpoint}/health"
    elif "localhost" in endpoint:
        health_url = endpoint

    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(health_url)
            latency = round((time.time() - start) * 1000, 1)
            if resp.status_code < 400:
                return ModelHealthEntry(
                    id=model_id, name=name,
                    status=ModelStatus.ONLINE, latency_ms=latency,
                )
            return ModelHealthEntry(
                id=model_id, name=name,
                status=ModelStatus.DEGRADED, latency_ms=latency,
                error=f"HTTP {resp.status_code}",
            )
    except httpx.ConnectError:
        return ModelHealthEntry(
            id=model_id, name=name, status=ModelStatus.OFFLINE,
            error="Connection refused",
        )
    except Exception as e:
        return ModelHealthEntry(
            id=model_id, name=name, status=ModelStatus.OFFLINE,
            error=str(e)[:200],
        )


# ---------------------------------------------------------------------------
# Flame Signature Validation
# ---------------------------------------------------------------------------


def validate_flame_signature(signature: str | None) -> str:
    """Validate the Flame Signature header. Returns the validated signature."""
    sig = signature or FLAME_DEFAULT
    if sig not in FLAME_ALLOWLIST:
        raise HTTPException(
            status_code=403,
            detail=f"Invalid Flame Signature: '{sig}'. Not in allowlist.",
        )
    return sig


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------


app = FastAPI(
    title="ARK95X HLM Trinity Router",
    description=(
        "HLM Trinity Stack model routing for 27 AI models across 5 tiers. "
        "Obelisk 9R Brain cognitive function mapping."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app)
except ImportError:
    logger.debug("prometheus-fastapi-instrumentator not installed, skipping metrics")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, Any]:
    """Basic health check for the router itself."""
    return {
        "status": "operational",
        "service": "hlm_trinity_router",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "models_registered": len(REGISTRY.models),
    }


@app.post("/router/classify", response_model=ClassificationResult)
async def classify_endpoint(
    body: TaskInput,
    x_flame_signature: str | None = Header(None),
) -> ClassificationResult:
    """Classify a task into an Obelisk 9R function and recommend models."""
    validate_flame_signature(x_flame_signature)

    obelisk_fn, hlm_tier, confidence, keywords = classify_task(body.task)

    # If user forced a tier, override
    if body.force_tier:
        hlm_tier = body.force_tier

    # Get recommended models
    recommended = OBELISK_MODEL_MAP.get(obelisk_fn, [])
    if body.force_model:
        recommended = [body.force_model] + [
            m for m in recommended if m != body.force_model
        ]

    return ClassificationResult(
        task=body.task,
        obelisk_function=obelisk_fn,
        hlm_tier=hlm_tier,
        recommended_models=recommended,
        confidence=confidence,
        keywords_matched=keywords,
        question_loop=QUESTION_LOOP_TEMPLATES,
    )


@app.post("/router/route", response_model=RoutingResult)
async def route_endpoint(
    body: TaskInput,
    x_flame_signature: str | None = Header(None),
) -> RoutingResult:
    """Route a task to the best available model and return results."""
    validate_flame_signature(x_flame_signature)

    obelisk_fn, hlm_tier, confidence, keywords = classify_task(body.task)

    if body.force_tier:
        hlm_tier = body.force_tier

    # Determine target model
    if body.force_model:
        target_models = [body.force_model]
    else:
        target_models = OBELISK_MODEL_MAP.get(obelisk_fn, [])

    if not target_models:
        raise HTTPException(
            status_code=400,
            detail=f"No models available for {obelisk_fn.value}",
        )

    # Try each model in order, with fallback
    fallback_used = False
    last_error = ""
    for i, model_id in enumerate(target_models):
        if i > 0:
            fallback_used = True
        start = time.time()
        try:
            prompt = body.task
            if body.context:
                prompt = f"Context: {body.context}\n\nTask: {body.task}"
            response = await route_to_model(model_id, prompt)
            elapsed = round(time.time() - start, 3)
            return RoutingResult(
                task=body.task,
                routed_to=model_id,
                hlm_tier=hlm_tier,
                obelisk_function=obelisk_fn,
                model_response=response,
                elapsed_seconds=elapsed,
                fallback_used=fallback_used,
                question_loop=QUESTION_LOOP_TEMPLATES,
            )
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Model {model_id} failed: {last_error}")
            continue

    raise HTTPException(
        status_code=503,
        detail=f"All models exhausted for {obelisk_fn.value}. Last error: {last_error}",
    )


@app.get("/router/models", response_model=list[ModelInfo])
async def list_models(
    x_flame_signature: str | None = Header(None),
) -> list[ModelInfo]:
    """List all 27 models with tier, status, capabilities, and endpoints."""
    validate_flame_signature(x_flame_signature)
    return REGISTRY.list_all()


@app.get("/router/health", response_model=HealthDashboard)
async def health_dashboard(
    x_flame_signature: str | None = Header(None),
) -> HealthDashboard:
    """Aggregated health check of all model endpoints."""
    validate_flame_signature(x_flame_signature)

    # Check all models concurrently
    tasks = [
        check_model_health(model_id) for model_id in REGISTRY.models
    ]
    results: list[ModelHealthEntry] = await asyncio.gather(*tasks)

    online = sum(1 for r in results if r.status == ModelStatus.ONLINE)
    offline = sum(1 for r in results if r.status == ModelStatus.OFFLINE)
    degraded = sum(1 for r in results if r.status == ModelStatus.DEGRADED)
    unknown = sum(1 for r in results if r.status == ModelStatus.UNKNOWN)

    if online == len(results):
        overall = "healthy"
    elif offline == len(results):
        overall = "critical"
    elif online > 0:
        overall = "degraded"
    else:
        overall = "unknown"

    return HealthDashboard(
        status=overall,
        total_models=len(results),
        online=online,
        offline=offline,
        degraded=degraded,
        unknown=unknown,
        uptime_seconds=round(time.time() - START_TIME, 2),
        timestamp=datetime.now(timezone.utc).isoformat(),
        models=results,
    )


@app.post("/router/council", response_model=CouncilResult)
async def council_endpoint(
    body: CouncilRequest,
    x_flame_signature: str | None = Header(None),
) -> CouncilResult:
    """Send task to multiple Head models and return synthesized consensus."""
    validate_flame_signature(x_flame_signature)

    council = body.council_models or COUNCIL_MODELS

    # Query all council models concurrently
    async def _get_vote(model_id: str) -> CouncilVote:
        start = time.time()
        try:
            prompt = body.task
            if body.context:
                prompt = f"Context: {body.context}\n\nTask: {body.task}"
            response = await route_to_model(model_id, prompt)
            elapsed = round(time.time() - start, 3)
            return CouncilVote(
                model_id=model_id,
                response=response,
                confidence=0.8,
                elapsed_seconds=elapsed,
            )
        except Exception as e:
            elapsed = round(time.time() - start, 3)
            return CouncilVote(
                model_id=model_id,
                response="",
                confidence=0.0,
                elapsed_seconds=elapsed,
                error=str(e)[:300],
            )

    votes = await asyncio.gather(*[_get_vote(m) for m in council])
    votes_list = list(votes)

    # Synthesize consensus from successful votes
    successful_votes = [v for v in votes_list if not v.error and v.response]
    if successful_votes:
        consensus_parts = []
        for v in successful_votes:
            consensus_parts.append(f"[{v.model_id}]: {v.response[:500]}")
        consensus = (
            f"Council consensus from {len(successful_votes)}/{len(council)} models:\n\n"
            + "\n\n---\n\n".join(consensus_parts)
        )
        agreement = round(len(successful_votes) / len(council), 2)
    else:
        consensus = "No council members responded successfully."
        agreement = 0.0

    return CouncilResult(
        task=body.task,
        votes=votes_list,
        consensus=consensus,
        agreement_score=agreement,
        question_loop=QUESTION_LOOP_TEMPLATES,
    )


@app.get("/router/tiers")
async def list_tiers(
    x_flame_signature: str | None = Header(None),
) -> dict[str, Any]:
    """List all HLM tiers and their models."""
    validate_flame_signature(x_flame_signature)
    hlm_tiers = CONFIG.get("hlm_tiers", {})
    return {
        "tiers": hlm_tiers,
        "obelisk_9r": {
            fn.value: OBELISK_MODEL_MAP[fn] for fn in ObeliskFunction
        },
    }


@app.get("/router/obelisk")
async def obelisk_map(
    x_flame_signature: str | None = Header(None),
) -> dict[str, Any]:
    """Return the full Obelisk 9R Brain mapping."""
    validate_flame_signature(x_flame_signature)
    return {
        "obelisk_9r": {
            fn.value: {
                "models": OBELISK_MODEL_MAP[fn],
                "description": CONFIG.get("obelisk_9r", {})
                .get(fn.value, {})
                .get("description", ""),
            }
            for fn in ObeliskFunction
        },
    }


# ---------------------------------------------------------------------------
# Startup Logging
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def startup_log() -> None:
    logger.info("=" * 60)
    logger.info("ARK95X HLM Trinity Router starting")
    logger.info(f"  Models registered: {len(REGISTRY.models)}")
    logger.info(f"  Port: {APP_PORT}")
    logger.info(f"  Flame signatures: {FLAME_ALLOWLIST}")
    logger.info("=" * 60)

    for tier_name in ["head", "lateral", "motor"]:
        models = REGISTRY.by_tier(HLMTier(tier_name))
        logger.info(f"  {tier_name.upper()} tier: {len(models)} models — {models}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "core.hlm_trinity_router:app",
        host="0.0.0.0",
        port=APP_PORT,
        reload=True,
        log_level="info",
    )
