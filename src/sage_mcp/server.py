"""FastMCP server instance, lifespan, tool registration, and entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import httpx
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from sage_mcp.auth import ApiKeyAuthMiddleware
from sage_mcp.client.sage_client import SageClient
from sage_mcp.settings import SageSettings, ServerSettings
from sage_mcp.tools.categories import get_categories
from sage_mcp.tools.detail import get_product_detail
from sage_mcp.tools.images import get_product_images
from sage_mcp.tools.inventory import check_inventory
from sage_mcp.tools.search import search_products


@asynccontextmanager
async def sage_lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """Create shared httpx.AsyncClient and SageClient for the server lifetime."""
    settings = SageSettings()  # type: ignore[call-arg]
    async with httpx.AsyncClient(
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=settings.request_timeout_seconds,
    ) as http:
        sage_client = SageClient(http_client=http, settings=settings)
        yield {"sage_client": sage_client, "settings": settings}


_INSTRUCTIONS = """\
SAGE Connect promotional products API server.

Available tools:
- search_products: Search the SAGE catalog by keywords, categories, price, color, etc.
- get_product_detail: Get full details for a product by entity ID or SPC code.
- check_inventory: Check real-time inventory and stock levels.
- get_categories: Browse product categories, themes, colors, and ESG flags.
- get_product_images: Get all images for a product.

Typical workflow: search → detail → inventory check.
"""

mcp = FastMCP(
    "SageConnect",
    instructions=_INSTRUCTIONS,
    lifespan=sage_lifespan,
)

# Register tools
mcp.tool(search_products)
mcp.tool(get_product_detail)
mcp.tool(check_inventory)
mcp.tool(get_categories)
mcp.tool(get_product_images)


# Health check endpoint
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy"})


def _build_app() -> Any:
    """Build the production ASGI app with auth middleware."""
    server_settings = ServerSettings()  # type: ignore[call-arg]
    asgi_app = mcp.http_app(transport="streamable-http")
    api_key = server_settings.api_key
    asgi_app.add_middleware(
        ApiKeyAuthMiddleware,
        api_key=api_key.get_secret_value() if api_key else None,
    )
    return asgi_app


# Module-level ASGI app for uvicorn: `uvicorn sage_mcp.server:app`
app = _build_app()


def main() -> None:
    """CLI entry point — runs the MCP server."""
    server_settings = ServerSettings()  # type: ignore[call-arg]
    transport = server_settings.transport

    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(
            transport="streamable-http",
            host=server_settings.host,
            port=server_settings.port,
        )


if __name__ == "__main__":
    main()
