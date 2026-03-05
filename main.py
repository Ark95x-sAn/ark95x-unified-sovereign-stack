"""ARK95X Unified Sovereign Stack - Core API"""
import os
import time
import httpx
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

# Config
APP_PORT = int(os.getenv("APP_PORT", 8000))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
POSTGRES_URL = os.getenv("POSTGRES_URL", "")
MONGODB_URL = os.getenv("MONGODB_URL", "")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
N8N_URL = os.getenv("N8N_URL", "http://localhost:5678")

START_TIME = time.time()

# Models
class HealthResponse(BaseModel):
    status: str
    uptime: float
    timestamp: str
    services: dict
    version: str = "1.0.0"

class QueryRequest(BaseModel):
    prompt: str
    model: str = "llama3"
    context: str = ""

class QueryResponse(BaseModel):
    response: str
    model: str
    elapsed: float

# Service health checks
async def check_service(url: str, name: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(url)
            return {"name": name, "status": "healthy" if r.status_code < 400 else "unhealthy", "code": r.status_code}
    except Exception as e:
        return {"name": name, "status": "unreachable", "error": str(e)}

# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ARK95X Sovereign Stack starting...")
    logger.info(f"Ollama: {OLLAMA_HOST}")
    logger.info(f"Redis: {REDIS_URL}")
    logger.info(f"Postgres: {POSTGRES_URL[:30]}..." if POSTGRES_URL else "Postgres: not configured")
    logger.info(f"Qdrant: {QDRANT_URL}")
    logger.info(f"n8n: {N8N_URL}")
    yield
    logger.info("ARK95X Sovereign Stack shutting down")

# App
app = FastAPI(
    title="ARK95X Unified Sovereign Stack",
    description="All repositories. One united front. Total sovereign integration.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app)
except ImportError:
    logger.warning("prometheus-fastapi-instrumentator not available")

@app.get("/")
async def root():
    return {
        "name": "ARK95X Unified Sovereign Stack",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoints": {
            "health": "/health",
            "query": "/api/query",
            "models": "/api/models",
            "services": "/api/services",
            "docs": "/docs",
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health():
    services = {}
    checks = [
        (f"{OLLAMA_HOST}/api/tags", "ollama"),
        (f"{QDRANT_URL}/health", "qdrant"),
        (f"{N8N_URL}", "n8n"),
    ]
    for url, name in checks:
        result = await check_service(url, name)
        services[name] = result["status"]
    all_healthy = all(s == "healthy" for s in services.values())
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        uptime=round(time.time() - START_TIME, 2),
        timestamp=datetime.now(timezone.utc).isoformat(),
        services=services,
    )

@app.get("/api/models")
async def list_models():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{OLLAMA_HOST}/api/tags")
            return r.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ollama unreachable: {e}")

@app.post("/api/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    start = time.time()
    try:
        payload = {
            "model": req.model,
            "prompt": req.prompt,
            "stream": False,
        }
        if req.context:
            payload["system"] = req.context
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
            data = r.json()
            return QueryResponse(
                response=data.get("response", ""),
                model=req.model,
                elapsed=round(time.time() - start, 2),
            )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Query failed: {e}")

@app.get("/api/services")
async def services_status():
    checks = [
        (f"{OLLAMA_HOST}/api/tags", "ollama"),
        (f"{QDRANT_URL}/health", "qdrant"),
        (f"{N8N_URL}", "n8n"),
    ]
    results = []
    for url, name in checks:
        results.append(await check_service(url, name))
    return {"services": results, "timestamp": datetime.now(timezone.utc).isoformat()}

if __name__ == "__main__":
    import sys
    if "--check" in sys.argv:
        print("ARK95X Sovereign Stack: All modules loaded successfully.")
        print(f"FastAPI app '{app.title}' v{app.version} ready.")
        sys.exit(0)
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=APP_PORT, reload=True, log_level="info")
