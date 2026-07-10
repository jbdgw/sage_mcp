"""get_categories tool — Service 101 (Research List)."""

from __future__ import annotations

from typing import Annotated

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import Field

from sage_mcp.client.sage_client import SageClient
from sage_mcp.types.errors import SageAPIError
from sage_mcp.types.requests import CategoryListTypeName
from sage_mcp.types.responses import CategoriesResponse


async def get_categories(
    list_type: Annotated[
        CategoryListTypeName,
        Field(description="List to retrieve: categories, themes, or esg (diversity flags)"),
    ] = "categories",
    *,
    ctx: Context,
) -> CategoriesResponse:
    """Browse SAGE research lists: product categories, themes, or ESG flags.

    Returns a flat list of {id, name}. Use the id (or name) as the
    categories/esg value in search_products.
    """
    client: SageClient = ctx.lifespan_context["sage_client"]
    try:
        return await client.get_categories(list_type=list_type)
    except SageAPIError as e:
        raise ToolError(str(e)) from e
