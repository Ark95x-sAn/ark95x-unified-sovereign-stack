"""Control-plane auth, proxy allowlist, and signature checks.

Fail-closed modules read FLAMEGATE_ADMIN_TOKEN and FLAME_SIGNATURES at import
time, so those values are set before the application imports below.
"""
import os
import tempfile
from pathlib import Path

from fastapi import HTTPException
from fastapi.testclient import TestClient

TOKEN = "a" * 32
_TMP = tempfile.mkdtemp(prefix="ark95x-sec-")
os.environ["FLAMEGATE_ADMIN_TOKEN"] = TOKEN
os.environ["GATE_STATE_DB"] = str(Path(_TMP) / "gates.db")
os.environ["FLAMEGATE_AUDIT_DB"] = str(Path(_TMP) / "audit.db")
os.environ["APP_ENV"] = "production"
os.environ["FLAME_SIGNATURES"] = "unit-test-signature"

from core import comet_router, gate_unlocker, hlm_trinity_router  # noqa: E402
from flame import council, flamegate_tls  # noqa: E402


AUTH = {"X-Flamegate-Token": TOKEN}


class TestGateUnlockerAuth:
    def setup_method(self):
        self.client = TestClient(gate_unlocker.app)

    def test_health_remains_public(self):
        assert self.client.get("/health").status_code == 200

    def test_unlock_without_token_is_forbidden(self):
        response = self.client.post("/unlock", json={"gate_id": "gate_core"})
        assert response.status_code == 403

    def test_unlock_all_without_token_is_forbidden(self):
        response = self.client.post("/unlock-all")
        assert response.status_code == 403

    def test_unlock_with_token_succeeds(self):
        response = self.client.post(
            "/unlock",
            json={"gate_id": "gate_core", "actor": "test"},
            headers=AUTH,
        )
        assert response.status_code == 200
        assert response.json()["status"] in {"unlocked", "already_unlocked"}

    def test_council_override_still_requires_token(self):
        response = self.client.post(
            "/unlock",
            json={"gate_id": "gate_flamegate", "council_override": True},
        )
        assert response.status_code == 403


class TestCometRouterAuth:
    def setup_method(self):
        self.client = TestClient(comet_router.app)

    def test_health_remains_public(self):
        assert self.client.get("/health").status_code == 200

    def test_route_without_token_is_forbidden(self):
        response = self.client.post("/route", json={"prompt": "hello"})
        assert response.status_code == 403


class TestCouncilGateVoteAuth:
    def setup_method(self):
        self.client = TestClient(council.app)

    def test_gate_vote_without_token_is_forbidden(self):
        response = self.client.post("/gate-vote", params={"gate_id": "gate_core"})
        assert response.status_code == 403


class TestFlamegateAllowlist:
    def test_unknown_target_is_rejected(self):
        try:
            flamegate_tls.resolve_target("http://127.0.0.1:9", "/secrets")
            assert False, "expected HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 400

    def test_absolute_url_path_is_rejected(self):
        try:
            flamegate_tls.resolve_target("core", "http://127.0.0.1:9/")
            assert False, "expected HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 400

    def test_allowlisted_target_resolves(self):
        url = flamegate_tls.resolve_target("core", "/health")
        assert url.endswith("/health")
        assert "://" in url


class TestHlmSignature:
    def test_missing_header_is_rejected(self):
        try:
            hlm_trinity_router.validate_flame_signature(None)
            assert False, "expected HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 403

    def test_configured_signature_is_accepted(self):
        assert hlm_trinity_router.validate_flame_signature("unit-test-signature") == "unit-test-signature"

    def test_public_yaml_default_is_not_accepted_in_production(self):
        try:
            hlm_trinity_router.validate_flame_signature("sovereign")
            assert False, "expected HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 403
