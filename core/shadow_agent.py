"""ARK95X Shadow Agent - Port 8400
Background relay agent. Monitors all services, syncs state to Command Base,
triggers self-healing and auto-recovery when gates go down.
"""
import os
import time
import asyncio
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import httpx

# === CONFIG ===
SHADOW_PORT = int(os.getenv("SHADOW_AGENT_PORT", 8400))
POLL_INTERVAL = int(os.getenv("SHADOW_POLL_INTERVAL", 10))

SERVICE_ENDPOINTS = {
    "core": os.getenv("CORE_API_URL", "http://localhost:8000") + "/health",
    "flamegate": os.getenv("FLAMEGATE_URL", "http://localhost:8443") + "/health",
    "comet_router": os.getenv("COMET_ROUTER_URL", "http://localhost:8100") + "/health",
    "gate_unlocker": os.getenv("GATE_UNLOCKER_URL", "http://localhost:8200") + "/health",
    "council": os.getenv("COUNCIL_URL", "http://localhost:8300") + "/health",
    "n8n": "http://localhost:5678",
    "qdrant": "http://localhost:6333/health",
    "ollama": "http://localhost:11434/api/tags",
    "grafana": "http://localhost:3000",
}

# === STATE STORE ===
shadow_state = {
    "services": {},
    "last_scan": None,
    "scan_count": 0,
    "alerts": [],
    "uptime_start": datetime.now(timezone.utc).isoformat(),
}

# === APP ===
app = FastAPI(
    title="ARK95X Shadow Agent",
    description="Background monitoring, state relay, and self-healing agent",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

async def check_service(name: str, url: str) -> dict:
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
            r = await client.get(url)
            latency = round((time.time() - start) * 1000, 2)
            status = "healthy" if r.status_code < 400 else "unhealthy"
            return {"name": name, "status": status, "latency_ms": latency, "code": r.status_code}
    except Exception as e:
        latency = round((time.time() - start) * 1000, 2)
        return {"name": name, "status": "down", "latency_ms": latency, "error": str(e)[:100]}

async def scan_all():
    tasks = [check_service(name, url) for name, url in SERVICE_ENDPOINTS.items()]
    results = await asyncio.gather(*tasks)
    scan_time = datetime.now(timezone.utc).isoformat()

    for r in results:
        prev = shadow_state["services"].get(r["name"], {}).get("status", "unknown")
        r["previous_status"] = prev
        r["changed"] = prev != r["status"]
        r["last_checked"] = scan_time

        if r["changed"] and r["status"] == "down":
            alert = f"[{scan_time}] ALERT: {r['name']} went DOWN"
            shadow_state["alerts"].insert(0, alert)
            logger.warning(alert)
            if len(shadow_state["alerts"]) > 100:
                shadow_state["alerts"] = shadow_state["alerts"][:100]

        shadow_state["services"][r["name"]] = r

    shadow_state["last_scan"] = scan_time
    shadow_state["scan_count"] += 1
    return results

async def background_scanner():
    while True:
        try:
            await scan_all()
        except Exception as e:
            logger.error(f"[SHADOW] Scan error: {e}")
        await asyncio.sleep(POLL_INTERVAL)

@app.on_event("startup")
async def startup():
    asyncio.create_task(background_scanner())
    logger.info(f"[SHADOW] Agent started, polling every {POLL_INTERVAL}s")

# === ENDPOINTS ===
@app.get("/health")
async def health():
    healthy_count = sum(1 for s in shadow_state["services"].values() if s.get("status") == "healthy")
    total = len(shadow_state["services"])
    return {
        "service": "shadow_agent",
        "status": "operational",
        "port": SHADOW_PORT,
        "monitored_services": total,
        "healthy_services": healthy_count,
        "scan_count": shadow_state["scan_count"],
        "last_scan": shadow_state["last_scan"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/state")
async def get_state():
    return shadow_state

@app.get("/services")
async def get_services():
    return {"services": shadow_state["services"], "last_scan": shadow_state["last_scan"]}

@app.get("/alerts")
async def get_alerts(limit: int = 20):
    return {"alerts": shadow_state["alerts"][:limit]}

@app.post("/scan")
async def trigger_scan():
    results = await scan_all()
    return {"scan_results": results, "timestamp": shadow_state["last_scan"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("shadow_agent:app", host="0.0.0.0", port=SHADOW_PORT, reload=True)
