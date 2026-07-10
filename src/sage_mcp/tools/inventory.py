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
        list[int] | None,
        Field(description="Product entity IDs (prodEId) to check — batches in one call"),
    ] = None,
    supplier_sage_num: Annotated[
        int | None,
        Field(description="Alternative lookup: supplier's 5-digit SAGE # (with item_num)"),
    ] = None,
    item_num: Annotated[
        str | None,
        Field(description="Alternative lookup: supplier's item number (with supplier_sage_num)"),
    ] = None,
    *,
    ctx: Context,
) -> InventoryResponse:
    """Check real-time inventory levels for one or more promotional products.

    Look up by product_ids (batchable), or by supplier_sage_num + item_num.
    Returns per-product totals and per-variant (color/size) stock levels.
    Note: get_product_detail already includes this data — use this tool for
    quick re-checks or batching several products in one call.
    """
    client: SageClient = ctx.lifespan_context["sage_client"]
    refs = [InventoryProductRef(productId=pid) for pid in product_ids or []]
    if supplier_sage_num is not None or item_num is not None:
        refs.append(InventoryProductRef(sageNum=supplier_sage_num, itemNum=item_num))
    if not refs:
        raise ToolError("Provide product_ids or supplier_sage_num + item_num.")
    try:
        return await client.check_inventory(products=refs)
    except SageAPIError as e:
        raise ToolError(str(e)) from e
