"""ARK95X Comet Router - Port 8100
Task classification, model routing, and multi-provider AI orchestration.
Routes to Ollama (local), OpenAI, Anthropic, or Groq based on task type and load.
"""
import os
import time
import hashlib
from datetime import datetime, timezone
from enum import Enum
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger
import httpx

# === CONFIG ===
ROUTER_PORT = int(os.getenv("COMET_ROUTER_PORT", 8100))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# === TASK CLASSIFICATION ===
class TaskType(str, Enum):
    GENERAL = "general"
    CODE = "code"
    ANALYSIS = "analysis"
    RESEARCH = "research"
    CREATIVE = "creative"
    LITIGATION = "litigation"
    BUSINESS_OPS = "business_ops"

class ModelProvider(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"

# Task -> preferred provider routing table
ROUTING_TABLE = {
    TaskType.GENERAL: [ModelProvider.OLLAMA, ModelProvider.GROQ],
    TaskType.CODE: [ModelProvider.ANTHROPIC, ModelProvider.OLLAMA],
    TaskType.ANALYSIS: [ModelProvider.OPENAI, ModelProvider.ANTHROPIC],
    TaskType.RESEARCH: [ModelProvider.OPENAI, ModelProvider.OLLAMA],
    TaskType.CREATIVE: [ModelProvider.ANTHROPIC, ModelProvider.OPENAI],
    TaskType.LITIGATION: [ModelProvider.ANTHROPIC, ModelProvider.OPENAI],
    TaskType.BUSINESS_OPS: [ModelProvider.OLLAMA, ModelProvider.GROQ],
}

# Provider -> default model
MODEL_DEFAULTS = {
    ModelProvider.OLLAMA: "llama3",
    ModelProvider.OPENAI: "gpt-4o",
    ModelProvider.ANTHROPIC: "claude-sonnet-4-20250514",
    ModelProvider.GROQ: "llama-3.3-70b-versatile",
}

# === MODELS ===
class RouteRequest(BaseModel):
    prompt: str
    task_type: str = "general"
    model: str = ""
    provider: str = ""
    context: str = ""
    max_tokens: int = 2048
    council_vote: bool = False

class RouteResponse(BaseModel):
    response: str
    provider: str
    model: str
    task_type: str
    elapsed: float
    route_hash: str

# === APP ===
app = FastAPI(
    title="ARK95X Comet Router",
    description="Multi-provider AI model routing and task classification",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# === TASK CLASSIFIER ===
TASK_KEYWORDS = {
    TaskType.CODE: ["code", "function", "debug", "python", "javascript", "api", "deploy", "docker", "git"],
    TaskType.ANALYSIS: ["analyze", "compare", "evaluate", "metrics", "data", "statistics", "trend"],
    TaskType.RESEARCH: ["research", "find", "search", "investigate", "discover", "study"],
    TaskType.CREATIVE: ["write", "create", "design", "story", "poem", "generate", "imagine"],
    TaskType.LITIGATION: ["legal", "court", "litigation", "foreclosure", "filing", "motion", "statute", "iowa"],
    TaskType.BUSINESS_OPS: ["restaurant", "schedule", "inventory", "revenue", "employee", "pos", "toast"],
}

def classify_task(prompt: str) -> TaskType:
    prompt_lower = prompt.lower()
    scores = {}
    for task_type, keywords in TASK_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in prompt_lower)
        if score > 0:
            scores[task_type] = score
    if scores:
        return max(scores, key=scores.get)
    return TaskType.GENERAL

def select_provider(task_type: TaskType, preferred: str = "") -> tuple:
    if preferred and preferred in ModelProvider.__members__.values():
        return ModelProvider(preferred), MODEL_DEFAULTS.get(ModelProvider(preferred), "llama3")
    providers = ROUTING_TABLE.get(task_type, [ModelProvider.OLLAMA])
    for provider in providers:
        if provider == ModelProvider.OPENAI and not OPENAI_API_KEY:
            continue
        if provider == ModelProvider.ANTHROPIC and not ANTHROPIC_API_KEY:
            continue
        if provider == ModelProvider.GROQ and not GROQ_API_KEY:
            continue
        return provider, MODEL_DEFAULTS[provider]
    return ModelProvider.OLLAMA, "llama3"

# === PROVIDER CALLS ===
async def call_ollama(prompt: str, model: str, context: str, max_tokens: int) -> str:
    payload = {"model": model, "prompt": prompt, "stream": False}
    if context:
        payload["system"] = context
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
        return r.json().get("response", "")

async def call_openai(prompt: str, model: str, context: str, max_tokens: int) -> str:
    messages = []
    if context:
        messages.append({"role": "system", "content": context})
    messages.append({"role": "user", "content": prompt})
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": model, "messages": messages, "max_tokens": max_tokens},
        )
        data = r.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")

