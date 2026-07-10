"""Tests for the check_inventory MCP tool."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from sage_mcp.client.sage_client import SageClient
from sage_mcp.types.errors import SageAPIError
from sage_mcp.types.responses import InventoryResponse
from tests.conftest import INVENTORY_RESPONSE_OK


@pytest.fixture
def mock_sage_client() -> AsyncMock:
    return AsyncMock(spec=SageClient)


@pytest.fixture
def mock_context(mock_sage_client: AsyncMock) -> AsyncMock:
    ctx = AsyncMock()
    ctx.lifespan_context = {"sage_client": mock_sage_client}
    return ctx


class TestCheckInventoryTool:
    async def test_happy_path_returns_inventory(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.inventory import check_inventory

        mock_sage_client.check_inventory.return_value = InventoryResponse.model_validate(
            INVENTORY_RESPONSE_OK
        )
        result = await check_inventory(product_ids=[105917761], ctx=mock_context)
        assert len(result.products) == 1
        assert result.products[0].onHand == 56341
        assert result.products[0].skus[0].onHand == 5991

    async def test_batches_multiple_product_ids_in_one_call(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.inventory import check_inventory

        mock_sage_client.check_inventory.return_value = InventoryResponse.model_validate(
            INVENTORY_RESPONSE_OK
        )
        await check_inventory(product_ids=[105917761, 771822521], ctx=mock_context)
        refs = mock_sage_client.check_inventory.call_args.kwargs["products"]
        assert [r.productId for r in refs] == [105917761, 771822521]

    async def test_supplier_item_num_lookup_without_product_ids(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        """Service 107 alternative lookup: supplier SAGE # + item number."""
        from sage_mcp.tools.inventory import check_inventory

        mock_sage_client.check_inventory.return_value = InventoryResponse.model_validate(
            INVENTORY_RESPONSE_OK
        )
        await check_inventory(
            supplier_sage_num=60462, item_num="DBT-AT19", ctx=mock_context
        )
        refs = mock_sage_client.check_inventory.call_args.kwargs["products"]
        assert len(refs) == 1
        assert refs[0].productId is None
        assert refs[0].sageNum == 60462
        assert refs[0].itemNum == "DBT-AT19"

    async def test_no_identifiers_raises_tool_error_without_api_call(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from fastmcp.exceptions import ToolError

        from sage_mcp.tools.inventory import check_inventory

        with pytest.raises(ToolError, match="product_ids or supplier_sage_num"):
            await check_inventory(ctx=mock_context)
        mock_sage_client.check_inventory.assert_not_called()

    async def test_api_error_raises_tool_error(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from fastmcp.exceptions import ToolError

        from sage_mcp.tools.inventory import check_inventory

        mock_sage_client.check_inventory.side_effect = SageAPIError(
            10701, "Include at least one product in the request."
        )
        with pytest.raises(ToolError):
            await check_inventory(product_ids=[0], ctx=mock_context)
