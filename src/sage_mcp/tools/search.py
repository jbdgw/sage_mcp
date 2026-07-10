"""search_products tool — Service 103."""

from __future__ import annotations

from typing import Annotated

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import Field

from sage_mcp.client.sage_client import SageClient
from sage_mcp.types.errors import SageAPIError
from sage_mcp.types.requests import SearchRec, SearchSort
from sage_mcp.types.responses import SearchResponse

# Small extras on by default; DESCRIPTION/COLORS/THEMES are opt-in because
# they roughly triple per-product payload size.
_LEAN_EXTRA_FIELDS = "ITEMNUM,CATEGORY,SUPPLIER,SUPPID,LINE,PRODTIME"
_VERBOSE_EXTRA_FIELDS = _LEAN_EXTRA_FIELDS + ",DESCRIPTION,COLORS,THEMES"

_MAX_LIMIT = 250
_DEFAULT_LIMIT = 25


async def search_products(
    keywords: Annotated[str | None, Field(description="Free-text keyword search")] = None,
    quick_search: Annotated[
        str | None,
        Field(description="Smart search — SAGE auto-detects category vs keyword vs SPC"),
    ] = None,
    categories: Annotated[str | None, Field(description="Category name or number")] = None,
    spc: Annotated[str | None, Field(description="SAGE product code")] = None,
    item_num: Annotated[str | None, Field(description="Supplier's item number")] = None,
    price_low: Annotated[float | None, Field(description="Minimum price filter")] = None,
    price_high: Annotated[float | None, Field(description="Maximum price filter")] = None,
    qty: Annotated[int | None, Field(description="Quantity for pricing")] = None,
    colors: Annotated[str | None, Field(description="Color filter")] = None,
    themes: Annotated[str | None, Field(description="Theme filter")] = None,
    made_in: Annotated[str | None, Field(description="Two-digit country code")] = None,
    env_friendly: Annotated[bool | None, Field(description="Eco-friendly only")] = None,
    verified: Annotated[bool | None, Field(description="SAGE-verified only")] = None,
    esg: Annotated[
        str | None,
        Field(description="Comma-separated ESG flag IDs (from get_categories esg list)"),
    ] = None,
    production_days: Annotated[
        int | None, Field(description="Production time in working days")
    ] = None,
    supplier_id: Annotated[
        int | None, Field(description="Restrict to one supplier's SAGE #")
    ] = None,
    line_name: Annotated[str | None, Field(description="Supplier line name filter")] = None,
    sort: Annotated[
        SearchSort | None,
        Field(description="Sort order: BESTMATCH (default), PRICE, PRICEHIGHLOW, POPULARITY, PREFGROUP"),
    ] = None,
    limit: Annotated[
        int | None, Field(description="Results per page (1-250, default 25)", ge=1, le=_MAX_LIMIT)
    ] = None,
    page: Annotated[int | None, Field(description="Page number (1-based)", ge=1)] = None,
    page_size: Annotated[
        int | None,
        Field(description="Deprecated alias for limit", ge=1, le=_MAX_LIMIT),
    ] = None,
    page_number: Annotated[
        int | None, Field(description="Deprecated alias for page", ge=1)
    ] = None,
    include_descriptions: Annotated[
        bool,
        Field(description="Include DESCRIPTION/COLORS/THEMES per product (~3x payload)"),
    ] = False,
    *,
    ctx: Context,
) -> SearchResponse:
    """Search the SAGE promotional products catalog.

    Provide at least one criterion (keywords, quick_search, categories, or spc).
    Returns one page of results (default 25); totalFound reports the full match
    count so you can paginate with the page parameter.
    """
    client: SageClient = ctx.lifespan_context["sage_client"]
    effective_limit = limit or page_size or _DEFAULT_LIMIT
    effective_page = page or page_number or 1

    search = SearchRec(
        keywords=keywords,
        quickSearch=quick_search,
        categories=categories,
        spc=spc,
        itemNum=item_num,
        priceLow=price_low,
        priceHigh=price_high,
        qty=qty,
        colors=colors,
        themes=themes,
        madeIn=made_in,
        envFriendly=env_friendly,
        verified=verified,
        esg=esg,
        prodTime=production_days,
        suppId=supplier_id,
        lineName=line_name,
        sort=sort,
        maxRecs=effective_limit,
        startNum=(effective_page - 1) * effective_limit + 1,
        extraReturnFields=_VERBOSE_EXTRA_FIELDS if include_descriptions else _LEAN_EXTRA_FIELDS,
    )
    try:
        return await client.search_products(search)
    except SageAPIError as e:
        raise ToolError(str(e)) from e
