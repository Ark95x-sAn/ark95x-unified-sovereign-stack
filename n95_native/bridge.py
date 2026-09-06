"""Dependency-free, loopback-only receipt bridge. See README.md for trust boundaries."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import platform
import re
import secrets
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
import uuid

NODES = ("GM700", "RTX2080", "SURFACE")
MAX_BODY = 16_384
MAX_TTL = 90
FUTURE_SKEW = 15
GENESIS = "0" * 64
FIELDS = {"version", "event_id", "node_id", "nonce", "kind", "source_time",
          "expires_at", "payload", "signature"}
PAYLOAD_KEYS = {"producer_sha256", "os", "python", "cpu_count", "synthetic"}
HEX = re.compile(r"^[a-f0-9]{64}$")
IDENTIFIER = re.compile(r"^[a-zA-Z0-9_-]{16,80}$")


class Rejected(ValueError):
    """Internal rejection reason; HTTP clients receive a generic response."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False)


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise Rejected("duplicate JSON key")
            result[key] = value
        return result

    def invalid_constant(_):
        raise Rejected("nonfinite JSON number")

    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid_constant)
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise Rejected("invalid JSON") from exc


def private_write(path, text):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(text)


def producer_digest():
    source = Path(__file__)
    return hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else None


def init_state(state):
    state = Path(state).expanduser().resolve()
    if any((parent / ".git").exists() for parent in (state, *state.parents)):
        raise Rejected("secret state must be outside a git checkout")
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    if any(state.iterdir()):
        raise Rejected("state directory must be empty")
    os.chmod(state, 0o700)
    (state / "nodes").mkdir(mode=0o700)
    config = {"version": 1, "nodes": {
        node: {"capabilities": ["telemetry"], "producer_sha256": producer_digest()}
        for node in NODES}}
    for node in NODES:
        private_write(state / "nodes" / (node + ".key"), secrets.token_hex(32))
    private_write(state / "reader.key", secrets.token_hex(32))
    private_write(state / "config.json", canonical(config))
    Store(state)
    return {"initialized": True, "configured_nodes": list(NODES), "online_nodes": 0}


def key_for(state, node):
    if node not in NODES:
        raise Rejected("unregistered node")
    try:
        text = (Path(state) / "nodes" / (node + ".key")).read_text().strip()
        if not HEX.fullmatch(text):
            raise ValueError("invalid key")
        return bytes.fromhex(text)
    except (OSError, ValueError) as exc:
        raise Rejected("node key unavailable") from exc


def sign(envelope, key):
    body = {k: v for k, v in envelope.items() if k != "signature"}
    return hmac.new(key, canonical(body).encode(), hashlib.sha256).hexdigest()


def make_envelope(state, node, *, now=None, synthetic=False):
    now = time.time() if now is None else now
    envelope = {"version": 1, "event_id": uuid.uuid4().hex, "node_id": node,
                "nonce": secrets.token_hex(16), "kind": "heartbeat",
                "source_time": now, "expires_at": now + MAX_TTL,
                "payload": {"producer_sha256": producer_digest(),
                            "os": platform.system(), "python": platform.python_version(),
                            "cpu_count": os.cpu_count() or 1, "synthetic": synthetic}}
    envelope["signature"] = sign(envelope, key_for(state, node))
    return envelope


