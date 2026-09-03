"""ARK95X Cockpit - FastAPI + WebSocket integration tests
Verifies the ROI ledger + leverage meter endpoints and the /ws/cockpit
WebSocket broadcast real, non-decorative numbers end-to-end.
"""
import pytest
from fastapi.testclient import TestClient

import cockpit.app as cockpit_app
from passive_income_engine import PassiveIncomeEngine
from ledger.command_ledger import CommandLedger
from netx.risk_calculator import RiskCalculator
from control_plane import build_default_control_plane


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Fresh engine/ledger per test, control plane OFF -- exercises the
    original ungated /fills contract (immediate execution)."""
    persist_path = tmp_path / "ledger_state.json"
    engine = PassiveIncomeEngine(starting_balance=10000.0, persist_path=str(persist_path))
    ledger = CommandLedger(
        engine=engine,
        risk_calculator=RiskCalculator(),
        risk_pct=1.0,
        on_telemetry=cockpit_app.manager.broadcast,
    )
    monkeypatch.setattr(cockpit_app, "engine", engine)
    monkeypatch.setattr(cockpit_app, "ledger", ledger)
    monkeypatch.setattr(cockpit_app, "control_plane", None)
    return TestClient(cockpit_app.app)


@pytest.fixture
def gated_client(tmp_path, monkeypatch):
    """Fresh engine/ledger/control_plane per test -- exercises the default,
    control-plane-gated /fills contract (queue -> approve)."""
    persist_path = tmp_path / "ledger_state.json"
    engine = PassiveIncomeEngine(starting_balance=10000.0, persist_path=str(persist_path))
    plane = build_default_control_plane()
    ledger = CommandLedger(
        engine=engine,
        risk_calculator=RiskCalculator(),
        risk_pct=1.0,
        on_telemetry=cockpit_app.manager.broadcast,
        control_plane=plane,
    )
    monkeypatch.setattr(cockpit_app, "engine", engine)
    monkeypatch.setattr(cockpit_app, "ledger", ledger)
    monkeypatch.setattr(cockpit_app, "control_plane", plane)
    return TestClient(cockpit_app.app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_roi_endpoint_reflects_real_zero_state(client):
    r = client.get("/roi")
    body = r.json()
    assert body["kind"] == "telemetry_event"
    assert body["ledger_snapshot"]["total_pnl_usd"] == 0.0
    assert body["ledger_snapshot"]["roi_pct"] == 0.0


def test_netx_webhook_sizes_real_order(client):
    payload = {"symbol": "BTCUSD", "side": "long", "entry_price": 100.0, "stop_price": 95.0}
    r = client.post("/netx/webhook", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "risk_sized_order"
    assert body["approved"] is True
    assert body["position_size"] == pytest.approx(20.0)  # 10000 * 1% / 5


def test_netx_webhook_rejects_bad_signal(client):
    payload = {"symbol": "BTCUSD", "side": "sideways", "entry_price": 100.0, "stop_price": 95.0}
    r = client.post("/netx/webhook", json=payload)
    assert r.status_code == 422


def test_fill_records_real_pnl_and_updates_roi(client):
    """Control plane OFF: /fills executes immediately, as before."""
    payload = {"symbol": "BTCUSD", "side": "long", "entry_price": 100.0, "stop_price": 95.0}
    order = client.post("/netx/webhook", json=payload).json()

    fill = client.post("/fills", json={"order_id": order["order_id"], "exit_price": 110.0}).json()
    assert fill["disposition"] == "executed_no_gate"
    assert fill["entry"]["kind"] == "ledger_entry"
    assert fill["entry"]["amount_usd"] == pytest.approx(200.0)  # 20 * (110 - 100)

    roi = client.get("/roi").json()
    assert roi["ledger_snapshot"]["total_pnl_usd"] == pytest.approx(200.0)
    assert roi["ledger_snapshot"]["roi_pct"] == pytest.approx(2.0)


def test_fill_unknown_order_returns_404(client):
    r = client.post("/fills", json={"order_id": "does-not-exist", "exit_price": 100.0})
    assert r.status_code == 404


def test_control_plane_disabled_reports_correctly(client):
    r = client.get("/control-plane")
    assert r.json() == {"control_plane_enabled": False}
    r = client.get("/pending")
    assert r.json() == {"control_plane_enabled": False, "pending": []}
    r = client.post("/approve/does-not-matter")
    assert r.status_code == 409


class TestControlPlaneGatedFills:
    """Control plane ON (the cockpit's real default): /fills queues a
    financial action for human approval; money only moves on /approve."""

    def test_fill_queues_instead_of_executing(self, gated_client):
        payload = {"symbol": "BTCUSD", "side": "long", "entry_price": 100.0, "stop_price": 95.0}
        order = gated_client.post("/netx/webhook", json=payload).json()

        fill = gated_client.post("/fills", json={"order_id": order["order_id"], "exit_price": 110.0}).json()
        assert fill["disposition"] == "queued_for_human_approval"
        assert "request_id" in fill

        # No money has moved yet.
        roi = gated_client.get("/roi").json()
        assert roi["ledger_snapshot"]["total_pnl_usd"] == 0.0

    def test_pending_endpoint_shows_the_queued_action(self, gated_client):
        payload = {"symbol": "BTCUSD", "side": "long", "entry_price": 100.0, "stop_price": 95.0}
        order = gated_client.post("/netx/webhook", json=payload).json()
        fill = gated_client.post("/fills", json={"order_id": order["order_id"], "exit_price": 110.0}).json()

        pending = gated_client.get("/pending").json()
        assert pending["control_plane_enabled"] is True
        request_ids = [r["request_id"] for r in pending["pending"]]
        assert fill["request_id"] in request_ids

    def test_approve_executes_and_updates_roi(self, gated_client):
        payload = {"symbol": "BTCUSD", "side": "long", "entry_price": 100.0, "stop_price": 95.0}
        order = gated_client.post("/netx/webhook", json=payload).json()
        fill = gated_client.post("/fills", json={"order_id": order["order_id"], "exit_price": 110.0}).json()

        approved = gated_client.post(f"/approve/{fill['request_id']}").json()
        assert approved["kind"] == "ledger_entry"
        assert approved["amount_usd"] == pytest.approx(200.0)

        roi = gated_client.get("/roi").json()
        assert roi["ledger_snapshot"]["total_pnl_usd"] == pytest.approx(200.0)

    def test_approve_unknown_request_id_returns_404(self, gated_client):
        r = gated_client.post("/approve/not-a-real-request-id")
        assert r.status_code == 404

    def test_control_plane_snapshot_shows_registered_agents(self, gated_client):
        snapshot = gated_client.get("/control-plane").json()
        assert snapshot["control_plane_enabled"] is True
        assert snapshot["agent_count"] == 8
        assert "business_ops" in snapshot["agents"]


def test_websocket_receives_initial_snapshot(client):
    with client.websocket_connect("/ws/cockpit") as ws:
        data = ws.receive_json()
        assert data["kind"] == "telemetry_event"
        assert data["event_type"] == "roi_update"
        assert data["ledger_snapshot"]["total_pnl_usd"] == 0.0


def test_websocket_receives_live_update_on_signal(client):
    with client.websocket_connect("/ws/cockpit") as ws:
        ws.receive_json()  # initial snapshot on connect
        payload = {"symbol": "ETHUSD", "side": "long", "entry_price": 50.0, "stop_price": 48.0}
        client.post("/netx/webhook", json=payload)
        event = ws.receive_json()
        assert event["kind"] == "telemetry_event"
        assert event["event_type"] == "leverage_update"
        assert event["broadcast"] is True


class TestFailoverDispatchEndpoint:
    """POST /failover/dispatch: the HTTP path n8n (or anything else) uses to
    trigger router/failover.py's dispatch_next() without needing python3,
    git, or a repo checkout in the caller's own runtime."""

    def test_dispatches_next_pending_task(self, client, tmp_path, monkeypatch):
        import json
        state_path = tmp_path / "ARK-STATE.json"
        state_path.write_text(json.dumps({
            "updated_at": "2026-01-01T00:00:00Z", "updated_by": "test",
            "todo_queue": [{"id": "P1", "phase": 99, "title": "x", "status": "pending", "depends_on": []}],
        }))
        monkeypatch.setattr(cockpit_app, "ARK_STATE_PATH", str(state_path))

        # No ANTHROPIC_API_KEY/GROQ_API_KEY/GEMINI_API_KEY and no local Ollama
        # in the test environment -- honestly reports no backend available,
        # same as the router does standalone.
        result = client.post("/failover/dispatch").json()
        assert result["status"] in ("no_backend_available", "dispatched")
        assert result["task_id"] == "P1"

    def test_no_pending_tasks(self, client, tmp_path, monkeypatch):
        import json
        state_path = tmp_path / "ARK-STATE.json"
        state_path.write_text(json.dumps({
            "updated_at": "2026-01-01T00:00:00Z", "updated_by": "test",
            "todo_queue": [{"id": "P1", "phase": 99, "title": "x", "status": "done", "depends_on": []}],
        }))
        monkeypatch.setattr(cockpit_app, "ARK_STATE_PATH", str(state_path))

        result = client.post("/failover/dispatch").json()
        assert result == {"status": "no_pending_tasks"}
