"""search_products tool — Service 103."""

from __future__ import annotations

from typing import Annotated

from fastmcp.exceptions import ToolError
from pydantic import Field

from sage_mcp.client.sage_client import SageClient
from sage_mcp.types.errors import SageAPIError
from sage_mcp.types.requests import SearchRec
from sage_mcp.types.responses import SearchResponse

_DEFAULT_EXTRA_FIELDS = "ITEMNUM,CATEGORY,DESCRIPTION,COLORS,THEMES,SUPPLIER,LINE,PRODTIME"


async def search_products(
    keywords: Annotated[str | None, Field(description="Free-text keyword search")] = None,
    categories: Annotated[str | None, Field(description="Category name or number")] = None,
    spc: Annotated[str | None, Field(description="SAGE product code")] = None,
    price_low: Annotated[float | None, Field(description="Minimum price filter")] = None,
    price_high: Annotated[float | None, Field(description="Maximum price filter")] = None,
    qty: Annotated[int | None, Field(description="Quantity for pricing")] = None,
    colors: Annotated[str | None, Field(description="Color filter")] = None,
    themes: Annotated[str | None, Field(description="Theme filter")] = None,
    made_in: Annotated[str | None, Field(description="Two-digit country code")] = None,
    env_friendly: Annotated[bool | None, Field(description="Eco-friendly only")] = None,
    verified: Annotated[bool | None, Field(description="SAGE-verified only")] = None,
    prod_time: Annotated[str | None, Field(description="Production time filter")] = None,
    production_days: Annotated[int | None, Field(description="Max production days")] = None,
    order_by: Annotated[str | None, Field(description="Sort order")] = None,
    page_size: Annotated[int | None, Field(description="Results per page")] = None,
    page_number: Annotated[int | None, Field(description="Page number (1-based)")] = None,
    limit: Annotated[int | None, Field(description="Max results to return")] = None,
    *,
    ctx: object,
) -> SearchResponse:
    """Search the SAGE promotional products catalog.

    Provide at least one search criterion (keywords, categories, or spc).
    Returns matching products with pricing, thumbnails, and metadata.
    """
    client: SageClient = ctx.lifespan_context["sage_client"]  # type: ignore[union-attr]

    search = SearchRec(
        keywords=keywords,
        categories=categories,
        spc=spc,
        priceLow=price_low,
        priceHigh=price_high,
        qty=qty,
        colors=colors,
        themes=themes,
        madeIn=made_in,
        envFriendly=env_friendly,
        verified=verified,
        prodTime=prod_time,
        productionDays=production_days,
        orderBy=order_by,
        pageSize=page_size,
        pageNumber=page_number,
        limit=limit,
        extraReturnFields=_DEFAULT_EXTRA_FIELDS,
    )
    try:
        return await client.search_products(search)
    except SageAPIError as e:
        raise ToolError(str(e)) from e
