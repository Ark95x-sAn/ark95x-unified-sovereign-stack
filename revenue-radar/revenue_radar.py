#!/usr/bin/env python3
"""Revenue Radar: local-first opportunity workflow with approval and audit gates.

Pipeline:
Capture -> clean -> deduplicate -> score -> draft -> approve -> send -> outcome

Runs on Python 3.10+ using only the standard library. It binds to localhost,
stores data in SQLite, defaults to dry-run sends, and can hand approved messages
to an n8n webhook when explicitly configured.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


APP_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("REVENUE_RADAR_DB", APP_DIR / "revenue_radar.db"))
HOST = os.environ.get("REVENUE_RADAR_HOST", "127.0.0.1")
PORT = int(os.environ.get("REVENUE_RADAR_PORT", "8765"))
DRY_RUN = os.environ.get("REVENUE_RADAR_DRY_RUN", "1").lower() not in {"0", "false", "no"}
SEND_WEBHOOK_URL = os.environ.get("REVENUE_RADAR_SEND_WEBHOOK_URL", "").strip()
USE_OLLAMA = os.environ.get("REVENUE_RADAR_USE_OLLAMA", "0").lower() in {"1", "true", "yes"}
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:14b")
SENDER_NAME = os.environ.get("REVENUE_RADAR_SENDER_NAME", "Ben")
ORG_NAME = os.environ.get("REVENUE_RADAR_ORG_NAME", "Network 95 Operations")
SCORE_POLICY_VERSION = "2026-07-21.v1"
TEMPLATE_VERSION = "followup.v1"

OPPORTUNITY_TYPES = {
    "real_estate": "Real Estate",
    "grant_service": "Grant Service",
    "investor": "Investor / Capital",
    "property_management": "Property Management",
    "ai_automation": "AI Automation",
    "other": "Other",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def clean_text(value: Any, limit: int = 4000) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()[:limit]


def normalize_email(value: Any) -> str:
    email = clean_text(value, 320).lower()
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError("Email format is invalid")
    return email


def normalize_phone(value: Any) -> str:
    raw = clean_text(value, 80)
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if digits and not 7 <= len(digits) <= 15:
        raise ValueError("Phone number must contain 7 to 15 digits")
    return digits


def bounded_float(value: Any, minimum: float = 0, maximum: float = 1_000_000_000) -> float:
    if value in (None, ""):
        return 0.0
    number = float(value)
    if number < minimum or number > maximum:
        raise ValueError(f"Number must be between {minimum:g} and {maximum:g}")
    return round(number, 2)


def bounded_int(value: Any, minimum: int = 0, maximum: int = 3650) -> int:
    if value in (None, ""):
        return 30
    number = int(value)
    if number < minimum or number > maximum:
        raise ValueError(f"Integer must be between {minimum} and {maximum}")
    return number


def canonical_type(value: Any) -> str:
    item = clean_text(value, 80).lower().replace(" ", "_")
    return item if item in OPPORTUNITY_TYPES else "other"


def fingerprint(record: dict[str, Any]) -> str:
    identity = record["normalized_email"] or record["normalized_phone"]
    parts = [
        identity,
        record["opportunity_type"],
        clean_text(record.get("property_address"), 500).lower(),
        clean_text(record.get("company"), 300).lower(),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def clean_record(payload: dict[str, Any]) -> dict[str, Any]:
    first_name = clean_text(payload.get("first_name"), 120)
    last_name = clean_text(payload.get("last_name"), 120)
    company = clean_text(payload.get("company"), 240)
    email = normalize_email(payload.get("email"))
    phone = normalize_phone(payload.get("phone"))
    if not any([first_name, last_name, company]):
        raise ValueError("Add a contact name or company")
    if not email and not phone:
        raise ValueError("Add an email or phone number")

    record: dict[str, Any] = {
        "source": clean_text(payload.get("source"), 120) or "manual",
        "first_name": first_name,
        "last_name": last_name,
        "company": company,
        "email": email,
        "normalized_email": email,
        "phone": phone,
        "normalized_phone": phone,
        "opportunity_type": canonical_type(payload.get("opportunity_type")),
        "property_address": clean_text(payload.get("property_address"), 500),
        "notes": clean_text(payload.get("notes"), 4000),
        "estimated_value": bounded_float(payload.get("estimated_value")),
        "urgency_days": bounded_int(payload.get("urgency_days")),
    }
    record["fingerprint"] = fingerprint(record)
    return record


def score_record(record: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    value = float(record.get("estimated_value") or 0)
    if value >= 100_000:
        score += 35
        reasons.append("high potential value +35")
    elif value >= 25_000:
        score += 28
        reasons.append("strong potential value +28")
    elif value >= 10_000:
        score += 22
        reasons.append("material potential value +22")
    elif value >= 2_500:
        score += 14
        reasons.append("moderate potential value +14")
    elif value > 0:
        score += 8
        reasons.append("value identified +8")

    urgency = int(record.get("urgency_days") or 30)
    if urgency <= 7:
        score += 25
        reasons.append("action needed within 7 days +25")
    elif urgency <= 30:
        score += 18
        reasons.append("action needed within 30 days +18")
    elif urgency <= 90:
        score += 10
        reasons.append("action needed within 90 days +10")
    else:
        score += 4
        reasons.append("long-range timing +4")

    has_email = bool(record.get("normalized_email"))
    has_phone = bool(record.get("normalized_phone"))
    if has_email and has_phone:
        score += 15
        reasons.append("two contact channels +15")
    elif has_email or has_phone:
        score += 8
        reasons.append("one contact channel +8")

    if record.get("opportunity_type") in {
        "real_estate", "grant_service", "investor", "property_management", "ai_automation"
    }:
        score += 15
        reasons.append("core service fit +15")
    else:
        score += 6
        reasons.append("unclassified fit +6")

    source = str(record.get("source") or "").lower()
    if source in {"referral", "existing_client", "inbound", "repeat"}:
        score += 10
        reasons.append("trusted source +10")
    elif source:
        score += 5
        reasons.append("source captured +5")
    return min(score, 100), reasons


def fallback_draft(record: dict[str, Any]) -> tuple[str, str, str]:
    contact = record.get("first_name") or record.get("company") or "there"
    label = OPPORTUNITY_TYPES.get(record.get("opportunity_type"), "opportunity")
    subject_target = record.get("company") or record.get("property_address") or contact
    subject = f"Next step: {label} — {subject_target}"[:200]
    timing = int(record.get("urgency_days") or 30)
    context = f" for {record['property_address']}" if record.get("property_address") else ""
    body = (
        f"Hi {contact},\n\n"
        f"I’m following up regarding the {label.lower()} opportunity{context}. "
        f"Based on the information I have, the next decision is expected within about {timing} days.\n\n"
        "If this is still active, reply with the best next step or a time that works for a short call. "
        "I’ll keep the process focused and document the action items.\n\n"
        f"{SENDER_NAME}\n{ORG_NAME}"
    )
    return subject, body, f"template:{TEMPLATE_VERSION}"


def ollama_draft(record: dict[str, Any]) -> tuple[str, str, str]:
    subject, body, method = fallback_draft(record)
    if not USE_OLLAMA:
        return subject, body, method
    prompt = {
        "task": "Write a concise, calm business follow-up. Do not invent facts or promises.",
        "output_schema": {"subject": "string", "body": "string"},
        "opportunity": {
            "contact_first_name": record.get("first_name"),
            "company": record.get("company"),
            "type": OPPORTUNITY_TYPES.get(record.get("opportunity_type"), "Other"),
            "property_address": record.get("property_address"),
            "estimated_value": record.get("estimated_value"),
            "urgency_days": record.get("urgency_days"),
            "notes": record.get("notes"),
            "sender": SENDER_NAME,
            "organization": ORG_NAME,
        },
    }
    request_body = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": json.dumps(prompt),
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2},
    }).encode("utf-8")
    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=request_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=45) as response:
            raw = json.loads(response.read().decode("utf-8"))
        generated = json.loads(raw.get("response", "{}"))
        candidate_subject = clean_text(generated.get("subject"), 200)
        candidate_body = str(generated.get("body") or "").strip()[:6000]
        if candidate_subject and candidate_body:
            return candidate_subject, candidate_body, f"ollama:{OLLAMA_MODEL}"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError, KeyError):
        pass
    return subject, body, method


def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with db_connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                source TEXT NOT NULL,
                first_name TEXT NOT NULL DEFAULT '',
                last_name TEXT NOT NULL DEFAULT '',
                company TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                normalized_email TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                normalized_phone TEXT NOT NULL DEFAULT '',
                opportunity_type TEXT NOT NULL,
                property_address TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                estimated_value REAL NOT NULL DEFAULT 0,
                urgency_days INTEGER NOT NULL DEFAULT 30,
                fingerprint TEXT NOT NULL,
                duplicate_of INTEGER,
                score INTEGER NOT NULL,
                score_reasons TEXT NOT NULL,
                draft_subject TEXT NOT NULL,
                draft_body TEXT NOT NULL,
                draft_method TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'drafted',
                approved_at TEXT,
                approval_hash TEXT,
                sent_at TEXT,
                outcome TEXT,
                outcome_value REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (duplicate_of) REFERENCES opportunities(id)
            );
            CREATE INDEX IF NOT EXISTS idx_opportunities_email ON opportunities(normalized_email);
            CREATE INDEX IF NOT EXISTS idx_opportunities_phone ON opportunities(normalized_phone);
            CREATE INDEX IF NOT EXISTS idx_opportunities_fingerprint ON opportunities(fingerprint);
            CREATE INDEX IF NOT EXISTS idx_opportunities_status ON opportunities(status);

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                opportunity_id INTEGER,
                event_type TEXT NOT NULL,
                actor TEXT NOT NULL,
                event_data TEXT NOT NULL,
                FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
            );
            CREATE INDEX IF NOT EXISTS idx_audit_opportunity ON audit_log(opportunity_id);
            """
        )
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(opportunities)")}
        if "approval_hash" not in columns:
            conn.execute("ALTER TABLE opportunities ADD COLUMN approval_hash TEXT")


