"""Bearer token authentication middleware for the MCP server."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

_PUBLIC_PATHS = frozenset({"/health"})


class ApiKeyAuthMiddleware(BaseHTTPMiddleware):
    """Check Authorization: Bearer <key> on protected endpoints.

    Skips auth on /health and when no api_key is configured (local dev).
    """

    def __init__(self, app: object, api_key: str | None = None) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._api_key = api_key

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if self._api_key is None or request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                {"error": "Missing or invalid Authorization header"},
                status_code=401,
            )

        token = auth_header.removeprefix("Bearer ")
        if token != self._api_key:
            return JSONResponse(
                {"error": "Missing or invalid Authorization header"},
                status_code=401,
            )

        return await call_next(request)
