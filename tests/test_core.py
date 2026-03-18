"""ARK95X Unified Sovereign Stack - Core Test Suite
Tests for health endpoints, models, config, and module loading.
"""
import pytest
import subprocess
import sys
import os

# ============================================================
# LEVEL 1: Smoke Tests - Does the code even load?
# ============================================================

class TestImports:
    """LEVEL 1: Verify all modules can be imported."""

    def test_main_imports(self):
        import main
        assert hasattr(main, 'app')

    def test_health_endpoint_exists(self):
        from main import app
        routes = [r.path for r in app.routes]
        assert '/health' in routes

    def test_query_endpoint_exists(self):
        from main import app
        routes = [r.path for r in app.routes]
        assert '/api/query' in routes

    def test_module_load_subprocess(self):
        result = subprocess.run(
            [sys.executable, '-c', 'import main; print("All modules loaded successfully")'],
            capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0
        assert "All modules loaded successfully" in result.stdout


# ============================================================
# LEVEL 2: Unit Tests - Models and Config
# ============================================================

class TestHealthModels:
    """LEVEL 2: Verify Pydantic models."""

    def test_health_response_model(self):
        from main import HealthResponse
        health = HealthResponse(
            status="healthy", uptime=1.0,
            timestamp="2026-01-01T00:00:00Z",
            services={"test": "healthy"}
        )
        assert health.status == "healthy"
        assert health.version == "1.0.0"

    def test_query_request_model(self):
        from main import QueryRequest
        req = QueryRequest(prompt="test")
        assert req.prompt == "test"
        assert req.model == "llama3"

    def test_query_response_model(self):
        from main import QueryResponse
        resp = QueryResponse(response="hello", model="llama3", elapsed=0.5)
        assert resp.response == "hello"


class TestConfig:
    """LEVEL 2: Verify configuration defaults."""

    def test_app_port_default(self):
        from main import APP_PORT
        assert APP_PORT == 8000

    def test_ollama_host_default(self):
        from main import OLLAMA_HOST
        assert "11434" in OLLAMA_HOST

    def test_redis_url_default(self):
        from main import REDIS_URL
        assert "6379" in REDIS_URL

    def test_qdrant_url_default(self):
        from main import QDRANT_URL
        assert "6333" in QDRANT_URL


# ============================================================
# LEVEL 3: Integration Tests - API Behavior
# ============================================================

class TestHealthAPI:
    """LEVEL 3: Test /health endpoint responses."""

    @pytest.fixture
    def client(self):
        from main import app
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_health_returns_200(self, client):
        response = client.get('/health')
        assert response.status_code == 200

    def test_health_json_structure(self, client):
        data = client.get('/health').json()
        assert 'status' in data
        assert 'uptime' in data
        assert 'services' in data
        assert 'version' in data

    def test_health_status_values(self, client):
        data = client.get('/health').json()
        assert data['status'] in ['healthy', 'degraded', 'unhealthy']


class TestQueryAPI:
    """LEVEL 3: Test /api/query endpoint."""

    @pytest.fixture
    def client(self):
        from main import app
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_query_rejects_empty_prompt(self, client):
        response = client.post('/api/query', json={'prompt': ''})
        assert response.status_code in [400, 422, 503]

    def test_query_accepts_valid_prompt(self, client):
        response = client.post('/api/query', json={'prompt': 'hello'})
        assert response.status_code in [200, 503]  # 503 if Ollama not running
