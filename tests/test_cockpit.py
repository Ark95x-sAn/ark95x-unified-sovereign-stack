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


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Fresh engine/ledger per test so cockpit state doesn't leak between tests."""
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
    payload = {"symbol": "BTCUSD", "side": "long", "entry_price": 100.0, "stop_price": 95.0}
    order = client.post("/netx/webhook", json=payload).json()

    fill = client.post("/fills", json={"order_id": order["order_id"], "exit_price": 110.0}).json()
    assert fill["kind"] == "ledger_entry"
    assert fill["amount_usd"] == pytest.approx(200.0)  # 20 * (110 - 100)

    roi = client.get("/roi").json()
    assert roi["ledger_snapshot"]["total_pnl_usd"] == pytest.approx(200.0)
    assert roi["ledger_snapshot"]["roi_pct"] == pytest.approx(2.0)


def test_fill_unknown_order_returns_404(client):
    r = client.post("/fills", json={"order_id": "does-not-exist", "exit_price": 100.0})
    assert r.status_code == 404


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
