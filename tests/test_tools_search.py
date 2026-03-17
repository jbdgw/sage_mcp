"""Tests for the search_products MCP tool."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from sage_mcp.client.sage_client import SageClient
from sage_mcp.types.errors import SageAPIError
from sage_mcp.types.responses import SearchResponse
from tests.conftest import SEARCH_RESPONSE_OK


@pytest.fixture
def mock_sage_client() -> AsyncMock:
    return AsyncMock(spec=SageClient)


@pytest.fixture
def mock_context(mock_sage_client: AsyncMock) -> AsyncMock:
    ctx = AsyncMock()
    ctx.lifespan_context = {"sage_client": mock_sage_client}
    return ctx


class TestSearchProductsTool:
    async def test_happy_path_returns_search_results(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.search import search_products

        mock_sage_client.search_products.return_value = SearchResponse.model_validate(
            SEARCH_RESPONSE_OK
        )
        result = await search_products(keywords="flashlight", ctx=mock_context)
        assert result.ok is True
        assert result.totalFound == 2
        assert len(result.products) == 2

    async def test_passes_all_search_params_to_client(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.search import search_products

        mock_sage_client.search_products.return_value = SearchResponse.model_validate(
            SEARCH_RESPONSE_OK
        )
        await search_products(
            keywords="pen",
            categories="Writing",
            price_low=1.0,
            price_high=5.0,
            colors="Blue",
            themes="Corporate",
            env_friendly=True,
            qty=100,
            limit=50,
            ctx=mock_context,
        )
        call_args = mock_sage_client.search_products.call_args
        search_rec = call_args[0][0]
        assert search_rec.keywords == "pen"
        assert search_rec.categories == "Writing"
        assert search_rec.priceLow == 1.0
        assert search_rec.priceHigh == 5.0
        assert search_rec.colors == "Blue"
        assert search_rec.envFriendly is True
        assert search_rec.limit == 50

    async def test_default_extra_return_fields(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.search import search_products

        mock_sage_client.search_products.return_value = SearchResponse.model_validate(
            SEARCH_RESPONSE_OK
        )
        await search_products(keywords="flashlight", ctx=mock_context)
        call_args = mock_sage_client.search_products.call_args
        search_rec = call_args[0][0]
        assert search_rec.extraReturnFields is not None
        assert "CATEGORY" in search_rec.extraReturnFields

    async def test_sage_api_error_raises_tool_error(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from fastmcp.exceptions import ToolError

        from sage_mcp.tools.search import search_products

        mock_sage_client.search_products.side_effect = SageAPIError(
            10301, "Not enough search criteria"
        )
        with pytest.raises(ToolError):
            await search_products(ctx=mock_context)
