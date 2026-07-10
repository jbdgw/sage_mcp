"""check_inventory tool — Service 107."""

from __future__ import annotations

from typing import Annotated

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import Field

from sage_mcp.client.sage_client import SageClient
from sage_mcp.types.errors import SageAPIError
from sage_mcp.types.requests import InventoryProductRef
from sage_mcp.types.responses import InventoryProduct, InventoryResponse


def _service_product_id(prod_eid: int) -> int:
    """Service 107 productIds are 9-digit prodEIds minus their 2-digit prefix.

    Observed live 2026-07-09: prodEId 105917761 -> productId 5917761,
    595465361 -> 5465361. Raw prodEIds always return ok=false.
    """
    s = str(prod_eid)
    return int(s[2:]) if len(s) == 9 else prod_eid


async def _lookup_by_item_num(client: SageClient, prod_eid: int) -> InventoryProduct | None:
    """Fallback: resolve supplier SAGE # + item number via detail, then query 107."""
    detail = await client.get_product_detail(prod_eid=prod_eid, include_supplier_info=False)
    product = detail.product
    if not product.itemNum or not product.suppId:
        return None
    resp = await client.check_inventory(
        products=[InventoryProductRef(sageNum=product.suppId, itemNum=product.itemNum)]
    )
    return resp.products[0] if resp.products else None


async def _check_single(client: SageClient, prod_eid: int) -> InventoryProduct:
    """Inventory for one prodEId, falling back to suppId+itemNum lookup.

    Some SAGE records return unparseable JSON (err_num 0) — the item-num
    path bypasses them; if that also yields nothing, report ok=False.
    """
    try:
        ref = InventoryProductRef(productId=_service_product_id(prod_eid))
        resp = await client.check_inventory(products=[ref])
        entry = resp.products[0] if resp.products else None
    except SageAPIError as e:
        if e.err_num != 0:
            raise
        entry = None
    if entry is None or entry.ok is not True:
        try:
            entry = await _lookup_by_item_num(client, prod_eid) or entry
        except SageAPIError as e:
            if e.err_num != 0:
                raise
    if entry is None:
        entry = InventoryProduct(ok=False)
    entry.prodEId = prod_eid
    return entry


async def _check_by_prod_eids(client: SageClient, prod_eids: list[int]) -> InventoryResponse:
    refs = [InventoryProductRef(productId=_service_product_id(p)) for p in prod_eids]
    try:
        resp = await client.check_inventory(products=refs)
    except SageAPIError as e:
        if e.err_num != 0:
            raise
        # One poison record corrupts the whole batch response — isolate.
        products = [await _check_single(client, p) for p in prod_eids]
        return InventoryResponse(ok=any(p.ok is True for p in products), products=products)
    by_service_id = {_service_product_id(p): p for p in prod_eids}
    for i, entry in enumerate(resp.products):
        prod_eid = by_service_id.get(entry.productId)
        if prod_eid is None:
            continue
        if entry.ok is not True:
            fallback = await _lookup_by_item_num(client, prod_eid)
            if fallback is not None:
                resp.products[i] = entry = fallback
        entry.prodEId = prod_eid
    return resp


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

    Look up by product_ids (prodEIds from search/detail, batchable), or by
    supplier_sage_num + item_num. Each result carries prodEId for correlation;
    per-product ok=false means the supplier does not feed inventory to SAGE.
    Note: get_product_detail already includes this data — use this tool for
    quick re-checks or batching several products in one call.
    """
    client: SageClient = ctx.lifespan_context["sage_client"]
    if not product_ids and supplier_sage_num is None and item_num is None:
        raise ToolError("Provide product_ids or supplier_sage_num + item_num.")
    try:
        if supplier_sage_num is not None or item_num is not None:
            refs = [InventoryProductRef(sageNum=supplier_sage_num, itemNum=item_num)]
            direct = await client.check_inventory(products=refs)
            if not product_ids:
                return direct
            by_eid = await _check_by_prod_eids(client, product_ids)
            by_eid.products.extend(direct.products)
            return by_eid
        return await _check_by_prod_eids(client, product_ids or [])
    except SageAPIError as e:
        raise ToolError(str(e)) from e
