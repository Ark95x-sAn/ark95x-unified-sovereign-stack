"""Auth tests for core.gate_unlocker: /unlock and /unlock-all must require the admin token."""
import importlib
import secrets
import sys

import pytest
from fastapi.testclient import TestClient

HEADER = "X-Flamegate-Token"


def _load(monkeypatch, tmp_path, token):
    monkeypatch.setenv("GATE_STATE_DB", str(tmp_path / "gate_states.db"))
    if token is None:
        monkeypatch.delenv("FLAMEGATE_ADMIN_TOKEN", raising=False)
    else:
        monkeypatch.setenv("FLAMEGATE_ADMIN_TOKEN", token)
    sys.modules.pop("core.gate_unlocker", None)
    return importlib.import_module("core.gate_unlocker")


@pytest.fixture
def gate(monkeypatch, tmp_path):
    token = secrets.token_hex(32)
    mod = _load(monkeypatch, tmp_path, token)
    yield TestClient(mod.app), token
    sys.modules.pop("core.gate_unlocker", None)


def test_refuses_to_start_without_token(monkeypatch, tmp_path):
    with pytest.raises(RuntimeError):
        _load(monkeypatch, tmp_path, None)
    sys.modules.pop("core.gate_unlocker", None)


@pytest.mark.parametrize("headers", [{}, {HEADER: ""}, {HEADER: "wrong-token"}])
def test_unlock_rejects_missing_or_wrong_token(gate, headers):
    client, _ = gate
    r = client.post("/unlock", json={"gate_id": "gate_core"}, headers=headers)
    assert r.status_code == 401
    # gate must still be locked
    assert client.get("/gates/gate_core").json()["state"] == "locked"


@pytest.mark.parametrize("headers", [{}, {HEADER: ""}, {HEADER: "wrong-token"}])
def test_unlock_all_rejects_missing_or_wrong_token(gate, headers):
    client, _ = gate
    r = client.post("/unlock-all", headers=headers)
    assert r.status_code == 401
    assert client.get("/health").json()["unlocked_gates"] == 0


def test_unlock_succeeds_with_correct_token(gate):
    client, token = gate
    r = client.post("/unlock", json={"gate_id": "gate_core"}, headers={HEADER: token})
    assert r.status_code == 200
    assert r.json()["status"] == "unlocked"


def test_unlock_all_succeeds_with_correct_token(gate):
    client, token = gate
    r = client.post("/unlock-all", headers={HEADER: token})
    assert r.status_code == 200
    assert r.json()["status"] == "bulk_unlocked"
    assert r.json()["count"] > 0
