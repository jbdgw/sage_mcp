"""Tests for API key authentication middleware."""

from __future__ import annotations

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from sage_mcp.auth import ApiKeyAuthMiddleware


def _make_app(api_key: str | None) -> Starlette:
    """Build a minimal Starlette app with auth middleware for testing."""

    async def mcp_endpoint(request: Request) -> PlainTextResponse:
        return PlainTextResponse("ok")

    async def health_endpoint(request: Request) -> JSONResponse:
        return JSONResponse({"status": "healthy"})

    app = Starlette(
        routes=[
            Route("/mcp", mcp_endpoint, methods=["POST", "GET"]),
            Route("/health", health_endpoint, methods=["GET"]),
        ],
    )
    app.add_middleware(ApiKeyAuthMiddleware, api_key=api_key)
    return app


class TestAuthMiddlewareWithKeyConfigured:
    """When MCP_API_KEY is set, requests to /mcp must include a valid bearer token."""

    def test_request_without_auth_header_returns_401(self) -> None:
        client = TestClient(_make_app(api_key="test-secret-key"))
        response = client.post("/mcp")
        assert response.status_code == 401
        assert response.json()["error"] == "Missing or invalid Authorization header"

    def test_request_with_wrong_key_returns_401(self) -> None:
        client = TestClient(_make_app(api_key="test-secret-key"))
        response = client.post(
            "/mcp",
            headers={"Authorization": "Bearer wrong-key"},
        )
        assert response.status_code == 401

    def test_request_with_correct_key_passes_through(self) -> None:
        client = TestClient(_make_app(api_key="test-secret-key"))
        response = client.post(
            "/mcp",
            headers={"Authorization": "Bearer test-secret-key"},
        )
        assert response.status_code == 200
        assert response.text == "ok"

    def test_health_endpoint_bypasses_auth(self) -> None:
        client = TestClient(_make_app(api_key="test-secret-key"))
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_malformed_auth_header_returns_401(self) -> None:
        client = TestClient(_make_app(api_key="test-secret-key"))
        response = client.post(
            "/mcp",
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )
        assert response.status_code == 401


class TestAuthMiddlewareWithNoKeyConfigured:
    """When MCP_API_KEY is not set, all requests pass through (local dev mode)."""

    def test_no_auth_required_when_key_not_configured(self) -> None:
        client = TestClient(_make_app(api_key=None))
        response = client.post("/mcp")
        assert response.status_code == 200
        assert response.text == "ok"

    def test_health_still_works_when_key_not_configured(self) -> None:
        client = TestClient(_make_app(api_key=None))
        response = client.get("/health")
        assert response.status_code == 200
