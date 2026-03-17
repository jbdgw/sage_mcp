"""get_product_images tool — derived from Service 105."""

from __future__ import annotations

from typing import Annotated

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import Field

from sage_mcp.client.sage_client import SageClient
from sage_mcp.types.errors import SageAPIError
from sage_mcp.types.responses import ProductImage


async def get_product_images(
    prod_eid: Annotated[str, Field(description="Product entity ID or SAGE product code (SPC)")],
    *,
    ctx: Context,
) -> list[ProductImage]:
    """Get all images for a promotional product.

    Fetches the product detail and extracts the image list.
    Each image includes a URL, hasLogo flag (1=with logo, 0=blank), and caption.
    """
    client: SageClient = ctx.lifespan_context["sage_client"]
    try:
        resp = await client.get_product_detail(prod_eid=prod_eid, include_supplier_info=False)
        return resp.product.pics
    except SageAPIError as e:
        raise ToolError(str(e)) from e
