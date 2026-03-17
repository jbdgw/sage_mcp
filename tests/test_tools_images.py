"""Tests for the get_product_images MCP tool."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from sage_mcp.client.sage_client import SageClient
from sage_mcp.types.errors import SageAPIError
from sage_mcp.types.responses import ProductDetailResponse
from tests.conftest import DETAIL_RESPONSE_OK


@pytest.fixture
def mock_sage_client() -> AsyncMock:
    return AsyncMock(spec=SageClient)


@pytest.fixture
def mock_context(mock_sage_client: AsyncMock) -> AsyncMock:
    ctx = AsyncMock()
    ctx.lifespan_context = {"sage_client": mock_sage_client}
    return ctx


class TestGetProductImagesTool:
    async def test_happy_path_returns_images(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.images import get_product_images

        mock_sage_client.get_product_detail.return_value = (
            ProductDetailResponse.model_validate(DETAIL_RESPONSE_OK)
        )
        result = await get_product_images(prod_eid="345733702", ctx=mock_context)
        assert len(result) == 2
        assert result[0].url == "https://example.com/pic1.jpg"
        assert result[0].hasLogo == 1

    async def test_empty_pics_returns_empty_list(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.images import get_product_images

        no_pics = {
            "product": {
                "prodEId": 1,
                "pics": [],
            }
        }
        mock_sage_client.get_product_detail.return_value = (
            ProductDetailResponse.model_validate(no_pics)
        )
        result = await get_product_images(prod_eid="1", ctx=mock_context)
        assert result == []

    async def test_product_not_found_raises_tool_error(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from fastmcp.exceptions import ToolError

        from sage_mcp.tools.images import get_product_images

        mock_sage_client.get_product_detail.side_effect = SageAPIError(
            10501, "Product not found"
        )
        with pytest.raises(ToolError):
            await get_product_images(prod_eid="999999999", ctx=mock_context)
