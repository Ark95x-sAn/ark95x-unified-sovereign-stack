"""Adversarial checks for the isolated receipt transport (no physical device claims)."""
import copy
from contextlib import closing
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

from n95_native.bridge import (LoopbackServer, MAX_BODY, MAX_TTL, NODES, Rejected,
                               Store, canonical, decode, demo, http_json, init_state,
                               key_for, make_envelope, sign, watch)


class NativeBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="n95-native-test-")
        self.state = Path(self.temp.name) / "state"
        init_state(self.state)
        self.store = Store(self.state)
        self.now = time.time()

    def tearDown(self):
        self.temp.cleanup()

    def envelope(self, node="GM700"):
        return make_envelope(self.state, node, now=self.now, synthetic=True)

    def resign(self, envelope):
        envelope["signature"] = sign(envelope, key_for(self.state, envelope["node_id"]))
        return envelope

    def test_configured_nodes_are_offline_and_no_route_without_receipt(self):
        status = self.store.status(now=self.now)
        self.assertTrue(all(not node["online"] for node in status["nodes"].values()))
        self.assertEqual(status["evidence_coverage"]["verified_checks"], 0)
        self.assertEqual(status["evidence_coverage"]["required_checks"], 6)
        self.assertEqual(self.store.route("telemetry")["status"], "blocked")
        self.assertEqual(len({key_for(self.state, node) for node in NODES}), 3)

    def test_authenticated_idempotency_and_conflicting_replay(self):
        event = self.envelope()
        first = self.store.accept(event, now=self.now)
        repeat = self.store.accept(event, now=self.now)
        self.assertFalse(first["duplicate"])
        self.assertTrue(repeat["duplicate"])
        self.assertEqual(first["receipt_sha256"], repeat["receipt_sha256"])
        bad_auth = copy.deepcopy(event)
        bad_auth["signature"] = "0" * 64
        with self.assertRaises(Rejected):
            self.store.accept(bad_auth, now=self.now)
        conflict = copy.deepcopy(event)
        conflict["payload"]["cpu_count"] = 2 if event["payload"]["cpu_count"] != 2 else 3
        self.resign(conflict)
        with self.assertRaises(Rejected):
            self.store.accept(conflict, now=self.now)
        nonce_reuse = self.envelope()
        nonce_reuse["nonce"] = event["nonce"]
        self.resign(nonce_reuse)
        with self.assertRaises(Rejected):
            self.store.accept(nonce_reuse, now=self.now)
        self.assertEqual(self.store.audit()["events"], 1)

    def test_node_spoofing_and_unknown_node_rejected(self):
        event = self.envelope()
        event["node_id"] = "RTX2080"
        # A GM700 signature is not valid for the GPU node even with identical content.
        event["signature"] = sign(event, key_for(self.state, "GM700"))
        with self.assertRaises(Rejected):
            self.store.accept(event, now=self.now)
        event["node_id"] = "../../reader"
        with self.assertRaises(Rejected):
            self.store.accept(event, now=self.now)

    def test_stale_future_long_lifetime_and_invalid_numbers(self):
        for source, expiry in ((self.now - 200, self.now - 110),
                               (self.now + 30, self.now + 90),
                               (self.now, self.now + 91),
                               (self.now, self.now), (True, self.now + 10),
                               (10**1000, 10**1000)):
            with self.subTest(source=str(source)[:20]):
                event = self.envelope()
                event.update(source_time=source, expires_at=expiry)
                self.resign(event)
                with self.assertRaises(Rejected):
                    self.store.accept(event, now=self.now)
        event = self.envelope()
        event["payload"]["cpu_count"] = float("nan")
        with self.assertRaises(Rejected):
            self.store.accept(event, now=self.now)
        for raw in (b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1,"x":2}'):
            with self.assertRaises(Rejected):
                decode(raw)

    def test_medical_arbitrary_nested_and_nonfinite_metadata_disabled(self):
        for kind, extra in (("wearable", {}), ("medical", {}), ("health", {}),
                            ("system_health", {"heart_rate": 75}),
                            ("heartbeat", {"command": "whoami"}),
                            ("heartbeat", {"notes": {"anything": "nested"}})):
            event = self.envelope()
            event["kind"] = kind
            event["payload"].update(extra)
            self.resign(event)
            with self.assertRaises(Rejected):
                self.store.accept(event, now=self.now)
        self.assertEqual(self.store.audit()["events"], 0)

    def test_restart_preserves_receipt_and_expiry_blocks_route(self):
        receipt = self.store.accept(self.envelope(), now=self.now)
        reopened = Store(self.state)
        self.assertEqual(reopened.audit()["head_sha256"], receipt["receipt_sha256"])
        self.assertEqual(reopened.route("telemetry", now=self.now)["node"], "GM700")
        self.assertEqual(reopened.route("inference", now=self.now)["status"], "blocked")
        self.assertEqual(reopened.route("telemetry", now=self.now + MAX_TTL)["status"], "blocked")
        self.assertFalse(reopened.status(now=self.now + MAX_TTL)["nodes"]["GM700"]["online"])
        snapshot = reopened.status(now=self.now)
        self.assertEqual(snapshot["observed_at"], self.now)
        self.assertEqual(snapshot["nodes"]["GM700"]["source_time"], self.now)
        self.assertEqual(snapshot["nodes"]["GM700"]["expires_at"], self.now + MAX_TTL)

    def test_status_audit_and_node_evidence_use_same_cross_connection_snapshot(self):
        with closing(sqlite3.connect(self.store.db)) as db, db:
            db.execute("PRAGMA journal_mode=WAL")
        other_writer = Store(self.state)
        original_audit = self.store._audit

        def append_between_audit_and_node_reads(db):
            audit = original_audit(db)
            other_writer.accept(self.envelope(), now=self.now)
            return audit

        with patch.object(self.store, "_audit", side_effect=append_between_audit_and_node_reads):
            snapshot = self.store.status(now=self.now)
        self.assertEqual(snapshot["audit"]["events"], 0)
        self.assertFalse(snapshot["nodes"]["GM700"]["online"])
        live = self.store.status(now=self.now)
        self.assertEqual(live["audit"]["events"], 1)
        self.assertTrue(live["nodes"]["GM700"]["online"])

    def test_signed_but_wrong_artifact_cannot_route(self):
        event = self.envelope()
        event["payload"]["producer_sha256"] = "0" * 64
        self.store.accept(self.resign(event), now=self.now)
        status = self.store.status(now=self.now)
        self.assertTrue(status["nodes"]["GM700"]["online"])
        self.assertEqual(status["nodes"]["GM700"]["eligible_capabilities"], [])
        self.assertEqual(self.store.route("telemetry", now=self.now)["status"], "blocked")
        self.assertEqual(status["evidence_coverage"]["verified_checks"], 1)

    def test_hash_corruption_is_detected_before_append_or_restart(self):
        self.store.accept(self.envelope(), now=self.now)
        with closing(sqlite3.connect(self.store.db)) as db, db:
            db.execute("UPDATE events SET chain_hash = ?", ("0" * 64,))
        with self.assertRaises(Rejected):
            self.store.audit()
        with self.assertRaises(Rejected):
            self.store.accept(self.envelope(), now=self.now)
        with self.assertRaises(Rejected):
            Store(self.state)

    def test_nonce_and_payload_tampering_detected(self):
        self.store.accept(self.envelope(), now=self.now)
        with closing(sqlite3.connect(self.store.db)) as db, db:
            db.execute("UPDATE events SET nonce = ?", ("not-the-real-nonce",))
        with self.assertRaises(Rejected):
            self.store.audit()

    def test_store_connection_closes_after_commit_and_exceptional_rollback(self):
        with self.store.connect() as committed:
            committed.execute("CREATE TABLE connection_cleanup_probe (value INTEGER)")
            committed.execute("INSERT INTO connection_cleanup_probe VALUES (1)")
        with self.assertRaises(sqlite3.ProgrammingError):
            committed.execute("SELECT 1")

        with self.assertRaisesRegex(RuntimeError, "fixture rollback"):
            with self.store.connect() as rolled_back:
                rolled_back.execute("INSERT INTO connection_cleanup_probe VALUES (2)")
                raise RuntimeError("fixture rollback")
        with self.assertRaises(sqlite3.ProgrammingError):
            rolled_back.execute("SELECT 1")

        with self.store.connect() as reader:
            values = [row[0] for row in reader.execute("SELECT value FROM connection_cleanup_probe")]
        self.assertEqual(values, [1])
        with self.assertRaises(sqlite3.ProgrammingError):
            reader.execute("SELECT 1")

    def test_actual_http_three_node_demo_has_explicit_synthetic_scope(self):
        result = demo(self.state)
        self.assertFalse(result["physical_three_device_deployment"])
        self.assertEqual(set(result["receipts"]), set(NODES))
        self.assertEqual(len({r["receipt_sha256"] for r in result["receipts"].values()}), 3)
        self.assertTrue(all(n["synthetic"] for n in result["status"]["nodes"].values()))
        self.assertEqual(result["status"]["evidence_coverage"]["percent"], 100)
        self.assertEqual(Store(self.state).audit()["events"], 3)

    def test_http_blocks_browser_writes_oversize_bad_json_and_status_without_token(self):
        server = LoopbackServer(self.store)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base = f"http://127.0.0.1:{server.server_port}"
        opener = build_opener(ProxyHandler({}))
        try:
            self.assertEqual(server.server_address[0], "127.0.0.1")
            self.assertTrue(http_json(base, "/health")["ok"])
            with self.assertRaises(HTTPError) as error:
                http_json(base, "/status")
            self.assertEqual(error.exception.code, 401)
            token = (self.state / "reader.key").read_text()
            self.assertEqual(http_json(base, "/status", token=token)["audit"]["events"], 0)
            event_raw = canonical(self.envelope()).encode()
            for raw, extra, expected in (
                    (event_raw, {"Origin": "https://attacker.invalid"}, 403),
                    (event_raw, {"Sec-Fetch-Site": "same-origin"}, 403),
                    (event_raw, {"Host": "attacker.invalid"}, 403),
                    (b"x" * (MAX_BODY + 1), {}, 413),
                    (b'{"x":NaN}', {}, 400),
                    (b'{"x":1,"x":2}', {}, 400)):
                request = Request(base + "/event", data=raw,
                                  headers={"Content-Type": "application/json", **extra})
                with self.assertRaises(HTTPError) as error:
                    opener.open(request, timeout=5)
                self.assertEqual(error.exception.code, expected)
                self.assertEqual(json.loads(error.exception.read()), {"error": "request rejected"})
            self.assertEqual(self.store.audit()["events"], 0)
        finally:
            server.shutdown()
            worker.join(timeout=5)
            server.server_close()

    def test_state_initialization_is_exclusive_and_node_client_needs_only_own_key(self):
        with self.assertRaises(Rejected):
            init_state(self.state)
        client_state = Path(self.temp.name) / "client"
        (client_state / "nodes").mkdir(parents=True)
        (client_state / "nodes" / "SURFACE.key").write_bytes(
            (self.state / "nodes" / "SURFACE.key").read_bytes())
        event = make_envelope(client_state, "SURFACE", now=self.now)
        self.assertTrue(self.store.accept(event, now=self.now)["accepted"])
        with self.assertRaises(Rejected):
            make_envelope(client_state, "GM700", now=self.now)

    def test_bounded_watch_stops_and_opens_circuit_after_three_failures(self):
        sent = []

        def deliver(url, path, *, envelope):
            sent.append(envelope)
            return self.store.accept(envelope)

        with patch("n95_native.bridge.http_json", side_effect=deliver):
            report = watch(self.state, "GM700", "http://127.0.0.1:8795",
                           cycles=3, interval=1, _sleep=lambda _: None)
        self.assertTrue(report["completed"])
        self.assertEqual(report["accepted_receipts"], 3)
        self.assertEqual(len({e["nonce"] for e in sent}), 3)
        with patch("n95_native.bridge.http_json", side_effect=OSError("fixture outage")):
            report = watch(self.state, "GM700", "http://127.0.0.1:8795",
                           cycles=10, interval=1, _sleep=lambda _: None)
        self.assertFalse(report["completed"])
        self.assertEqual(report["attempted_cycles"], 3)
        self.assertEqual(report["stop_reason"], "three_consecutive_failures")
        for cycles, interval in ((0, 1), (121, 1), (3, 0), (3, float("nan"))):
            with self.assertRaises(Rejected):
                watch(self.state, "GM700", "http://127.0.0.1:8795", cycles=cycles,
                      interval=interval, _sleep=lambda _: None)

    def test_http_redirect_cannot_forward_reader_token_to_another_host(self):
        destination_requests = []

        class RedirectHandler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_GET(self):
                if self.path == "/status":
                    self.send_response(302)
                    self.send_header("Location", f"http://localhost:{self.server.server_port}/leak")
                else:
                    destination_requests.append(self.headers.get("Authorization"))
                    self.send_response(200)
                self.send_header("Content-Length", "0")
                self.end_headers()

        server = HTTPServer(("127.0.0.1", 0), RedirectHandler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            with self.assertRaises(Rejected):
                http_json(f"http://127.0.0.1:{server.server_port}", "/status", token="test-only-reader")
            self.assertEqual(destination_requests, [])
        finally:
            server.shutdown()
            worker.join(timeout=5)
            server.server_close()


if __name__ == "__main__":
    unittest.main()
