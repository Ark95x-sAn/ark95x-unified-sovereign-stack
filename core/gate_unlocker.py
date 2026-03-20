"""ARK95X Gate Unlocker - Port 8200
Zero-trust gate state management. Controls lock/unlock state for all system gates.
Council validation required for sensitive gates. Full audit trail.
"""
import os
import time
import json
import sqlite3
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

# === CONFIG ===
UNLOCKER_PORT = int(os.getenv("GATE_UNLOCKER_PORT", 8200))
ADMIN_TOKEN = os.getenv("FLAMEGATE_ADMIN_TOKEN", "ark95x-sovereign-flame-token")
GATE_DB = os.getenv("GATE_STATE_DB", "gate_states.db")

# === GATE STATE DATABASE ===
def init_gate_db():
    db = sqlite3.connect(GATE_DB)
    db.execute("""
        CREATE TABLE IF NOT EXISTS gate_states (
            gate_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            state TEXT DEFAULT 'locked',
            last_actor TEXT DEFAULT 'system',
            last_changed TEXT,
            unlock_count INTEGER DEFAULT 0,
            requires_council BOOLEAN DEFAULT 0
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS gate_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            gate_id TEXT NOT NULL,
            action TEXT NOT NULL,
            actor TEXT NOT NULL,
            previous_state TEXT,
            new_state TEXT,
            council_approved BOOLEAN DEFAULT 0
        )
    """)
    # Seed default gates
    default_gates = [
        ("gate_core", "Core API Gate", "locked", 0),
        ("gate_n8n", "n8n Workflow Gate", "locked", 0),
        ("gate_qdrant", "Qdrant Vector Gate", "locked", 0),
        ("gate_searxng", "SearXNG Intel Gate", "locked", 0),
        ("gate_grafana", "Grafana Monitor Gate", "locked", 0),
        ("gate_flamegate", "Flamegate TLS Gate", "locked", 1),
        ("gate_comet", "Comet Router Gate", "locked", 0),
        ("gate_ollama", "Ollama LLM Gate", "locked", 0),
    ]
    for gid, name, state, council in default_gates:
        db.execute(
            "INSERT OR IGNORE INTO gate_states (gate_id, name, state, requires_council, last_changed) VALUES (?,?,?,?,?)",
            (gid, name, state, council, datetime.now(timezone.utc).isoformat()),
        )
    db.commit()
    db.close()

def get_db():
    db = sqlite3.connect(GATE_DB)
    db.row_factory = sqlite3.Row
    return db

# === MODELS ===
class UnlockRequest(BaseModel):
    gate_id: str
    actor: str = "command_base"
    timestamp: str = ""
    council_override: bool = False

class LockRequest(BaseModel):
    gate_id: str = ""  # empty = lock all
    actor: str = "command_base"

