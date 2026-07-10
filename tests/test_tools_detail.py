"""Tests for the get_product_detail MCP tool."""

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


class TestGetProductDetailTool:
    async def test_happy_path_returns_product(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.detail import get_product_detail

        mock_sage_client.get_product_detail.return_value = (
            ProductDetailResponse.model_validate(DETAIL_RESPONSE_OK)
        )
        result = await get_product_detail(prod_eid="105917761", ctx=mock_context)
        assert result.product.prodEId == 105917761
        assert result.product.prName == "Atrium 25 oz Aluminum Bottle"

    async def test_detail_exposes_embedded_inventory(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        """Detail already carries live stock — apps should read it here
        instead of making a follow-up check_inventory call."""
        from sage_mcp.tools.detail import get_product_detail

        mock_sage_client.get_product_detail.return_value = (
            ProductDetailResponse.model_validate(DETAIL_RESPONSE_OK)
        )
        result = await get_product_detail(prod_eid="105917761", ctx=mock_context)
        assert result.product.onHand == 56341
        assert result.product.skus[0].attributes[0].value == "Black"

    async def test_accepts_spc_as_prod_eid(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.detail import get_product_detail

        mock_sage_client.get_product_detail.return_value = (
            ProductDetailResponse.model_validate(DETAIL_RESPONSE_OK)
        )
        await get_product_detail(prod_eid="NBJXC-SZZDO", ctx=mock_context)
        call_args = mock_sage_client.get_product_detail.call_args
        assert call_args.kwargs["prod_eid"] == "NBJXC-SZZDO"

    async def test_include_supplier_info_passed_through(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.detail import get_product_detail

        mock_sage_client.get_product_detail.return_value = (
            ProductDetailResponse.model_validate(DETAIL_RESPONSE_OK)
        )
        await get_product_detail(
            prod_eid="105917761", include_supplier_info=False, ctx=mock_context
        )
        call_args = mock_sage_client.get_product_detail.call_args
        assert call_args.kwargs["include_supplier_info"] is False

    async def test_include_images_false_strips_pics(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.detail import get_product_detail

        mock_sage_client.get_product_detail.return_value = (
            ProductDetailResponse.model_validate(DETAIL_RESPONSE_OK)
        )
        result = await get_product_detail(
            prod_eid="105917761", include_images=False, ctx=mock_context
        )
        assert result.product.pics == []

    async def test_product_not_found_raises_tool_error(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from fastmcp.exceptions import ToolError

        from sage_mcp.tools.detail import get_product_detail

        mock_sage_client.get_product_detail.side_effect = SageAPIError(
            10501, "Product not found"
        )
        with pytest.raises(ToolError):
            await get_product_detail(prod_eid="999999999", ctx=mock_context)
