"""check_inventory tool — Service 107."""

from __future__ import annotations

from typing import Annotated

from fastmcp.exceptions import ToolError
from pydantic import Field

from sage_mcp.client.sage_client import SageClient
from sage_mcp.types.errors import SageAPIError
from sage_mcp.types.responses import InventoryResponse


async def check_inventory(
    product_id: Annotated[str, Field(description="Product entity ID to check inventory for")],
    *,
    ctx: object,
) -> InventoryResponse:
    """Check real-time inventory levels for a promotional product.

    Returns warehouse stock levels, available quantities, and lead times.
    """
    client: SageClient = ctx.lifespan_context["sage_client"]  # type: ignore[union-attr]
    try:
        return await client.check_inventory(product_id=product_id)
    except SageAPIError as e:
        raise ToolError(str(e)) from e