async def call_anthropic(prompt: str, model: str, context: str, max_tokens: int) -> str:
    messages = [{"role": "user", "content": prompt}]
    body = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if context:
        body["system"] = context
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"},
            json=body,
        )
        data = r.json()
        return data.get("content", [{}])[0].get("text", "")

async def call_groq(prompt: str, model: str, context: str, max_tokens: int) -> str:
    messages = []
    if context:
        messages.append({"role": "system", "content": context})
    messages.append({"role": "user", "content": prompt})
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={"model": model, "messages": messages, "max_tokens": max_tokens},
        )
        data = r.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")

PROVIDER_HANDLERS = {
    ModelProvider.OLLAMA: call_ollama,
    ModelProvider.OPENAI: call_openai,
    ModelProvider.ANTHROPIC: call_anthropic,
    ModelProvider.GROQ: call_groq,
}

# === ENDPOINTS ===
@app.get("/health")
async def health():
    return {
        "service": "comet_router",
        "status": "operational",
        "port": ROUTER_PORT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "providers": {
            "ollama": bool(OLLAMA_HOST),
            "openai": bool(OPENAI_API_KEY),
            "anthropic": bool(ANTHROPIC_API_KEY),
            "groq": bool(GROQ_API_KEY),
        },
    }

@app.post("/route", response_model=RouteResponse)
async def route_request(req: RouteRequest):
    start = time.time()
    task_type = TaskType(req.task_type) if req.task_type in TaskType.__members__.values() else classify_task(req.prompt)
    provider, model = select_provider(task_type, req.provider)
    if req.model:
        model = req.model

    logger.info(f"[COMET] task={task_type.value} provider={provider.value} model={model}")

    handler = PROVIDER_HANDLERS.get(provider)
    if not handler:
        raise HTTPException(503, f"No handler for provider: {provider}")

    try:
        response_text = await handler(req.prompt, model, req.context, req.max_tokens)
    except Exception as e:
        logger.error(f"[COMET] Provider {provider.value} failed: {e}")
        if provider != ModelProvider.OLLAMA:
            logger.info("[COMET] Falling back to Ollama")
            response_text = await call_ollama(req.prompt, "llama3", req.context, req.max_tokens)
            provider = ModelProvider.OLLAMA
            model = "llama3"
        else:
            raise HTTPException(503, f"All providers failed: {e}")

    elapsed = round(time.time() - start, 2)
    route_hash = hashlib.sha256(f"{task_type}{provider}{model}{elapsed}".encode()).hexdigest()[:12]

    return RouteResponse(
        response=response_text,
        provider=provider.value,
        model=model,
        task_type=task_type.value,
        elapsed=elapsed,
        route_hash=route_hash,
    )

@app.post("/classify")
async def classify_only(prompt: str = ""):
    task_type = classify_task(prompt)
    provider, model = select_provider(task_type)
    return {"task_type": task_type.value, "recommended_provider": provider.value, "recommended_model": model}

@app.get("/providers")
async def list_providers():
    return {
        "providers": {
            "ollama": {"available": True, "host": OLLAMA_HOST},
            "openai": {"available": bool(OPENAI_API_KEY)},
            "anthropic": {"available": bool(ANTHROPIC_API_KEY)},
            "groq": {"available": bool(GROQ_API_KEY)},
        },
        "routing_table": {k.value: [p.value for p in v] for k, v in ROUTING_TABLE.items()},
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("comet_router:app", host="0.0.0.0", port=ROUTER_PORT, reload=True)
