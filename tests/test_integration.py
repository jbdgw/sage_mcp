"""Integration tests — live Sage API tests (skipped without credentials)."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def has_sage_credentials() -> bool:
    return all(os.environ.get(k) for k in ("SAGE_ACCT_ID", "SAGE_AUTH_KEY"))


@pytest.mark.skipif(
    not all(os.environ.get(k) for k in ("SAGE_ACCT_ID", "SAGE_AUTH_KEY")),
    reason="SAGE_ACCT_ID and SAGE_AUTH_KEY not set",
)
class TestLiveSageAPI:
    async def test_search_flashlights(self) -> None:
        from fastmcp import Client

        from sage_mcp.server import mcp

        async with Client(mcp) as client:
            result = await client.call_tool(
                "search_products", {"keywords": "flashlight", "limit": 5}
            )
            assert result is not None

    async def test_get_categories(self) -> None:
        from fastmcp import Client

        from sage_mcp.server import mcp

        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_categories", {"list_type": "categories"}
            )
            assert result is not None
