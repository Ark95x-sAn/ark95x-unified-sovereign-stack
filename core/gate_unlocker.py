"""ARK95X Gate Unlocker - Port 8200
Zero-trust gate state management. Controls lock/unlock state for all system gates.
Council validation required for sensitive gates. Full audit trail.

/unlock and /unlock-all accept only operator credentials supplied in the
environment (GATE_OPERATOR_ID / GATE_OPERATOR_SECRET). Nothing is hard-coded
and there is no default. A relayed X-Flamegate-Token is not a credential.
"""
import hashlib
import hmac
import os
import sqlite3
from datetime import datetime, timezone

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel

# === CONFIG ===
UNLOCKER_PORT = int(os.getenv("GATE_UNLOCKER_PORT", 8200))
GATE_DB = os.getenv("GATE_STATE_DB", "gate_states.db")

OPERATOR_ID_HEADER = "X-Operator-Id"
OPERATOR_SECRET_HEADER = "X-Operator-Secret"
FORWARDED_TOKEN_HEADER = "X-Flamegate-Token"

MIN_OPERATOR_SECRET = 32
MAX_OPERATOR_SECRET = 512
MAX_OPERATOR_ID = 128


def credential_shape(operator_id: str, operator_secret: str) -> str:
    """Classify a pair as 'missing', 'malformed', or 'ok'.

    Empty values are missing. Whitespace, control characters, and an
    undersized secret are malformed. This does not compare the pair to the
    configured operator, and it never supplies a default.
    """
    if operator_id == "" or operator_secret == "":
        return "missing"
    id_bad = (
        len(operator_id) > MAX_OPERATOR_ID
        or any(ord(ch) < 33 or ord(ch) == 127 for ch in operator_id)
    )
    secret_bad = (
        len(operator_secret) < MIN_OPERATOR_SECRET
        or len(operator_secret) > MAX_OPERATOR_SECRET
        or any(ch.isspace() for ch in operator_secret)
    )
    if id_bad or secret_bad:
        return "malformed"
    return "ok"


_operator_id = os.environ.get("GATE_OPERATOR_ID", "")
_operator_secret = os.environ.get("GATE_OPERATOR_SECRET", "")
if credential_shape(_operator_id, _operator_secret) != "ok":
    # Fail closed before serving. The message must not echo the secret.
    logger.error("[GATE] refusing to start: operator credentials missing or malformed")
    raise RuntimeError(
        "GATE_OPERATOR_ID and GATE_OPERATOR_SECRET must be set in the environment "
        "(printable non-space id, secret >= 32 chars, no whitespace). No default is provided."
    )
OPERATOR_ID = _operator_id
OPERATOR_SECRET = _operator_secret


def _digest(value: str) -> bytes:
    return hashlib.sha256(value.encode("utf-8")).digest()


def _matches(presented: str, expected: str) -> bool:
    return hmac.compare_digest(_digest(presented), _digest(expected))


# === GATE STATE DATABASE ===
def init_gate_db():
    db = sqlite3.connect(GATE_DB, timeout=5)
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
            council_approved BOOLEAN DEFAULT 0,
            source TEXT DEFAULT ''
        )
    """)
    columns = {row[1] for row in db.execute("PRAGMA table_info(gate_journal)")}
    if "source" not in columns:
        db.execute("ALTER TABLE gate_journal ADD COLUMN source TEXT DEFAULT ''")
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
    db = sqlite3.connect(GATE_DB, timeout=5)
    db.row_factory = sqlite3.Row
    return db


def append_journal(db, gate_id, action, actor, prev_state, new_state, council=False, source=""):
    """Write one audit row on the caller's connection so it can commit with state."""
    db.execute(
        "INSERT INTO gate_journal (timestamp, gate_id, action, actor, previous_state, new_state, council_approved, source) VALUES (?,?,?,?,?,?,?,?)",
        (
            datetime.now(timezone.utc).isoformat(),
            gate_id,
            action,
            actor,
            prev_state,
            new_state,
            int(bool(council)),
            source,
        ),
    )


def journal_entry(gate_id, action, actor, prev_state, new_state, council=False, source=""):
    db = sqlite3.connect(GATE_DB, timeout=5)
    try:
        append_journal(db, gate_id, action, actor, prev_state, new_state, council, source)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


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


def _client_host(request: Request) -> str:
    if request.client is None or not request.client.host:
        return "unknown"
    return request.client.host


def _refuse(request: Request, reason: str) -> None:
    """Log and journal a refused unlock, then answer 401. Never record the secret."""
    source = _client_host(request)
    route = request.url.path or "/unlock"
    relayed = bool(request.headers.get(FORWARDED_TOKEN_HEADER, ""))
    recorded = f"{reason}:forwarded_token" if relayed else reason
    logger.warning(
        "[GATE] unlock refused route={} reason={} source={} relayed_token={}",
        route,
        reason,
        source,
        relayed,
    )
    try:
        journal_entry(route, "auth_failed", "unauthenticated", recorded, "locked", False, source)
    except Exception as exc:
        logger.error("[GATE] failed to journal unlock refusal: {}", exc)
    raise HTTPException(
        status_code=401,
        detail="Missing or invalid operator credentials",
        headers={"WWW-Authenticate": 'X-Operator-Id realm="gate-unlocker"'},
    )


