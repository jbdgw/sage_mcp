"""check_inventory tool — Service 107."""

from __future__ import annotations

from typing import Annotated

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import Field

from sage_mcp.client.sage_client import SageClient
from sage_mcp.types.errors import SageAPIError
from sage_mcp.types.requests import InventoryProductRef
from sage_mcp.types.responses import InventoryResponse


async def check_inventory(
    product_ids: Annotated[
        list[int],
        Field(description="Product entity IDs (prodEId) to check — batches in one call", min_length=1),
    ],
    *,
    ctx: Context,
) -> InventoryResponse:
    """Check real-time inventory levels for one or more promotional products.

    Returns per-product totals and per-variant (color/size) stock levels.
    Note: get_product_detail already includes this data — use this tool for
    quick re-checks or batching several products in one call.
    """
    client: SageClient = ctx.lifespan_context["sage_client"]
    refs = [InventoryProductRef(productId=pid) for pid in product_ids]
    try:
        return await client.check_inventory(products=refs)
    except SageAPIError as e:
        raise ToolError(str(e)) from e