# === APP ===
app = FastAPI(
    title="ARK95X Gate Unlocker",
    description="Zero-trust gate state management with council validation",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

init_gate_db()

def journal_entry(gate_id, action, actor, prev_state, new_state, council=False):
    db = sqlite3.connect(GATE_DB)
    db.execute(
        "INSERT INTO gate_journal (timestamp, gate_id, action, actor, previous_state, new_state, council_approved) VALUES (?,?,?,?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), gate_id, action, actor, prev_state, new_state, council),
    )
    db.commit()
    db.close()

# === ENDPOINTS ===
@app.get("/health")
async def health():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM gate_states").fetchone()[0]
    unlocked = db.execute("SELECT COUNT(*) FROM gate_states WHERE state = 'unlocked'").fetchone()[0]
    db.close()
    return {
        "service": "gate_unlocker",
        "status": "operational",
        "port": UNLOCKER_PORT,
        "total_gates": total,
        "unlocked_gates": unlocked,
        "locked_gates": total - unlocked,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/gates")
async def list_gates():
    db = get_db()
    rows = db.execute("SELECT * FROM gate_states ORDER BY gate_id").fetchall()
    db.close()
    return {"gates": [dict(r) for r in rows]}

@app.get("/gates/{gate_id}")
async def get_gate(gate_id: str):
    db = get_db()
    row = db.execute("SELECT * FROM gate_states WHERE gate_id = ?", (gate_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(404, f"Gate not found: {gate_id}")
    return dict(row)

@app.post("/unlock")
async def unlock_gate(req: UnlockRequest):
    db = get_db()
    row = db.execute("SELECT * FROM gate_states WHERE gate_id = ?", (req.gate_id,)).fetchone()
    if not row:
        db.close()
        raise HTTPException(404, f"Gate not found: {req.gate_id}")

    gate = dict(row)
    if gate["state"] == "unlocked":
        db.close()
        return {"status": "already_unlocked", "gate_id": req.gate_id}

    if gate["requires_council"] and not req.council_override:
        db.close()
        journal_entry(req.gate_id, "unlock_denied", req.actor, gate["state"], gate["state"], False)
        return {"status": "council_required", "gate_id": req.gate_id, "message": "This gate requires council approval"}

    ts = datetime.now(timezone.utc).isoformat()
    db.execute(
        "UPDATE gate_states SET state = 'unlocked', last_actor = ?, last_changed = ?, unlock_count = unlock_count + 1 WHERE gate_id = ?",
        (req.actor, ts, req.gate_id),
    )
    db.commit()
    db.close()

    journal_entry(req.gate_id, "unlock", req.actor, "locked", "unlocked", req.council_override)
    logger.info(f"[GATE] UNLOCKED {req.gate_id} by {req.actor}")

    return {"status": "unlocked", "gate_id": req.gate_id, "actor": req.actor, "timestamp": ts}

@app.post("/lock")
async def lock_gate(req: LockRequest):
    db = get_db()
    if req.gate_id:
        row = db.execute("SELECT * FROM gate_states WHERE gate_id = ?", (req.gate_id,)).fetchone()
        if not row:
            db.close()
            raise HTTPException(404, f"Gate not found: {req.gate_id}")
        db.execute(
            "UPDATE gate_states SET state = 'locked', last_actor = ?, last_changed = ? WHERE gate_id = ?",
            (req.actor, datetime.now(timezone.utc).isoformat(), req.gate_id),
        )
        journal_entry(req.gate_id, "lock", req.actor, "unlocked", "locked")
        db.commit()
        db.close()
        return {"status": "locked", "gate_id": req.gate_id}
    else:
        ts = datetime.now(timezone.utc).isoformat()
        db.execute("UPDATE gate_states SET state = 'locked', last_actor = ?, last_changed = ?", (req.actor, ts))
        db.commit()
        gates = db.execute("SELECT gate_id FROM gate_states").fetchall()
        db.close()
        for g in gates:
            journal_entry(g["gate_id"], "lock_all", req.actor, "unknown", "locked")
        return {"status": "all_locked", "count": len(gates), "timestamp": ts}

@app.get("/journal")
async def get_journal(limit: int = 50):
    db = get_db()
    rows = db.execute("SELECT * FROM gate_journal ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    db.close()
    return {"journal": [dict(r) for r in rows]}

@app.post("/unlock-all")
async def unlock_all(actor: str = "command_base"):
    db = get_db()
    ts = datetime.now(timezone.utc).isoformat()
    non_council = db.execute("SELECT gate_id FROM gate_states WHERE requires_council = 0 AND state = 'locked'").fetchall()
    for g in non_council:
        db.execute(
            "UPDATE gate_states SET state = 'unlocked', last_actor = ?, last_changed = ?, unlock_count = unlock_count + 1 WHERE gate_id = ?",
            (actor, ts, g["gate_id"]),
        )
        journal_entry(g["gate_id"], "unlock_all", actor, "locked", "unlocked")
    db.commit()
    db.close()
    return {"status": "bulk_unlocked", "count": len(non_council), "skipped_council_gates": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("gate_unlocker:app", host="0.0.0.0", port=UNLOCKER_PORT, reload=True)
