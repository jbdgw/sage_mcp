"""Tests for the check_inventory MCP tool."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from sage_mcp.client.sage_client import SageClient
from sage_mcp.types.errors import SageAPIError
from sage_mcp.types.responses import InventoryResponse, ProductDetailResponse
from tests.conftest import DETAIL_RESPONSE_OK, INVENTORY_RESPONSE_OK


@pytest.fixture
def mock_sage_client() -> AsyncMock:
    return AsyncMock(spec=SageClient)


@pytest.fixture
def mock_context(mock_sage_client: AsyncMock) -> AsyncMock:
    ctx = AsyncMock()
    ctx.lifespan_context = {"sage_client": mock_sage_client}
    return ctx


# Service 107 answers with its internal id (prodEId minus 2-digit prefix)
INVENTORY_107_OK = {
    "ok": True,
    "products": [
        {
            "productId": 5917761,
            "sageNum": 60462,
            "itemNum": "DBT-AT19",
            "ok": True,
            "onHand": 56341,
            "skus": [
                {"attributes": [{"typeId": 10, "value": "Black"}], "onHand": 5991, "onOrder": 0}
            ],
            "lastUpdated": "2026-07-10T00:00:29Z",
        }
    ],
}

INVENTORY_107_NOT_FOUND = {
    "ok": False,
    "products": [
        {"productId": 5917761, "sageNum": 0, "itemNum": "", "ok": False, "onHand": 0, "skus": []}
    ],
}


class TestCheckInventoryTool:
    async def test_prod_eid_translated_to_service_107_id(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        """Live 2026-07-09: 107 productId is the 9-digit prodEId minus its
        2-digit prefix (105917761 -> 5917761); raw prodEIds return ok=false."""
        from sage_mcp.tools.inventory import check_inventory

        mock_sage_client.check_inventory.return_value = InventoryResponse.model_validate(
            INVENTORY_107_OK
        )
        result = await check_inventory(product_ids=[105917761], ctx=mock_context)
        refs = mock_sage_client.check_inventory.call_args.kwargs["products"]
        assert refs[0].productId == 5917761
        assert result.products[0].onHand == 56341
        assert result.products[0].prodEId == 105917761  # caller's id restored

    async def test_batches_multiple_product_ids_in_one_call(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.inventory import check_inventory

        mock_sage_client.check_inventory.return_value = InventoryResponse.model_validate(
            INVENTORY_RESPONSE_OK
        )
        await check_inventory(product_ids=[105917761, 595465361], ctx=mock_context)
        refs = mock_sage_client.check_inventory.call_args_list[0].kwargs["products"]
        assert [r.productId for r in refs] == [5917761, 5465361]

    async def test_not_found_falls_back_to_supplier_item_num(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        """When the derived id misses, resolve suppId+itemNum via detail and
        retry — so product_ids just work for agents."""
        from sage_mcp.tools.inventory import check_inventory

        mock_sage_client.check_inventory.side_effect = [
            InventoryResponse.model_validate(INVENTORY_107_NOT_FOUND),
            InventoryResponse.model_validate(INVENTORY_107_OK),
        ]
        mock_sage_client.get_product_detail.return_value = (
            ProductDetailResponse.model_validate(DETAIL_RESPONSE_OK)
        )
        result = await check_inventory(product_ids=[105917761], ctx=mock_context)

        retry_refs = mock_sage_client.check_inventory.call_args_list[1].kwargs["products"]
        assert retry_refs[0].sageNum == 60462
        assert retry_refs[0].itemNum == "DBT-AT19"
        assert result.products[0].ok is True
        assert result.products[0].onHand == 56341
        assert result.products[0].prodEId == 105917761

    async def test_supplier_item_num_lookup_without_product_ids(
        self, mock_sage_client: AsyncMock, mock_context: AsyncMock
    ) -> None:
        from sage_mcp.tools.inventory import check_inventory

        mock_sage_client.check_inventory.return_value = InventoryResponse.model_validate(
            INVENTORY_107_OK
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
            await check_inventory(product_ids=[105917761], ctx=mock_context)
