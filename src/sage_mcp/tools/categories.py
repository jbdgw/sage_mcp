"""get_categories tool — Service 101."""

from __future__ import annotations

from typing import Annotated, Literal

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import Field

from sage_mcp.client.sage_client import SageClient
from sage_mcp.types.errors import SageAPIError
from sage_mcp.types.responses import CategoriesResponse


async def get_categories(
    list_type: Annotated[
        Literal["categories", "themes", "colors", "esg-flags"],
        Field(description="Type of list to retrieve"),
    ] = "categories",
    parent_id: Annotated[
        str | None,
        Field(description="Parent category ID for subcategories"),
    ] = None,
    *,
    ctx: Context,
) -> CategoriesResponse:
    """Browse SAGE product categories, themes, colors, or ESG flags.

    Use list_type to select which taxonomy. Pass parent_id to drill into subcategories.
    """
    client: SageClient = ctx.lifespan_context["sage_client"]
    try:
        return await client.get_categories(list_type=list_type, parent_id=parent_id)
    except SageAPIError as e:
        raise ToolError(str(e)) from e
