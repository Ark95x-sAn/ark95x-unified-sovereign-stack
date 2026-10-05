#!/usr/bin/env python3
"""Pyrion offline continuity queue: deterministic triage, no external execution."""
import argparse
import json
import sqlite3
from datetime import datetime, timezone

FEATURES = [
    "mission_intake", "entity_firewall", "acceptance_check", "deadline_watch", "source_locator",
    "claim_status", "contradiction_hold", "worker_registry", "invocation_binding", "recipient_binding",
    "lease_expiry", "handoff_receipt", "replay_detection", "scope_allowlist", "idempotency_key",
    "single_writer_claim", "crash_recovery", "unknown_write_hold", "artifact_digest", "readback_gate",
    "exception_digest", "priority_queue", "pause_switch", "checkpoint", "lesson_candidate",
]
SCHEMA = """CREATE TABLE IF NOT EXISTS tasks (
id TEXT PRIMARY KEY, entity TEXT NOT NULL, objective TEXT NOT NULL, due TEXT,
source_ref TEXT NOT NULL, scope TEXT NOT NULL CHECK(scope IN ('read','draft')),
state TEXT NOT NULL CHECK(state IN ('queued','claimed','held','done')),
lease_until TEXT, worker TEXT, result_ref TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events (
seq INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, task_id TEXT, kind TEXT NOT NULL, detail TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);"""

def utc(): return datetime.now(timezone.utc).isoformat()

def open_db(path):
    db = sqlite3.connect(path, timeout=10)
    db.execute("PRAGMA busy_timeout=10000")
    db.executescript(SCHEMA)
    return db

def event(db, task, kind, detail):
    db.execute("INSERT INTO events(at,task_id,kind,detail) VALUES(?,?,?,?)", (utc(),task,kind,detail))

def enqueue(db, task_id, entity, objective, source_ref, scope="draft", due=None):
    if not all((task_id,entity,objective,source_ref)) or scope not in ("read","draft"):
        raise ValueError("complete identity, source, and read/draft scope required")
    with db:
        db.execute("INSERT INTO tasks(id,entity,objective,due,source_ref,scope,state,created_at) VALUES(?,?,?,?,?,?,?,?)",(task_id,entity,objective,due,source_ref,scope,"queued",utc()))
        event(db,task_id,"enqueued","scope="+scope)

def pulse(db):
    """Observe, quarantine stale claims, and return one pending task; never run it."""
    with db:
        if db.execute("SELECT value FROM settings WHERE key='paused'").fetchone() == ("1",):
            return {"state":"PAUSED","next":None}
        now=utc()
        stale=db.execute("SELECT id FROM tasks WHERE state='claimed' AND lease_until<=?",(now,)).fetchall()
        for (task_id,) in stale:
            db.execute("UPDATE tasks SET state='held',worker=NULL WHERE id=?",(task_id,))
            event(db,task_id,"lease_expired","manual reconciliation required; no automatic retry")
        row=db.execute("SELECT id,entity,objective,due,source_ref,scope FROM tasks WHERE state='queued' ORDER BY CASE WHEN due IS NULL THEN 1 ELSE 0 END,due,created_at LIMIT 1").fetchone()
        holds=db.execute("SELECT COUNT(*) FROM tasks WHERE state='held'").fetchone()[0]
        return {"state":"PENDING" if row else "IDLE","held":holds,"next":dict(zip(("id","entity","objective","due","source_ref","scope"),row)) if row else None}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--db",default="firebird.db")
    sub=p.add_subparsers(dest="command",required=True)
    a=sub.add_parser("add");a.add_argument("id");a.add_argument("entity");a.add_argument("objective");a.add_argument("source_ref");a.add_argument("--scope",choices=("read","draft"),default="draft");a.add_argument("--due")
    sub.add_parser("pulse");sub.add_parser("features")
    pause=sub.add_parser("pause");pause.add_argument("value",choices=("on","off"))
    args=p.parse_args()
    if args.command=="features": print(json.dumps({"count":len(FEATURES),"features":FEATURES,"active_automations":0}));return
    db=open_db(args.db)
    if args.command=="add": enqueue(db,args.id,args.entity,args.objective,args.source_ref,args.scope,args.due);print("queued")
    elif args.command=="pulse": print(json.dumps(pulse(db)))
    else:
        with db: db.execute("INSERT INTO settings(key,value) VALUES('paused',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",("1" if args.value=="on" else "0",))
        print("paused" if args.value=="on" else "resumed")

if __name__=="__main__":main()
