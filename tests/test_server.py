"""Tests for the production ASGI app exposed by server.py."""

from __future__ import annotations

import os
from unittest.mock import patch

from starlette.applications import Starlette
from starlette.testclient import TestClient


class TestAppExport:
    """The server module exposes a production-ready ASGI app."""

    def test_app_is_starlette_instance(self) -> None:
        from sage_mcp.server import app

        assert isinstance(app, Starlette)


class TestHealthEndpoint:
    """The /health endpoint works without auth for load balancer checks."""

    def test_health_returns_healthy_json(self) -> None:
        from sage_mcp.server import app

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestAuthOnMcpEndpoint:
    """The /mcp endpoint is protected when MCP_API_KEY is set."""

    def test_mcp_endpoint_requires_auth_when_key_set(self) -> None:
        """Reload module with MCP_API_KEY set to verify middleware is active."""
        import importlib

        import sage_mcp.server as server_module

        with patch.dict(os.environ, {"MCP_API_KEY": "prod-secret-key"}):
            importlib.reload(server_module)
            client = TestClient(server_module.app)
            response = client.post("/mcp")
            assert response.status_code == 401

        # Reload again to restore default state (no key)
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MCP_API_KEY", None)
            importlib.reload(server_module)