def require_operator(
    request: Request,
    x_operator_id: str = Header(default=""),
    x_operator_secret: str = Header(default=""),
):
    """Authorize from env-configured operator credentials. The admin token is not accepted."""
    x_operator_id = x_operator_id or ""
    x_operator_secret = x_operator_secret or ""
    shape = credential_shape(x_operator_id, x_operator_secret)
    if shape != "ok":
        _refuse(request, shape)
    id_ok = _matches(x_operator_id, OPERATOR_ID)
    secret_ok = _matches(x_operator_secret, OPERATOR_SECRET)
    if not (id_ok and secret_ok):
        _refuse(request, "rejected")
    return True


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


@app.post("/unlock", dependencies=[Depends(require_operator)])
async def unlock_gate(req: UnlockRequest):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM gate_states WHERE gate_id = ?", (req.gate_id,)).fetchone()
        if not row:
            raise HTTPException(404, f"Gate not found: {req.gate_id}")

        gate = dict(row)
        if gate["state"] == "unlocked":
            return {"status": "already_unlocked", "gate_id": req.gate_id}

        if gate["requires_council"] and not req.council_override:
            append_journal(db, req.gate_id, "unlock_denied", req.actor, gate["state"], gate["state"], False)
            db.commit()
            return {
                "status": "council_required",
                "gate_id": req.gate_id,
                "message": "This gate requires council approval",
            }

        ts = datetime.now(timezone.utc).isoformat()
        db.execute(
            "UPDATE gate_states SET state = 'unlocked', last_actor = ?, last_changed = ?, unlock_count = unlock_count + 1 WHERE gate_id = ?",
            (req.actor, ts, req.gate_id),
        )
        # Same connection and commit as the state change, so an unlock cannot land unaudited.
        append_journal(db, req.gate_id, "unlock", req.actor, "locked", "unlocked", req.council_override)
        db.commit()
        logger.info("[GATE] UNLOCKED {} by {}", req.gate_id, req.actor)
        return {"status": "unlocked", "gate_id": req.gate_id, "actor": req.actor, "timestamp": ts}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@app.post("/lock")
async def lock_gate(req: LockRequest):
    db = get_db()
    try:
        if req.gate_id:
            row = db.execute("SELECT * FROM gate_states WHERE gate_id = ?", (req.gate_id,)).fetchone()
            if not row:
                raise HTTPException(404, f"Gate not found: {req.gate_id}")
            ts = datetime.now(timezone.utc).isoformat()
            db.execute(
                "UPDATE gate_states SET state = 'locked', last_actor = ?, last_changed = ? WHERE gate_id = ?",
                (req.actor, ts, req.gate_id),
            )
            append_journal(db, req.gate_id, "lock", req.actor, "unlocked", "locked")
            db.commit()
            return {"status": "locked", "gate_id": req.gate_id}
        ts = datetime.now(timezone.utc).isoformat()
        db.execute("UPDATE gate_states SET state = 'locked', last_actor = ?, last_changed = ?", (req.actor, ts))
        gates = db.execute("SELECT gate_id FROM gate_states").fetchall()
        for g in gates:
            append_journal(db, g["gate_id"], "lock_all", req.actor, "unknown", "locked")
        db.commit()
        return {"status": "all_locked", "count": len(gates), "timestamp": ts}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@app.get("/journal")
async def get_journal(limit: int = 50):
    db = get_db()
    rows = db.execute("SELECT * FROM gate_journal ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    db.close()
    return {"journal": [dict(r) for r in rows]}


@app.post("/unlock-all", dependencies=[Depends(require_operator)])
async def unlock_all(actor: str = "command_base"):
    db = get_db()
    try:
        ts = datetime.now(timezone.utc).isoformat()
        non_council = db.execute(
            "SELECT gate_id FROM gate_states WHERE requires_council = 0 AND state = 'locked'"
        ).fetchall()
        for g in non_council:
            db.execute(
                "UPDATE gate_states SET state = 'unlocked', last_actor = ?, last_changed = ?, unlock_count = unlock_count + 1 WHERE gate_id = ?",
                (actor, ts, g["gate_id"]),
            )
            append_journal(db, g["gate_id"], "unlock_all", actor, "locked", "unlocked")
        db.commit()
        return {"status": "bulk_unlocked", "count": len(non_council), "skipped_council_gates": True}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    uvicorn.run("gate_unlocker:app", host="0.0.0.0", port=UNLOCKER_PORT, reload=True)