class Store:
    def __init__(self, state):
        self.state = Path(state).expanduser().resolve()
        self.lock = threading.RLock()
        self.config = decode((self.state / "config.json").read_bytes())
        self._validate_config()
        self.db = self.state / "evidence.sqlite3"
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY,
                    event_id TEXT NOT NULL UNIQUE,
                    node_id TEXT NOT NULL,
                    nonce TEXT NOT NULL,
                    received_at REAL NOT NULL,
                    envelope TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    chain_hash TEXT NOT NULL,
                    UNIQUE(node_id, nonce)
                );
            """)
        os.chmod(self.db, 0o600)
        self.audit()

    def _validate_config(self):
        if not isinstance(self.config, dict) or set(self.config) != {"version", "nodes"}:
            raise Rejected("invalid configuration")
        if self.config["version"] != 1 or set(self.config["nodes"]) != set(NODES):
            raise Rejected("invalid node registry")
        for node, config in self.config["nodes"].items():
            if not isinstance(config, dict) or set(config) != {"capabilities", "producer_sha256"}:
                raise Rejected("invalid node configuration")
            caps = config["capabilities"]
            if not isinstance(caps, list) or len(caps) != len(set(caps)) or any(
                    cap != "telemetry" for cap in caps):
                raise Rejected("unsupported capability; implement an adapter first")
            if not isinstance(config["producer_sha256"], str) or not HEX.fullmatch(
                    config["producer_sha256"]):
                raise Rejected("invalid producer artifact")
            key_for(self.state, node)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.db, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA synchronous=FULL")
            with db:
                yield db
        finally:
            db.close()

    def authenticate(self, envelope):
        if not isinstance(envelope, dict) or set(envelope) != FIELDS:
            raise Rejected("invalid envelope")
        if type(envelope["version"]) is not int or envelope["version"] != 1:
            raise Rejected("unknown protocol version")
        node = envelope["node_id"]
        if not isinstance(node, str) or node not in self.config["nodes"]:
            raise Rejected("unregistered node")
        signature = envelope["signature"]
        if not isinstance(signature, str) or not HEX.fullmatch(signature):
            raise Rejected("invalid authentication")
        try:
            valid = hmac.compare_digest(signature, sign(envelope, key_for(self.state, node)))
        except (ValueError, TypeError, RecursionError) as exc:
            raise Rejected("invalid canonical envelope") from exc
        if not valid:
            raise Rejected("invalid authentication")

    def validate(self, envelope, now):
        self.authenticate(envelope)  # Always before duplicate lookup.
        for key in ("event_id", "nonce"):
            if not isinstance(envelope[key], str) or not IDENTIFIER.fullmatch(envelope[key]):
                raise Rejected("invalid identifier")
        if envelope["kind"] not in ("heartbeat", "system_health"):
            raise Rejected("unsupported event kind")
        source, expiry = envelope["source_time"], envelope["expires_at"]
        if any(type(t) not in (int, float) or abs(t) > 1e15 or not math.isfinite(t)
               for t in (source, expiry)):
            raise Rejected("invalid timestamp")
        if not source <= now + FUTURE_SKEW or not source < expiry <= source + MAX_TTL:
            raise Rejected("invalid event lifetime")
        if expiry <= now or source < now - MAX_TTL:
            raise Rejected("stale event")
        payload = envelope["payload"]
        if not isinstance(payload, dict) or set(payload) != PAYLOAD_KEYS:
            raise Rejected("only bounded system metadata is accepted")
        if not isinstance(payload["producer_sha256"], str) or not HEX.fullmatch(payload["producer_sha256"]):
            raise Rejected("invalid artifact digest")
        if any(not isinstance(payload[k], str) or not re.fullmatch(r"[A-Za-z0-9_. -]{1,40}", payload[k])
               for k in ("os", "python")):
            raise Rejected("invalid metadata text")
        if type(payload["cpu_count"]) is not int or not 1 <= payload["cpu_count"] <= 4096:
            raise Rejected("invalid system metadata")
        if type(payload["synthetic"]) is not bool:
            raise Rejected("missing synthetic label")

    @staticmethod
    def digest(seq, received, envelope, previous):
        body = {"seq": seq, "received_at": received, "envelope": envelope,
                "previous_hash": previous}
        return hashlib.sha256(canonical(body).encode()).hexdigest()

    def _audit(self, db):
        previous, count = GENESIS, 0
        for row in db.execute("SELECT * FROM events ORDER BY seq"):
            count += 1
            envelope = decode(row["envelope"])
            self.authenticate(envelope)
            if (row["seq"] != count or row["previous_hash"] != previous
                    or row["event_id"] != envelope["event_id"]
                    or row["node_id"] != envelope["node_id"]
                    or row["nonce"] != envelope["nonce"]
                    or canonical(envelope) != row["envelope"]
                    or not math.isfinite(row["received_at"])):
                raise Rejected("audit integrity failure")
            expected = self.digest(count, row["received_at"], envelope, previous)
            if not hmac.compare_digest(expected, row["chain_hash"]):
                raise Rejected("audit integrity failure")
            previous = expected
        return {"verified": True, "events": count, "head_sha256": previous,
                "scope": "local hash-chain and node signatures; not tamperproof or externally anchored"}

    def audit(self):
        with self.lock, self.connect() as db:
            db.execute("BEGIN")
            return self._audit(db)

    def accept(self, envelope, *, now=None):
        now = time.time() if now is None else now
        self.validate(envelope, now)
        serialized = canonical(envelope)
        if len(serialized.encode()) > MAX_BODY:
            raise Rejected("event too large")
        with self.lock, self.connect() as db:
            db.execute("BEGIN IMMEDIATE")  # SQLite serializes writers across processes too.
            audit = self._audit(db)
            existing = db.execute("SELECT * FROM events WHERE event_id = ?",
                                  (envelope["event_id"],)).fetchone()
            if existing:
                if existing["envelope"] != serialized:
                    raise Rejected("conflicting event id")
                return {"accepted": True, "duplicate": True, "sequence": existing["seq"],
                        "receipt_sha256": existing["chain_hash"]}
            if db.execute("SELECT 1 FROM events WHERE node_id = ? AND nonce = ?",
                          (envelope["node_id"], envelope["nonce"])).fetchone():
                raise Rejected("reused nonce")
            seq = audit["events"] + 1
            digest = self.digest(seq, now, envelope, audit["head_sha256"])
            db.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (seq, envelope["event_id"], envelope["node_id"], envelope["nonce"],
                        now, serialized, audit["head_sha256"], digest))
            return {"accepted": True, "duplicate": False, "sequence": seq, "receipt_sha256": digest}

    def status(self, *, now=None):
        now = time.time() if now is None else now
        actual_digest = producer_digest()
        with self.lock, self.connect() as db:
            db.execute("BEGIN")  # Keep audit and node reads on one cross-process snapshot.
            audit = self._audit(db)
            result, verified = {}, 0
            for node, config in self.config["nodes"].items():
                row = db.execute("SELECT * FROM events WHERE node_id = ? ORDER BY seq DESC LIMIT 1",
                                 (node,)).fetchone()
                event = decode(row["envelope"]) if row else None
                fresh = bool(event and event["expires_at"] > now
                             and now - row["received_at"] <= MAX_TTL
                             and event["source_time"] <= now + FUTURE_SKEW)
                artifact = bool(event and actual_digest and actual_digest == config["producer_sha256"]
                                == event["payload"]["producer_sha256"])
                checks = {"fresh_signed_receipt": fresh, "local_artifact_and_signed_revision_match": artifact}
                verified += sum(checks.values())
                result[node] = {"online": fresh, "state": "online" if fresh else "unknown/offline",
                                "configured_capabilities": config["capabilities"],
                                "eligible_capabilities": config["capabilities"] if fresh and artifact else [],
                                "checks": checks, "last_receipt_at": row["received_at"] if row else None,
                                "source_time": event["source_time"] if event else None,
                                "expires_at": event["expires_at"] if event else None,
                                "synthetic": event["payload"]["synthetic"] if event else None}
            required = len(result) * 2
            return {"observed_at": now, "nodes": result, "audit": audit,
                    "core_adapter": "draft_export_only; no mission submission or execution",
                    "evidence_coverage": {"verified_checks": verified, "required_checks": required,
                                          "percent": round(100 * verified / required, 2),
                                          "meaning": "configured telemetry evidence coverage, not a truth, health, or deployment score"}}

    def route(self, capability, *, now=None):
        status = self.status(now=now)
        candidates = [(node, entry) for node, entry in status["nodes"].items()
                      if capability in entry["eligible_capabilities"]]
        if not candidates:
            return {"status": "blocked", "node": None, "reason": "no fresh node with verified supported capability"}
        node, entry = max(candidates, key=lambda item: (item[1]["last_receipt_at"], item[0]))
        return {"status": "eligible", "node": node, "capability": capability,
                "executed": False, "synthetic": entry["synthetic"]}


class LoopbackServer(HTTPServer):
    request_queue_size = 8

    def __init__(self, store, port=0):
        self.store = store
        self.reader_token = (store.state / "reader.key").read_text().strip()
        if not HEX.fullmatch(self.reader_token):
            raise Rejected("invalid reader token")
        super().__init__(("127.0.0.1", port), Handler)

    def get_request(self):
        sock, address = super().get_request()
        sock.settimeout(3)
        return sock, address


class Handler(BaseHTTPRequestHandler):
    server_version = "N95Receipt/0.1"
    sys_version = ""

    def log_message(self, *_):
        pass  # Do not log secrets, headers or payloads.

    def send_error(self, code, message=None, explain=None):
        self.reply(code, {"error": "request rejected"})

    def reply(self, code, body):
        raw = canonical(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        try:
            self.wfile.write(raw)
        except OSError:
            pass

    def valid_request_context(self):
        hosts = self.headers.get_all("Host", [])
        return (hosts == [f"127.0.0.1:{self.server.server_port}"]
                and not self.headers.get("Origin") and not self.headers.get("Sec-Fetch-Site"))

    def do_GET(self):
        if not self.valid_request_context():
            return self.reply(403, {"error": "request rejected"})
        if self.path == "/health":
            return self.reply(200, {"ok": True, "service": "n95-native-receipt"})
        if self.path != "/status":
            return self.reply(404, {"error": "request rejected"})
        authorization = self.headers.get_all("Authorization", [])
        expected = "Bearer " + self.server.reader_token
        if len(authorization) != 1 or not hmac.compare_digest(authorization[0], expected):
            return self.reply(401, {"error": "request rejected"})
        try:
            return self.reply(200, self.server.store.status())
        except (Rejected, OSError, sqlite3.Error):
            return self.reply(503, {"error": "request rejected"})

    def do_POST(self):
        if not self.valid_request_context():
            return self.reply(403, {"error": "request rejected"})
        if self.path != "/event":
            return self.reply(404, {"error": "request rejected"})
        lengths = self.headers.get_all("Content-Length", [])
        content_types = self.headers.get_all("Content-Type", [])
        if (self.headers.get("Transfer-Encoding") or len(lengths) != 1
                or content_types != ["application/json"] or not lengths[0].isdigit()):
            return self.reply(400, {"error": "request rejected"})
        length = int(lengths[0])
        if not 1 <= length <= MAX_BODY:
            return self.reply(413, {"error": "request rejected"})
        try:
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise Rejected("incomplete body")
            receipt = self.server.store.accept(decode(raw))
            return self.reply(200, receipt)
        except (Rejected, ValueError, TypeError, OSError, sqlite3.Error, RecursionError):
            return self.reply(400, {"error": "request rejected"})


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        fp.close()
        raise Rejected("redirects are disabled")


def http_json(url, path, *, envelope=None, token=None):
    parsed = urlsplit(url)
    if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or parsed.username
            or parsed.password or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        raise Rejected("only literal loopback URLs are supported")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(url.rstrip("/") + path, headers=headers,
                      data=canonical(envelope).encode() if envelope else None)
    # Avoid inherited proxies. This HTTP client is only for a local service/tunnel.
    with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=5) as response:
        return decode(response.read(MAX_BODY * 2))


def demo(state):
    state = Path(state)
    if not (state / "config.json").exists():
        init_state(state)
    store = Store(state)
    server = LoopbackServer(store)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    try:
        receipts = {node: http_json(url, "/event", envelope=make_envelope(state, node, synthetic=True))
                    for node in NODES}
        status = http_json(url, "/status", token=(state / "reader.key").read_text())
        return {"scope": "synthetic identities on one host, actual loopback HTTP and SQLite receipts",
                "physical_three_device_deployment": False, "receipts": receipts,
                "status": status, "audit": store.audit()}
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def watch(state, node, url, *, cycles=3, interval=30, _sleep=time.sleep):
    """Finite telemetry loop with a three-failure circuit breaker; no daemon."""
    if type(cycles) is not int or not 1 <= cycles <= 120:
        raise Rejected("cycles must be between 1 and 120")
    if type(interval) not in (int, float) or not 1 <= interval <= 300:
        raise Rejected("interval must be between 1 and 300 seconds")
    report = {"scope": "bounded telemetry only", "requested_cycles": cycles,
              "attempted_cycles": 0, "accepted_receipts": 0, "failures": 0,
              "completed": False, "stop_reason": "cycle_limit"}
    consecutive_failures = 0
    try:
        for iteration in range(cycles):
            report["attempted_cycles"] += 1
            try:
                receipt = http_json(url, "/event", envelope=make_envelope(state, node))
                if not isinstance(receipt, dict) or receipt.get("accepted") is not True:
                    raise Rejected("missing accepted receipt")
                report["accepted_receipts"] += 1
                consecutive_failures = 0
            except (Rejected, OSError, ValueError, TypeError):
                report["failures"] += 1
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    report["stop_reason"] = "three_consecutive_failures"
                    return report
            if iteration < cycles - 1:
                _sleep(interval)
        report["completed"] = True
    except KeyboardInterrupt:
        report["stop_reason"] = "operator_interrupt"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "serve", "pulse", "watch", "status", "demo", "audit"):
        current = sub.add_parser(command)
        current.add_argument("--state", required=True, type=Path)
        if command == "serve":
            current.add_argument("--port", type=int, default=8795)
        if command in ("pulse", "watch"):
            current.add_argument("--node", choices=NODES, required=True)
            current.add_argument("--url", default="http://127.0.0.1:8795")
        if command == "watch":
            current.add_argument("--cycles", type=int, default=3)
            current.add_argument("--interval", type=float, default=30)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            result = init_state(args.state)
        elif args.command == "demo":
            result = demo(args.state)
        elif args.command == "pulse":
            result = http_json(args.url, "/event", envelope=make_envelope(args.state, args.node))
        elif args.command == "watch":
            result = watch(args.state, args.node, args.url, cycles=args.cycles, interval=args.interval)
        elif args.command == "serve":
            server = LoopbackServer(Store(args.state), args.port)
            print(canonical({"listening": f"http://127.0.0.1:{server.server_port}"}), flush=True)
            try:
                server.serve_forever()
            finally:
                server.server_close()
            return 0
        else:
            store = Store(args.state)
            result = store.status() if args.command == "status" else store.audit()
        print(json.dumps(result, indent=2, allow_nan=False))
        return 1 if args.command == "watch" and (not result["completed"] or result["failures"]) else 0
    except KeyboardInterrupt:
        return 0
    except (Rejected, OSError, ValueError, TypeError, sqlite3.Error) as exc:
        # Paths, key data, payloads and remote response bodies never enter CLI error output.
        print(canonical({"ok": False, "error": "operation failed", "error_type": type(exc).__name__}))
        return 1
