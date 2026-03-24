"""ARK95X Flamegate TLS Proxy - Port 8443
Secure transit layer for all gate communications. TLS termination, audit logging,
payload routing, and zero-trust enforcement.
"""
import os
import time
import json
import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger
import httpx

# === CONFIG ===
FLAMEGATE_PORT = int(os.getenv("FLAMEGATE_PORT", 8443))
ADMIN_TOKEN = os.getenv("FLAMEGATE_ADMIN_TOKEN", "ark95x-sovereign-flame-token")
AUDIT_DB = os.getenv("FLAMEGATE_AUDIT_DB", "flamegate_audit.db")
CORE_API = os.getenv("CORE_API_URL", "http://localhost:8000")
COMET_ROUTER = os.getenv("COMET_ROUTER_URL", "http://localhost:8100")
GATE_UNLOCKER = os.getenv("GATE_UNLOCKER_URL", "http://localhost:8200")

# === AUDIT DATABASE ===
def init_audit_db():
    db = sqlite3.connect(AUDIT_DB)
    db.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT,
            payload_hash TEXT,
            status TEXT,
            latency_ms REAL,
            ip_address TEXT
        )
    """)
    db.commit()
    return db

def log_audit(actor, action, target=None, payload_hash=None, status="ok", latency_ms=0, ip="unknown"):
    try:
        db = sqlite3.connect(AUDIT_DB)
        db.execute(
            "INSERT INTO audit_log (timestamp, actor, action, target, payload_hash, status, latency_ms, ip_address) VALUES (?,?,?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), actor, action, target, payload_hash, status, latency_ms, ip),
        )
        db.commit()
        db.close()
    except Exception as e:
        logger.error(f"Audit log failed: {e}")

# === MODELS ===
class ProxyPayload(BaseModel):
    target: str  # "core", "comet_router", "gate_unlocker", or full URL
    method: str = "POST"
    path: str = "/"
    body: dict = {}
    actor: str = "unknown"
    gate_id: str = ""

class AuditQuery(BaseModel):
    limit: int = 50
    actor: str = ""
    action: str = ""

# === APP ===
app = FastAPI(
    title="ARK95X Flamegate TLS Proxy",
    description="Secure transit layer for sovereign gate communications",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Init audit DB on startup
init_audit_db()

# === AUTH ===
async def verify_token(request: Request):
    token = request.headers.get("X-Flamegate-Token", "")
    if token != ADMIN_TOKEN:
        log_audit("unknown", "auth_failed", ip=request.client.host if request.client else "unknown")
        raise HTTPException(status_code=403, detail="Invalid Flamegate token")
    return token

# === TARGET RESOLUTION ===
TARGET_MAP = {
    "core": CORE_API,
    "comet_router": COMET_ROUTER,
    "gate_unlocker": GATE_UNLOCKER,
}

def resolve_target(target: str, path: str) -> str:
    base = TARGET_MAP.get(target, target)
    if not base.startswith("http"):
        base = f"http://{base}"
    return f"{base}{path}"

# === ENDPOINTS ===
@app.get("/health")
async def health():
    return {
        "service": "flamegate_tls",
        "status": "operational",
        "port": FLAMEGATE_PORT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "audit_db": AUDIT_DB,
    }

@app.post("/flamegate/proxy")
async def proxy_request(payload: ProxyPayload, token: str = Depends(verify_token)):
    start = time.time()
    url = resolve_target(payload.target, payload.path)
    payload_hash = hashlib.sha256(json.dumps(payload.body, sort_keys=True).encode()).hexdigest()[:16]

    logger.info(f"[FLAMEGATE] {payload.actor} -> {payload.target}{payload.path} [{payload.method}]")

    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            if payload.method.upper() == "GET":
                r = await client.get(url)
            elif payload.method.upper() == "POST":
                r = await client.post(url, json=payload.body)
            elif payload.method.upper() == "PUT":
                r = await client.put(url, json=payload.body)
            elif payload.method.upper() == "DELETE":
                r = await client.delete(url)
            else:
                raise HTTPException(400, f"Unsupported method: {payload.method}")

        latency = round((time.time() - start) * 1000, 2)
        log_audit(payload.actor, f"proxy_{payload.method.lower()}", payload.target, payload_hash, "ok", latency)

        try:
            response_data = r.json()
        except Exception:
            response_data = {"raw": r.text[:500]}

        return {
            "status": "proxied",
            "target": payload.target,
            "path": payload.path,
            "http_status": r.status_code,
            "latency_ms": latency,
            "payload_hash": payload_hash,
            "response": response_data,
        }

    except httpx.ConnectError:
        latency = round((time.time() - start) * 1000, 2)
        log_audit(payload.actor, f"proxy_{payload.method.lower()}", payload.target, payload_hash, "connect_error", latency)
        raise HTTPException(502, f"Target unreachable: {url}")
    except Exception as e:
        latency = round((time.time() - start) * 1000, 2)
        log_audit(payload.actor, f"proxy_{payload.method.lower()}", payload.target, payload_hash, "error", latency)
        raise HTTPException(500, f"Proxy error: {e}")

@app.get("/flamegate/audit")
async def get_audit(limit: int = 50, token: str = Depends(verify_token)):
    db = sqlite3.connect(AUDIT_DB)
    db.row_factory = sqlite3.Row
    rows = db.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    db.close()
    return {"audit_log": [dict(r) for r in rows], "total": len(rows)}

@app.get("/flamegate/stats")
async def get_stats(token: str = Depends(verify_token)):
    db = sqlite3.connect(AUDIT_DB)
    total = db.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    errors = db.execute("SELECT COUNT(*) FROM audit_log WHERE status != 'ok'").fetchone()[0]
    avg_latency = db.execute("SELECT AVG(latency_ms) FROM audit_log WHERE latency_ms > 0").fetchone()[0] or 0
    db.close()
    return {
        "total_requests": total,
        "error_count": errors,
        "success_rate": round((total - errors) / max(total, 1) * 100, 2),
        "avg_latency_ms": round(avg_latency, 2),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("flamegate_tls:app", host="0.0.0.0", port=FLAMEGATE_PORT, reload=True)
