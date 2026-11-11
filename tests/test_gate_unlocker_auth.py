"""Operator-auth regressions for gate unlock.

/unlock must accept only operator credentials from the environment.
A forwarded admin token must fail, valid operator credentials must succeed,
and absent or malformed credentials must fail closed and be logged.
"""
import importlib
import inspect
import secrets
import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from loguru import logger

ROOT = Path(__file__).resolve().parents[1]
FORWARDED = "X-Flamegate-Token"
OPERATOR_ID = "X-Operator-Id"
OPERATOR_SECRET = "X-Operator-Secret"


def _load(monkeypatch, tmp_path, operator_id, operator_secret):
    monkeypatch.setenv("GATE_STATE_DB", str(tmp_path / "gate_states.db"))
    monkeypatch.delenv("FLAMEGATE_ADMIN_TOKEN", raising=False)
    if operator_id is None:
        monkeypatch.delenv("GATE_OPERATOR_ID", raising=False)
    else:
        monkeypatch.setenv("GATE_OPERATOR_ID", operator_id)
    if operator_secret is None:
        monkeypatch.delenv("GATE_OPERATOR_SECRET", raising=False)
    else:
        monkeypatch.setenv("GATE_OPERATOR_SECRET", operator_secret)
    sys.modules.pop("core.gate_unlocker", None)
    return importlib.import_module("core.gate_unlocker")


def _auth(operator_id, operator_secret):
    return {OPERATOR_ID: operator_id, OPERATOR_SECRET: operator_secret}


@pytest.fixture
def gate(monkeypatch, tmp_path):
    operator_id = "gate-operator"
    operator_secret = secrets.token_hex(32)
    mod = _load(monkeypatch, tmp_path, operator_id, operator_secret)
    yield TestClient(mod.app), operator_id, operator_secret
    sys.modules.pop("core.gate_unlocker", None)


def _journal(client):
    return client.get("/journal").json()["journal"]


def _assert_secret_not_recorded(client, operator_secret):
    body = client.get("/journal").text
    assert operator_secret not in body
    assert operator_secret not in client.get("/health").text


@pytest.mark.parametrize(
    ("operator_id", "operator_secret"),
    [
        (None, None),
        ("gate-operator", None),
        (None, "d" * 32),
        ("", ""),
        ("gate-operator", "short"),
        ("gate-operator", "d" * 31),
        (" ", "d" * 32),
        ("gate-operator", "d" * 32 + " "),
    ],
)
def test_refuses_to_start_without_valid_operator_credentials(monkeypatch, tmp_path, operator_id, operator_secret):
    with pytest.raises(RuntimeError) as exc:
        _load(monkeypatch, tmp_path, operator_id, operator_secret)
    if operator_secret:
        assert operator_secret not in str(exc.value)
    sys.modules.pop("core.gate_unlocker", None)


def test_forwarded_token_does_not_unlock(gate):
    client, _operator_id, operator_secret = gate
    headers = {FORWARDED: "f" * 64}
    for path, body in (("/unlock", {"gate_id": "gate_core", "council_override": True}), ("/unlock-all", None)):
        if body is None:
            response = client.post(path, headers=headers)
        else:
            response = client.post(path, json=body, headers=headers)
        assert response.status_code == 401
        assert response.json()["detail"] == "Missing or invalid operator credentials"
    assert client.get("/gates/gate_core").json()["state"] == "locked"
    assert client.get("/health").json()["unlocked_gates"] == 0
    failure = _journal(client)[0]
    assert failure["action"] == "auth_failed"
    assert failure["previous_state"] == "missing:forwarded_token"
    assert failure["actor"] == "unauthenticated"
    assert operator_secret not in str(failure)


def test_forwarded_token_is_ignored_when_it_matches_admin_env(monkeypatch, tmp_path):
    admin = "b" * 64
    monkeypatch.setenv("FLAMEGATE_ADMIN_TOKEN", admin)
    operator_secret = "c" * 32
    mod = _load(monkeypatch, tmp_path, "gate-operator", operator_secret)
    client = TestClient(mod.app)
    response = client.post(
        "/unlock",
        json={"gate_id": "gate_core"},
        headers={FORWARDED: admin},
    )
    assert response.status_code == 401
    assert client.get("/gates/gate_core").json()["state"] == "locked"
    assert admin not in client.get("/journal").text
    sys.modules.pop("core.gate_unlocker", None)


