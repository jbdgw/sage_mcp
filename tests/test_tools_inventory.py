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
        result = await check_inventory(product_id="345733702", ctx=mock_context)
        assert len(result.inventory) == 1
        assert result.inventory[0].availableQuantity == 1200

    async def test_passes_product_id_to_client(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.inventory import check_inventory

        mock_sage_client.check_inventory.return_value = InventoryResponse.model_validate(
            INVENTORY_RESPONSE_OK
        )
        await check_inventory(product_id="771822521", ctx=mock_context)
        call_args = mock_sage_client.check_inventory.call_args
        assert call_args.kwargs["product_id"] == "771822521"

    async def test_api_error_raises_tool_error(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from fastmcp.exceptions import ToolError

        from sage_mcp.tools.inventory import check_inventory

        mock_sage_client.check_inventory.side_effect = SageAPIError(
            10501, "Product not found"
        )
        with pytest.raises(ToolError):
            await check_inventory(product_id="000", ctx=mock_context)
