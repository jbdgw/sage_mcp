"""Tests for the search_products MCP tool."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from sage_mcp.client.sage_client import SageClient
from sage_mcp.types.errors import SageAPIError
from sage_mcp.types.requests import SearchRec
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


def sent_search_rec(mock_sage_client: AsyncMock) -> SearchRec:
    return mock_sage_client.search_products.call_args[0][0]


class TestSearchProductsTool:
    async def test_happy_path_returns_search_results(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.search import search_products

        mock_sage_client.search_products.return_value = SearchResponse.model_validate(
            SEARCH_RESPONSE_OK
        )
        result = await search_products(keywords="water bottle", ctx=mock_context)
        assert result.ok is True
        assert result.totalFound == 2
        assert len(result.products) == 2

    async def test_default_page_size_caps_payload_at_25(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        """Without maxRecs, SAGE returns up to 1000 products (~1MB). The
        tool must always send a page cap."""
        from sage_mcp.tools.search import search_products

        mock_sage_client.search_products.return_value = SearchResponse.model_validate(
            SEARCH_RESPONSE_OK
        )
        await search_products(keywords="water bottle", ctx=mock_context)
        rec = sent_search_rec(mock_sage_client)
        assert rec.maxRecs == 25
        assert rec.startNum == 1

    async def test_limit_and_page_map_to_max_recs_and_start_num(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.search import search_products

        mock_sage_client.search_products.return_value = SearchResponse.model_validate(
            SEARCH_RESPONSE_OK
        )
        await search_products(keywords="pen", limit=50, page=3, ctx=mock_context)
        rec = sent_search_rec(mock_sage_client)
        assert rec.maxRecs == 50
        assert rec.startNum == 101  # (3-1)*50 + 1

    async def test_deprecated_page_size_alias_still_works(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        """Consuming apps (grid search) send page_size: 250 — must not be
        rejected or silently dropped to the 25-result default."""
        from sage_mcp.tools.search import search_products

        mock_sage_client.search_products.return_value = SearchResponse.model_validate(
            SEARCH_RESPONSE_OK
        )
        await search_products(
            keywords="tumbler", page_size=250, page_number=2, ctx=mock_context
        )
        rec = sent_search_rec(mock_sage_client)
        assert rec.maxRecs == 250
        assert rec.startNum == 251

    async def test_explicit_limit_wins_over_page_size(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.search import search_products

        mock_sage_client.search_products.return_value = SearchResponse.model_validate(
            SEARCH_RESPONSE_OK
        )
        await search_products(keywords="pen", limit=100, page_size=250, ctx=mock_context)
        assert sent_search_rec(mock_sage_client).maxRecs == 100

    async def test_passes_filter_params_to_client(
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
            supplier_id=60462,
            sort="PRICE",
            ctx=mock_context,
        )
        rec = sent_search_rec(mock_sage_client)
        assert rec.keywords == "pen"
        assert rec.categories == "Writing"
        assert rec.priceLow == 1.0
        assert rec.priceHigh == 5.0
        assert rec.colors == "Blue"
        assert rec.envFriendly is True
        assert rec.suppId == 60462
        assert rec.sort == "PRICE"

    async def test_quick_search_maps_to_camelcase(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.search import search_products

        mock_sage_client.search_products.return_value = SearchResponse.model_validate(
            SEARCH_RESPONSE_OK
        )
        await search_products(quick_search="flashlights", ctx=mock_context)
        assert sent_search_rec(mock_sage_client).quickSearch == "flashlights"

    async def test_default_extras_are_lean_without_descriptions(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        """DESCRIPTION/COLORS/THEMES ~triple per-product size; they must be
        opt-in, while the small identifying extras stay on by default."""
        from sage_mcp.tools.search import search_products

        mock_sage_client.search_products.return_value = SearchResponse.model_validate(
            SEARCH_RESPONSE_OK
        )
        await search_products(keywords="flashlight", ctx=mock_context)
        extras = sent_search_rec(mock_sage_client).extraReturnFields
        assert extras is not None
        assert "SUPPID" in extras
        assert "CATEGORY" in extras
        assert "ITEMNUM" in extras
        assert "DESCRIPTION" not in extras

    async def test_include_descriptions_adds_verbose_extras(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.search import search_products

        mock_sage_client.search_products.return_value = SearchResponse.model_validate(
            SEARCH_RESPONSE_OK
        )
        await search_products(keywords="flashlight", include_descriptions=True, ctx=mock_context)
        extras = sent_search_rec(mock_sage_client).extraReturnFields
        assert extras is not None
        assert "DESCRIPTION" in extras
        assert "COLORS" in extras
        assert "THEMES" in extras

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
