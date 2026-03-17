"""get_product_detail tool — Service 105."""

from __future__ import annotations

from typing import Annotated

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import Field

from sage_mcp.client.sage_client import SageClient
from sage_mcp.types.errors import SageAPIError
from sage_mcp.types.responses import ProductDetailResponse


async def get_product_detail(
    prod_eid: Annotated[str, Field(description="Product entity ID or SAGE product code (SPC)")],
    include_supplier_info: Annotated[
        bool, Field(description="Include supplier contact information")
    ] = True,
    *,
    ctx: Context,
) -> ProductDetailResponse:
    """Get full details for a specific promotional product.

    Pass either a numeric product entity ID or a SAGE product code (SPC).
    Returns pricing tiers, description, supplier info, and images.
    """
    client: SageClient = ctx.lifespan_context["sage_client"]
    try:
        return await client.get_product_detail(
            prod_eid=prod_eid,
            include_supplier_info=include_supplier_info,
        )
    except SageAPIError as e:
        raise ToolError(str(e)) from e
