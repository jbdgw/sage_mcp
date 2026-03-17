"""Tests for the get_categories MCP tool."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from sage_mcp.client.sage_client import SageClient
from sage_mcp.types.errors import SageAPIError
from sage_mcp.types.responses import CategoriesResponse
from tests.conftest import CATEGORIES_RESPONSE_OK


@pytest.fixture
def mock_sage_client() -> AsyncMock:
    return AsyncMock(spec=SageClient)


@pytest.fixture
def mock_context(mock_sage_client: AsyncMock) -> AsyncMock:
    ctx = AsyncMock()
    ctx.lifespan_context = {"sage_client": mock_sage_client}
    return ctx


class TestGetCategoriesTool:
    async def test_happy_path_returns_categories(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.categories import get_categories

        mock_sage_client.get_categories.return_value = CategoriesResponse.model_validate(
            CATEGORIES_RESPONSE_OK
        )
        result = await get_categories(list_type="categories", ctx=mock_context)
        assert len(result.items) == 2
        assert result.items[0].name == "Flashlights"

    async def test_passes_parent_id_to_client(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.categories import get_categories

        mock_sage_client.get_categories.return_value = CategoriesResponse.model_validate(
            CATEGORIES_RESPONSE_OK
        )
        await get_categories(list_type="themes", parent_id="42", ctx=mock_context)
        call_args = mock_sage_client.get_categories.call_args
        assert call_args.kwargs["list_type"] == "themes"
        assert call_args.kwargs["parent_id"] == "42"

    async def test_parent_id_defaults_to_none(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.categories import get_categories

        mock_sage_client.get_categories.return_value = CategoriesResponse.model_validate(
            CATEGORIES_RESPONSE_OK
        )
        await get_categories(list_type="categories", ctx=mock_context)
        call_args = mock_sage_client.get_categories.call_args
        assert call_args.kwargs["parent_id"] is None

    async def test_api_error_raises_tool_error(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from fastmcp.exceptions import ToolError

        from sage_mcp.tools.categories import get_categories

        mock_sage_client.get_categories.side_effect = SageAPIError(
            10001, "General system error"
        )
        with pytest.raises(ToolError):
            await get_categories(list_type="categories", ctx=mock_context)