def test_valid_operator_credentials_unlock(gate):
    client, operator_id, operator_secret = gate
    response = client.post(
        "/unlock",
        json={"gate_id": "gate_core"},
        headers=_auth(operator_id, operator_secret),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "unlocked"
    assert client.get("/gates/gate_core").json()["state"] == "unlocked"
    assert _journal(client)[0]["action"] == "unlock"
    _assert_secret_not_recorded(client, operator_secret)

    bulk = client.post("/unlock-all", headers=_auth(operator_id, operator_secret))
    assert bulk.status_code == 200
    assert bulk.json()["status"] == "bulk_unlocked"
    assert bulk.json()["count"] > 0
    actions = [row["action"] for row in _journal(client)]
    assert actions.count("unlock_all") == bulk.json()["count"]


def test_absent_credentials_fail_closed_and_are_logged(gate):
    client, _operator_id, operator_secret = gate
    records = []
    sink = logger.add(lambda message: records.append(str(message)), level="WARNING")
    try:
        response = client.post("/unlock", json={"gate_id": "gate_core"})
    finally:
        logger.remove(sink)
    assert response.status_code == 401
    assert client.get("/gates/gate_core").json()["state"] == "locked"
    assert any("unlock refused" in rec and "reason=missing" in rec and "relayed_token=False" in rec for rec in records)
    failure = _journal(client)[0]
    assert failure["action"] == "auth_failed"
    assert failure["previous_state"] == "missing"
    assert failure["source"]
    assert operator_secret not in str(failure)
    assert operator_secret not in "".join(records)


@pytest.mark.parametrize(
    "headers_builder",
    [
        lambda operator_id, _secret: {OPERATOR_ID: operator_id, OPERATOR_SECRET: "short"},
        lambda operator_id, _secret: {OPERATOR_ID: "bad id", OPERATOR_SECRET: "e" * 32},
        lambda _operator_id, _secret: {OPERATOR_ID: "", OPERATOR_SECRET: ""},
    ],
)
def test_malformed_credentials_fail_closed_and_are_logged(gate, headers_builder):
    client, operator_id, operator_secret = gate
    records = []
    sink = logger.add(lambda message: records.append(str(message)), level="WARNING")
    try:
        response = client.post(
            "/unlock",
            json={"gate_id": "gate_core"},
            headers=headers_builder(operator_id, operator_secret),
        )
    finally:
        logger.remove(sink)
    assert response.status_code == 401
    assert client.get("/gates/gate_core").json()["state"] == "locked"
    assert any("reason=malformed" in rec or "reason=missing" in rec for rec in records)
    assert _journal(client)[0]["action"] == "auth_failed"
    assert operator_secret not in client.get("/journal").text


def test_wrong_operator_credentials_are_rejected(gate):
    client, operator_id, operator_secret = gate
    response = client.post(
        "/unlock",
        json={"gate_id": "gate_core"},
        headers=_auth(operator_id, "e" * 32),
    )
    assert response.status_code == 401
    assert client.get("/gates/gate_core").json()["state"] == "locked"
    assert _journal(client)[0]["previous_state"] == "rejected"
    assert operator_secret not in client.get("/journal").text


def test_council_gate_stays_locked_without_override(gate):
    client, operator_id, operator_secret = gate
    response = client.post(
        "/unlock",
        json={"gate_id": "gate_flamegate"},
        headers=_auth(operator_id, operator_secret),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "council_required"
    assert client.get("/gates/gate_flamegate").json()["state"] == "locked"


def test_unlock_rolls_back_when_journal_write_fails(gate, monkeypatch):
    client, operator_id, operator_secret = gate
    mod = sys.modules["core.gate_unlocker"]

    def boom(*_args, **_kwargs):
        raise sqlite3.OperationalError("journal failed")

    monkeypatch.setattr(mod, "append_journal", boom)
    with pytest.raises(sqlite3.OperationalError):
        client.post(
            "/unlock",
            json={"gate_id": "gate_core"},
            headers=_auth(operator_id, operator_secret),
        )
    assert client.get("/gates/gate_core").json()["state"] == "locked"


def test_dashboard_and_council_do_not_relay_unlock():
    dashboard = (ROOT / "command" / "dashboard.py").read_text()
    council = (ROOT / "flame" / "council.py").read_text()
    assert FORWARDED not in dashboard
    assert "FLAMEGATE_ADMIN_TOKEN" not in dashboard
    assert "GATE_OPERATOR_SECRET" not in dashboard
    assert FORWARDED not in council
    assert "FLAMEGATE_ADMIN_TOKEN" not in council
    assert "GATE_OPERATOR_SECRET" not in council
    assert "/unlock" not in council

    import command.dashboard as dashboard_mod
    import flame.council as council_mod

    dashboard_src = inspect.getsource(dashboard_mod.unlock_gate)
    council_src = inspect.getsource(council_mod.gate_vote)
    assert "httpx" not in dashboard_src
    assert "/unlock" not in dashboard_src
    assert "httpx" not in council_src
    assert "/unlock" not in council_src
    assert "headers" not in council_src

    alert, audit = dashboard_mod.unlock_gate(1, "gate_core", [])
    assert "cannot mint, relay, or replay" in alert.children
    assert "REFUSED" in audit[0]
    page = dashboard_mod.app.server.test_client()
    layout = page.get("/_dash-layout").get_data(as_text=True)
    assert "cannot unlock gates" in layout
    callback = page.post(
        "/_dash-update-component",
        json={
            "output": "..unlock-result.children...audit-entries.data..",
            "outputs": [
                {"id": "unlock-result", "property": "children"},
                {"id": "audit-entries", "property": "data"},
            ],
            "inputs": [{"id": "unlock-btn", "property": "n_clicks", "value": 1}],
            "changedPropIds": ["unlock-btn.n_clicks"],
            "state": [
                {"id": "gate-select", "property": "value", "value": "gate_core"},
                {"id": "audit-entries", "property": "data", "value": []},
            ],
        },
    )
    assert callback.status_code == 200
    assert "cannot mint, relay, or replay" in callback.get_data(as_text=True)


def test_flamegate_refuses_to_start_without_token(monkeypatch, tmp_path):
    monkeypatch.delenv("FLAMEGATE_ADMIN_TOKEN", raising=False)
    monkeypatch.setenv("FLAMEGATE_AUDIT_DB", str(tmp_path / "audit.db"))
    sys.modules.pop("flame.flamegate_tls", None)
    try:
        with pytest.raises(RuntimeError):
            importlib.import_module("flame.flamegate_tls")
    finally:
        sys.modules.pop("flame.flamegate_tls", None)


def test_flamegate_blocks_unlock_relay(monkeypatch, tmp_path):
    token = "a" * 64
    monkeypatch.setenv("FLAMEGATE_ADMIN_TOKEN", token)
    monkeypatch.setenv("FLAMEGATE_AUDIT_DB", str(tmp_path / "audit.db"))
    sys.modules.pop("flame.flamegate_tls", None)
    try:
        mod = importlib.import_module("flame.flamegate_tls")

        class Boom:
            def __init__(self, *_args, **_kwargs):
                raise AssertionError("Flamegate attempted to relay an unlock")

        monkeypatch.setattr(mod.httpx, "AsyncClient", Boom)
        client = TestClient(mod.app)
        response = client.post(
            "/flamegate/proxy",
            json={
                "target": "gate_unlocker",
                "method": "POST",
                "path": "/unlock",
                "body": {"gate_id": "gate_core", "council_override": True},
            },
            headers={FORWARDED: token},
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Gate unlock cannot be relayed"
        audit = client.get("/flamegate/audit", headers={FORWARDED: token}).json()["audit_log"]
        assert audit[0]["action"] == "unlock_relay_blocked"
        assert token not in response.text
    finally:
        sys.modules.pop("flame.flamegate_tls", None)


def test_compose_requires_external_operator_credentials():
    text = (ROOT / "docker-compose.yml").read_text()
    assert "FLAMEGATE_ADMIN_TOKEN:-" not in text
    assert "GATE_OPERATOR_ID=${GATE_OPERATOR_ID:?" in text
    assert "GATE_OPERATOR_SECRET=${GATE_OPERATOR_SECRET:?" in text
    dashboard = text.split("  dashboard:", 1)[1].split("  flamegate:", 1)[0]
    council = text.split("  council:", 1)[1].split("  shadow-agent:", 1)[0]
    unlocker = text.split("  gate-unlocker:", 1)[1].split("  council:", 1)[0]
    flamegate = text.split("  flamegate:", 1)[1].split("  comet-router:", 1)[0]
    for block in (dashboard, council):
        assert "FLAMEGATE_ADMIN_TOKEN" not in block
        assert "GATE_OPERATOR_SECRET" not in block
        assert "GATE_OPERATOR_ID" not in block
    assert "FLAMEGATE_ADMIN_TOKEN" not in unlocker
    assert "GATE_OPERATOR_SECRET" not in flamegate
    example = (ROOT / ".env.example").read_text()
    for name in ("FLAMEGATE_ADMIN_TOKEN", "GATE_OPERATOR_ID", "GATE_OPERATOR_SECRET"):
        assert f"{name}=" in example
        assert f"{name}=\"\"" not in example
        valued = [line for line in example.splitlines() if line.startswith(f"{name}=") and line.strip() != f"{name}="]
        assert valued == []
