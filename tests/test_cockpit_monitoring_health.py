"""ARK95X Cockpit <-> Monitoring Adapter integration tests. Proves
GET /monitoring/health runs the real health check against the cockpit's
actual engine/control_plane and reports through the plane."""
import pytest
from fastapi.testclient import TestClient

import cockpit.app as cockpit_app
from passive_income_engine import PassiveIncomeEngine
from control_plane import build_default_control_plane


@pytest.fixture
def client(tmp_path, monkeypatch):
    persist_path = tmp_path / "ledger_state.json"
    engine = PassiveIncomeEngine(starting_balance=10000.0, persist_path=str(persist_path))
    plane = build_default_control_plane()
    monkeypatch.setattr(cockpit_app, "engine", engine)
    monkeypatch.setattr(cockpit_app, "control_plane", plane)
    return TestClient(cockpit_app.app), plane


def test_monitoring_health_reflects_real_ledger_and_reports(client):
    test_client, plane = client

    r = test_client.get("/monitoring/health")

    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert body["ledger_ok"] is True
    assert "checks" in body  # real TCP probe results, whatever they are here

    agent = plane.agents["monitoring"]
    assert agent.state == "healthy"
    assert agent.last_report["ledger_ok"] is True