def audit(conn: sqlite3.Connection, opportunity_id: int | None, event_type: str,
          data: dict[str, Any], actor: str = "operator") -> None:
    conn.execute(
        "INSERT INTO audit_log(created_at, opportunity_id, event_type, actor, event_data) VALUES(?,?,?,?,?)",
        (utc_now(), opportunity_id, event_type, actor, json.dumps(data, separators=(",", ":"), default=str)),
    )


def approval_payload_hash(row: sqlite3.Row | dict[str, Any]) -> str:
    """Bind approval to the exact destination and message bytes."""
    payload = {
        "opportunity_id": row["id"],
        "email": row["email"],
        "phone": row["phone"],
        "subject": row["draft_subject"],
        "body": row["draft_body"],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    try:
        item["score_reasons"] = json.loads(item.get("score_reasons") or "[]")
    except json.JSONDecodeError:
        item["score_reasons"] = []
    item["opportunity_type_label"] = OPPORTUNITY_TYPES.get(item.get("opportunity_type"), "Other")
    return item


def find_potential_duplicate(conn: sqlite3.Connection, record: dict[str, Any]) -> sqlite3.Row | None:
    clauses: list[str] = []
    params: list[str] = []
    if record["normalized_email"]:
        clauses.append("normalized_email = ?")
        params.append(record["normalized_email"])
    if record["normalized_phone"]:
        clauses.append("normalized_phone = ?")
        params.append(record["normalized_phone"])
    if not clauses:
        return None
    return conn.execute(
        f"SELECT * FROM opportunities WHERE ({' OR '.join(clauses)}) ORDER BY id DESC LIMIT 1",
        params,
    ).fetchone()


def merge_exact_duplicate(conn: sqlite3.Connection, existing: sqlite3.Row,
                          record: dict[str, Any]) -> dict[str, Any]:
    current = row_to_dict(existing)
    updates: dict[str, Any] = {}
    for field in ["first_name", "last_name", "company", "email", "normalized_email", "phone",
                  "normalized_phone", "property_address"]:
        if not current.get(field) and record.get(field):
            updates[field] = record[field]
    if record.get("notes") and record["notes"] not in (current.get("notes") or ""):
        updates["notes"] = (current.get("notes", "") + " | " + record["notes"]).strip(" |")[:4000]
    if record["estimated_value"] > float(current.get("estimated_value") or 0):
        updates["estimated_value"] = record["estimated_value"]
    if record["urgency_days"] < int(current.get("urgency_days") or 3650):
        updates["urgency_days"] = record["urgency_days"]

    merged = dict(current)
    merged.update(updates)
    new_score, reasons = score_record(merged)
    merged["score"] = new_score
    merged["score_reasons"] = reasons
    if not current.get("approved_at"):
        subject, body, method = ollama_draft(merged)
        updates.update({"draft_subject": subject, "draft_body": body, "draft_method": method})
    updates.update({"score": new_score, "score_reasons": json.dumps(reasons), "updated_at": utc_now()})

    assignments = ", ".join(f"{field} = ?" for field in updates)
    conn.execute(
        f"UPDATE opportunities SET {assignments} WHERE id = ?",
        [*updates.values(), existing["id"]],
    )
    audit(conn, existing["id"], "duplicate_merged", {
        "matched_fingerprint": record["fingerprint"],
        "updated_fields": sorted(updates.keys()),
    })
    result = conn.execute("SELECT * FROM opportunities WHERE id = ?", (existing["id"],)).fetchone()
    assert result is not None
    return row_to_dict(result)


def capture_opportunity(payload: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    record = clean_record(payload)
    score, reasons = score_record(record)
    record["score"] = score
    record["score_reasons"] = reasons
    subject, body, method = ollama_draft(record)
    now = utc_now()
    with db_connect() as conn:
        exact = conn.execute(
            "SELECT * FROM opportunities WHERE fingerprint = ? ORDER BY id DESC LIMIT 1",
            (record["fingerprint"],),
        ).fetchone()
        if exact:
            return merge_exact_duplicate(conn, exact, record), True

        potential = find_potential_duplicate(conn, record)
        duplicate_of = potential["id"] if potential else None
        cursor = conn.execute(
            """
            INSERT INTO opportunities(
                created_at, updated_at, source, first_name, last_name, company,
                email, normalized_email, phone, normalized_phone, opportunity_type,
                property_address, notes, estimated_value, urgency_days, fingerprint,
                duplicate_of, score, score_reasons, draft_subject, draft_body, draft_method, status
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                now, now, record["source"], record["first_name"], record["last_name"], record["company"],
                record["email"], record["normalized_email"], record["phone"], record["normalized_phone"],
                record["opportunity_type"], record["property_address"], record["notes"],
                record["estimated_value"], record["urgency_days"], record["fingerprint"], duplicate_of,
                score, json.dumps(reasons), subject, body, method, "drafted",
            ),
        )
        opportunity_id = int(cursor.lastrowid)
        audit(conn, opportunity_id, "captured", {
            "source": record["source"], "score": score, "draft_method": method,
            "potential_duplicate_of": duplicate_of,
            "score_policy_version": SCORE_POLICY_VERSION,
            "template_version": TEMPLATE_VERSION,
        })
        row = conn.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)).fetchone()
        assert row is not None
        return row_to_dict(row), False


def approve_opportunity(opportunity_id: int) -> dict[str, Any]:
    with db_connect() as conn:
        row = conn.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)).fetchone()
        if not row:
            raise LookupError("Opportunity not found")
        if row["sent_at"]:
            return row_to_dict(row)
        if row["approved_at"]:
            return row_to_dict(row)
        now = utc_now()
        exact_hash = approval_payload_hash(row)
        conn.execute(
            "UPDATE opportunities SET approved_at = ?, approval_hash = ?, updated_at = ?, status = 'approved' WHERE id = ?",
            (now, exact_hash, now, opportunity_id),
        )
        audit(conn, opportunity_id, "approved", {
            "approval_payload_sha256": exact_hash,
            "score_policy_version": SCORE_POLICY_VERSION,
            "template_version": TEMPLATE_VERSION,
        })
        updated = conn.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)).fetchone()
        assert updated is not None
        return row_to_dict(updated)


def webhook_allowed(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme == "https" and parsed.netloc:
        return True
    return parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}


def send_opportunity(opportunity_id: int) -> dict[str, Any]:
    conn = db_connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)).fetchone()
        if not row:
            raise LookupError("Opportunity not found")
        if not row["approved_at"]:
            raise PermissionError("Approval is required before send")
        if row["sent_at"] or row["status"] in {"simulated", "handed_off", "won", "lost", "follow_up"}:
            result = row_to_dict(row)
            conn.rollback()
            conn.close()
            return result
        if row["status"] == "sending":
            raise RuntimeError("Send is already in progress; reconcile it before retrying")
        if row["approval_hash"] != approval_payload_hash(row):
            raise PermissionError("Draft or recipient changed after approval; approve again")

        idempotency_key = hashlib.sha256(
            f"revenue-radar:{opportunity_id}:{row['approved_at']}".encode()
        ).hexdigest()
        payload = {
            "idempotency_key": idempotency_key,
            "opportunity_id": opportunity_id,
            "recipient": {"email": row["email"], "phone": row["phone"]},
            "message": {"subject": row["draft_subject"], "body": row["draft_body"]},
            "approval": {"approved_at": row["approved_at"], "source": "revenue-radar"},
            "context": {
                "contact": " ".join(filter(None, [row["first_name"], row["last_name"]])),
                "company": row["company"],
                "opportunity_type": row["opportunity_type"],
                "estimated_value": row["estimated_value"],
            },
        }

        if DRY_RUN:
            conn.execute(
                "UPDATE opportunities SET status = 'simulated', updated_at = ? WHERE id = ?",
                (utc_now(), opportunity_id),
            )
            audit(conn, opportunity_id, "send_simulated", {
                "idempotency_key": idempotency_key,
                "recipient_channel": "email" if row["email"] else "phone",
            })
            updated = conn.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)).fetchone()
            conn.commit()
            assert updated is not None
            result = row_to_dict(updated)
            conn.close()
            return result

        if not SEND_WEBHOOK_URL:
            raise RuntimeError("Live send requires REVENUE_RADAR_SEND_WEBHOOK_URL")
        if not webhook_allowed(SEND_WEBHOOK_URL):
            raise RuntimeError("Webhook must use HTTPS or localhost HTTP")
        conn.execute(
            "UPDATE opportunities SET status = 'sending', updated_at = ? WHERE id = ?",
            (utc_now(), opportunity_id),
        )
        audit(conn, opportunity_id, "send_started", {"idempotency_key": idempotency_key})
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise
    conn.close()

    req = urllib.request.Request(
        SEND_WEBHOOK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key,
            "User-Agent": "RevenueRadar/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            response_preview = response.read(1000).decode("utf-8", errors="replace")
            status_code = response.status
    except urllib.error.HTTPError as exc:
        with db_connect() as failure_conn:
            failure_conn.execute(
                "UPDATE opportunities SET status = 'failed', updated_at = ? WHERE id = ?",
                (utc_now(), opportunity_id),
            )
            audit(failure_conn, opportunity_id, "send_failed", {"http_status": exc.code, "idempotency_key": idempotency_key})
        raise RuntimeError(f"Send webhook returned HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        with db_connect() as failure_conn:
            failure_conn.execute(
                "UPDATE opportunities SET status = 'failed', updated_at = ? WHERE id = ?",
                (utc_now(), opportunity_id),
            )
            audit(failure_conn, opportunity_id, "send_failed", {"reason": str(exc.reason)[:300], "idempotency_key": idempotency_key})
        raise RuntimeError("Send webhook could not be reached") from exc

    with db_connect() as success_conn:
        now = utc_now()
        success_conn.execute(
            "UPDATE opportunities SET status = 'handed_off', sent_at = ?, updated_at = ? WHERE id = ?",
            (now, now, opportunity_id),
        )
        audit(success_conn, opportunity_id, "webhook_accepted", {
            "idempotency_key": idempotency_key,
            "http_status": status_code,
            "response_preview": response_preview,
            "delivery_confirmed": False,
        })
        updated = success_conn.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)).fetchone()
        assert updated is not None
        return row_to_dict(updated)


def log_outcome(opportunity_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {"no_response", "replied", "meeting", "won", "lost", "other"}
    outcome = clean_text(payload.get("outcome"), 60).lower()
    if outcome not in allowed:
        raise ValueError("Invalid outcome")
    value = bounded_float(payload.get("outcome_value"))
    with db_connect() as conn:
        row = conn.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)).fetchone()
        if not row:
            raise LookupError("Opportunity not found")
        if row["status"] not in {"simulated", "handed_off", "follow_up", "won", "lost"}:
            raise PermissionError("Run the approved send step before logging an outcome")
        status = outcome if outcome in {"won", "lost"} else "follow_up"
        now = utc_now()
        conn.execute(
            "UPDATE opportunities SET outcome = ?, outcome_value = ?, status = ?, updated_at = ? WHERE id = ?",
            (outcome, value, status, now, opportunity_id),
        )
        audit(conn, opportunity_id, "outcome_logged", {"outcome": outcome, "outcome_value": value})
        updated = conn.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)).fetchone()
        assert updated is not None
        return row_to_dict(updated)


def dashboard_data() -> dict[str, Any]:
    with db_connect() as conn:
        rows = conn.execute("SELECT * FROM opportunities ORDER BY score DESC, id DESC LIMIT 250").fetchall()
        opportunities = [row_to_dict(row) for row in rows]
        metrics = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(estimated_value), 0) AS pipeline_value,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) AS awaiting_send,
                SUM(CASE WHEN status IN ('handed_off','simulated','follow_up','won','lost') THEN 1 ELSE 0 END) AS processed,
                SUM(CASE WHEN outcome = 'won' THEN 1 ELSE 0 END) AS won_count,
                COALESCE(SUM(CASE WHEN outcome = 'won' THEN outcome_value ELSE 0 END), 0) AS won_value,
                SUM(CASE WHEN duplicate_of IS NOT NULL THEN 1 ELSE 0 END) AS potential_duplicates
            FROM opportunities
            """
        ).fetchone()
        audit_rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT 30"
        ).fetchall()
    return {
        "mode": "DRY RUN" if DRY_RUN else "LIVE WEBHOOK",
        "metrics": dict(metrics) if metrics else {},
        "opportunities": opportunities,
        "recent_audit": [dict(row) for row in audit_rows],
    }


HTML = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Revenue Radar</title>
  <style>
    :root { --bg:#07100d; --panel:#0e1b17; --line:#21372f; --text:#ecfff7; --muted:#8eaa9f;
      --green:#42f5a1; --amber:#ffca62; --red:#ff6b75; --blue:#6bbcff; }
    * { box-sizing:border-box; }
    body { margin:0; font-family:Inter,Segoe UI,Arial,sans-serif; background:radial-gradient(circle at 15% -10%,#17352b,transparent 32%),var(--bg); color:var(--text); }
    main { width:min(1440px,95vw); margin:0 auto; padding:30px 0 70px; }
    header { display:flex; justify-content:space-between; align-items:flex-start; gap:20px; margin-bottom:24px; }
    h1 { font-size:clamp(28px,4vw,48px); margin:0; letter-spacing:-.04em; }
    h2 { margin:0 0 18px; font-size:18px; }
    p { color:var(--muted); margin:7px 0 0; }
    .mode { border:1px solid var(--green); color:var(--green); padding:8px 12px; border-radius:999px; font-size:12px; font-weight:800; letter-spacing:.12em; }
    .metrics { display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin-bottom:18px; }
    .card,.panel { background:linear-gradient(145deg,rgba(16,31,26,.96),rgba(10,22,18,.96)); border:1px solid var(--line); border-radius:16px; box-shadow:0 14px 30px rgba(0,0,0,.22); }
    .card { padding:17px; }
    .label { color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.12em; }
    .value { font-size:24px; font-weight:800; margin-top:7px; }
    .layout { display:grid; grid-template-columns:360px 1fr; gap:18px; align-items:start; }
    .panel { padding:20px; }
    form { display:grid; gap:11px; }
    .twocol { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
    label { font-size:12px; color:var(--muted); display:grid; gap:5px; }
    input,select,textarea { width:100%; border-radius:9px; border:1px solid var(--line); background:#07120e; color:var(--text); padding:10px 11px; outline:none; }
    input:focus,select:focus,textarea:focus { border-color:var(--green); }
    textarea { min-height:84px; resize:vertical; }
    button { border:0; border-radius:9px; padding:10px 13px; font-weight:800; cursor:pointer; background:var(--green); color:#04100b; }
    button.secondary { background:#173329; color:var(--text); border:1px solid #2b4a3f; }
    button.warn { background:var(--amber); }
    button:disabled { opacity:.4; cursor:not-allowed; }
    .tablewrap { overflow:auto; }
    table { width:100%; border-collapse:collapse; min-width:930px; }
    th { color:var(--muted); text-align:left; font-size:10px; letter-spacing:.11em; text-transform:uppercase; padding:0 10px 11px; }
    td { border-top:1px solid var(--line); padding:13px 10px; vertical-align:top; font-size:13px; }
    .name { font-weight:800; }
    .sub { color:var(--muted); font-size:11px; margin-top:4px; max-width:280px; }
    .score { width:40px; height:40px; border-radius:50%; display:grid; place-items:center; font-weight:900; border:3px solid var(--green); }
    .pill { display:inline-block; border:1px solid var(--line); border-radius:999px; padding:4px 8px; font-size:10px; text-transform:uppercase; letter-spacing:.06em; }
    .dup { border-color:var(--amber); color:var(--amber); margin-top:5px; }
    .actions { display:flex; flex-wrap:wrap; gap:6px; }
    .actions button { font-size:11px; padding:7px 9px; }
    dialog { max-width:700px; width:92vw; border:1px solid var(--line); border-radius:16px; padding:22px; background:#0c1915; color:var(--text); }
    dialog::backdrop { background:rgba(0,0,0,.72); }
    pre { white-space:pre-wrap; background:#07120e; border:1px solid var(--line); padding:14px; border-radius:10px; max-height:360px; overflow:auto; }
    .notice { min-height:22px; color:var(--green); font-size:12px; margin-top:10px; }
    @media (max-width:1000px) { .metrics{grid-template-columns:repeat(2,1fr)} .layout{grid-template-columns:1fr} }
  </style>
</head>
<body>
<main>
  <header><div><h1>Revenue Radar</h1><p>Capture → clean → deduplicate → score → draft → approve → send → outcome</p></div><div id="mode" class="mode">LOADING</div></header>
  <section class="metrics">
    <div class="card"><div class="label">Opportunities</div><div class="value" id="mTotal">0</div></div>
    <div class="card"><div class="label">Pipeline</div><div class="value" id="mPipeline">$0</div></div>
    <div class="card"><div class="label">Awaiting send</div><div class="value" id="mApproved">0</div></div>
    <div class="card"><div class="label">Potential duplicates</div><div class="value" id="mDupes">0</div></div>
    <div class="card"><div class="label">Won value</div><div class="value" id="mWon">$0</div></div>
  </section>
  <div class="layout">
    <section class="panel">
      <h2>Capture opportunity</h2>
      <form id="captureForm">
        <div class="twocol">
          <label>First name<input name="first_name" autocomplete="given-name"></label>
          <label>Last name<input name="last_name" autocomplete="family-name"></label>
        </div>
        <label>Company<input name="company" autocomplete="organization"></label>
        <div class="twocol">
          <label>Email<input name="email" type="email" autocomplete="email"></label>
          <label>Phone<input name="phone" autocomplete="tel"></label>
        </div>
        <div class="twocol">
          <label>Opportunity type<select name="opportunity_type">
            <option value="real_estate">Real Estate</option><option value="grant_service">Grant Service</option>
            <option value="investor">Investor / Capital</option><option value="property_management">Property Management</option>
            <option value="ai_automation">AI Automation</option><option value="other">Other</option>
          </select></label>
          <label>Source<select name="source"><option>manual</option><option>inbound</option><option>referral</option><option>existing_client</option><option>repeat</option><option>web</option></select></label>
        </div>
        <label>Property / project<input name="property_address"></label>
        <div class="twocol">
          <label>Estimated value<input name="estimated_value" type="number" min="0" step="100"></label>
          <label>Decision in days<input name="urgency_days" type="number" min="0" max="3650" value="30"></label>
        </div>
        <label>Notes<textarea name="notes" placeholder="Known facts only"></textarea></label>
        <button type="submit">Capture + score + draft</button>
      </form>
      <div id="notice" class="notice"></div>
    </section>
    <section class="panel">
      <h2>Priority queue</h2>
      <div class="tablewrap"><table>
        <thead><tr><th>Score</th><th>Contact</th><th>Opportunity</th><th>Value</th><th>Status</th><th>Controls</th></tr></thead>
        <tbody id="queue"></tbody>
      </table></div>
    </section>
  </div>
</main>
<dialog id="draftDialog"><h2>Draft review</h2><div id="draftMeta" class="sub"></div><h3 id="draftSubject"></h3><pre id="draftBody"></pre><form method="dialog"><button>Close</button></form></dialog>
<script>
const $ = s => document.querySelector(s);
let state = {opportunities:[]};
const money = n => new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(Number(n||0));
const esc = s => String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

async function api(path, options={}) {
  const res = await fetch(path,{headers:{'Content-Type':'application/json'},...options});
  const data = await res.json().catch(()=>({error:'Invalid server response'}));
  if(!res.ok) throw new Error(data.error||`Request failed (${res.status})`);
  return data;
}
function notify(message,bad=false){ const el=$('#notice'); el.textContent=message; el.style.color=bad?'var(--red)':'var(--green)'; }

async function refresh(){
  state = await api('/api/dashboard');
  const m=state.metrics;
  $('#mode').textContent=state.mode; $('#mTotal').textContent=m.total||0; $('#mPipeline').textContent=money(m.pipeline_value);
  $('#mApproved').textContent=m.awaiting_send||0; $('#mDupes').textContent=m.potential_duplicates||0; $('#mWon').textContent=money(m.won_value);
  const tbody=$('#queue'); tbody.innerHTML='';
  for(const o of state.opportunities){
    const canApprove=!o.approved_at&&!o.sent_at; const canSend=!!o.approved_at&&!o.sent_at&&['approved','failed'].includes(o.status);
    const contact=[o.first_name,o.last_name].filter(Boolean).join(' ')||o.company;
    const tr=document.createElement('tr');
    tr.innerHTML=`<td><div class="score">${o.score}</div></td>
      <td><div class="name">${esc(contact)}</div><div class="sub">${esc(o.company&&o.company!==contact?o.company:'')} ${esc(o.email||o.phone)}</div>${o.duplicate_of?`<span class="pill dup">review duplicate #${o.duplicate_of}</span>`:''}</td>
      <td><div class="name">${esc(o.opportunity_type_label)}</div><div class="sub">${esc(o.property_address||o.notes||'No project detail')}</div></td>
      <td><div class="name">${money(o.estimated_value)}</div><div class="sub">${o.urgency_days} day timing</div></td>
      <td><span class="pill">${esc(o.status)}</span>${o.outcome?`<div class="sub">${esc(o.outcome)} ${money(o.outcome_value)}</div>`:''}</td>
      <td><div class="actions"><button class="secondary" data-action="view" data-id="${o.id}">Review</button><button data-action="approve" data-id="${o.id}" ${canApprove?'':'disabled'}>Approve</button><button class="warn" data-action="send" data-id="${o.id}" ${canSend?'':'disabled'}>Send</button><button class="secondary" data-action="outcome" data-id="${o.id}" ${o.approved_at?'':'disabled'}>Outcome</button></div></td>`;
    tbody.appendChild(tr);
  }
}

$('#captureForm').addEventListener('submit',async e=>{
  e.preventDefault(); notify('Processing…');
  const payload=Object.fromEntries(new FormData(e.target).entries());
  try { const r=await api('/api/opportunities',{method:'POST',body:JSON.stringify(payload)}); notify(r.deduplicated?'Exact duplicate merged safely.':'Captured, scored, and drafted.'); e.target.reset(); e.target.urgency_days.value=30; await refresh(); }
  catch(err){ notify(err.message,true); }
});

$('#queue').addEventListener('click',async e=>{
  const b=e.target.closest('button[data-action]'); if(!b)return;
  const id=Number(b.dataset.id), action=b.dataset.action, o=state.opportunities.find(x=>x.id===id);
  try {
    if(action==='view'){ $('#draftMeta').textContent=`Score ${o.score} · ${o.draft_method} · ${o.score_reasons.join(' | ')}`; $('#draftSubject').textContent=o.draft_subject; $('#draftBody').textContent=o.draft_body; $('#draftDialog').showModal(); return; }
    if(action==='approve'){ if(!confirm('Approve this exact draft for sending?'))return; await api(`/api/opportunities/${id}/approve`,{method:'POST',body:'{}'}); notify(`Opportunity #${id} approved.`); }
    if(action==='send'){ if(!confirm('Send the approved draft? Dry-run mode simulates delivery.'))return; const r=await api(`/api/opportunities/${id}/send`,{method:'POST',body:'{}'}); notify(r.opportunity.status==='simulated'?`Opportunity #${id} simulated—nothing left the PC.`:`Opportunity #${id} handed to n8n; downstream delivery is not yet confirmed.`); }
    if(action==='outcome'){ const outcome=prompt('Outcome: no_response, replied, meeting, won, lost, or other','replied'); if(!outcome)return; const value=outcome==='won'?prompt('Collected/closed value','0'):'0'; await api(`/api/opportunities/${id}/outcome`,{method:'POST',body:JSON.stringify({outcome,outcome_value:value})}); notify(`Outcome logged for #${id}.`); }
    await refresh();
  } catch(err){ notify(err.message,true); }
});

refresh().catch(err=>notify(err.message,true));
</script>
</body></html>'''


class RevenueRadarHandler(BaseHTTPRequestHandler):
    server_version = "RevenueRadar/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write(f"[{utc_now()}] {self.address_string()} {fmt % args}\n")

    def _json(self, data: Any, status: int = 200) -> None:
        raw = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 1_000_000:
            raise ValueError("Request body is too large")
        if length == 0:
            return {}
        data = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def _route_id(self, suffix: str) -> int | None:
        match = re.fullmatch(rf"/api/opportunities/(\d+)/{suffix}", self.path)
        return int(match.group(1)) if match else None

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            raw = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.end_headers()
            self.wfile.write(raw)
            return
        if self.path == "/api/dashboard":
            self._json(dashboard_data())
            return
        if self.path == "/health":
            self._json({"ok": True, "mode": "dry-run" if DRY_RUN else "live"})
            return
        self._json({"error": "Not found"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        try:
            payload = self._read_json()
            if self.path == "/api/opportunities":
                opportunity, deduplicated = capture_opportunity(payload)
                self._json({"opportunity": opportunity, "deduplicated": deduplicated}, 200 if deduplicated else 201)
                return
            opportunity_id = self._route_id("approve")
            if opportunity_id is not None:
                self._json({"opportunity": approve_opportunity(opportunity_id)})
                return
            opportunity_id = self._route_id("send")
            if opportunity_id is not None:
                self._json({"opportunity": send_opportunity(opportunity_id)})
                return
            opportunity_id = self._route_id("outcome")
            if opportunity_id is not None:
                self._json({"opportunity": log_outcome(opportunity_id, payload)})
                return
            self._json({"error": "Not found"}, 404)
        except json.JSONDecodeError:
            self._json({"error": "Request contains invalid JSON"}, 400)
        except ValueError as exc:
            self._json({"error": str(exc)}, 400)
        except LookupError as exc:
            self._json({"error": str(exc)}, 404)
        except PermissionError as exc:
            self._json({"error": str(exc)}, 403)
        except RuntimeError as exc:
            self._json({"error": str(exc)}, 409)
        except Exception as exc:  # defensive boundary; details stay in local logs
            self.log_error("Unhandled error: %s", exc)
            self._json({"error": "Unexpected local server error"}, 500)


def main() -> None:
    global DB_PATH
    parser = argparse.ArgumentParser(description="Run Revenue Radar locally")
    parser.add_argument("--host", default=HOST, help="Bind address; default is localhost only")
    parser.add_argument("--port", type=int, default=PORT, help="Local port; default 8765")
    parser.add_argument("--db", type=Path, default=DB_PATH, help="SQLite database path")
    args = parser.parse_args()
    DB_PATH = args.db.resolve()
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        print("Refusing non-local bind. Use a private reverse proxy or Tailscale instead.", file=sys.stderr)
        raise SystemExit(2)
    init_db()
    server = ThreadingHTTPServer((args.host, args.port), RevenueRadarHandler)
    print(f"Revenue Radar running at http://{args.host}:{args.port}")
    print(f"Mode: {'DRY RUN (no external send)' if DRY_RUN else 'LIVE WEBHOOK'}")
    print(f"Database: {DB_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Revenue Radar.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
