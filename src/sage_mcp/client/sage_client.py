"""Async HTTP client for the SAGE Connect API."""

from __future__ import annotations

from typing import Any, Sequence

import httpx

from sage_mcp.settings import SageSettings
from sage_mcp.types.errors import SageAPIError
from sage_mcp.types.requests import CategoryListTypeName, InventoryProductRef, SearchRec
from sage_mcp.types.responses import (
    CategoriesResponse,
    InventoryResponse,
    ProductDetailResponse,
    SearchResponse,
)


def _extract_error(data: dict[str, Any]) -> tuple[int, str]:
    """Pull the error code/message from a SAGE response.

    SAGE returns lowercase ``errNum``/``errMsg`` (sometimes as numeric
    strings, e.g. ``"10701"``); older docs show ``ErrNum``/``ErrMsg``,
    so both spellings are accepted.
    """
    raw = data.get("errNum", data.get("ErrNum", 0))
    err_num = int(raw) if raw not in (None, "") else 0
    err_msg = str(data.get("errMsg") or data.get("ErrMsg") or "Unknown error")
    return err_num, err_msg


class SageClient:
    """Typed async client wrapping all SAGE Connect API services."""

    def __init__(self, http_client: httpx.AsyncClient, settings: SageSettings) -> None:
        self._http = http_client
        self._settings = settings

    def _build_auth(self) -> dict[str, str | int]:
        return {
            "acctId": self._settings.acct_id,
            "loginId": self._settings.login_id,
            "key": self._settings.auth_key.get_secret_value(),
        }

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send a POST to the SAGE API and return parsed JSON.

        Raises SageAPIError if the response contains a non-zero errNum.
        """
        response = await self._http.post(
            self._settings.api_url,
            json=payload,
            timeout=self._settings.request_timeout_seconds,
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()

        err_num, err_msg = _extract_error(data)
        if err_num != 0:
            raise SageAPIError(err_num=err_num, err_msg=err_msg)
        return data

    async def search_products(self, search: SearchRec) -> SearchResponse:
        """Service 103 — Product Search."""
        search_dict = search.model_dump(exclude_none=True)
        payload: dict[str, Any] = {
            "serviceId": 103,
            "apiVer": self._settings.api_version,
            "auth": self._build_auth(),
            "search": search_dict,
        }
        data = await self._post(payload)
        return SearchResponse.model_validate(data)

    async def get_product_detail(
        self,
        prod_eid: int | str,
        include_supplier_info: bool = True,
    ) -> ProductDetailResponse:
        """Service 105 — Product Detail (also returns live inventory)."""
        payload: dict[str, Any] = {
            "serviceId": 105,
            "apiVer": self._settings.api_version,
            "auth": self._build_auth(),
            "prodEId": prod_eid,
            "includeSuppInfo": 1 if include_supplier_info else 0,
        }
        data = await self._post(payload)
        return ProductDetailResponse.model_validate(data)

    async def check_inventory(
        self, products: Sequence[InventoryProductRef]
    ) -> InventoryResponse:
        """Service 107 — Inventory Status (batch: one request, many products)."""
        payload: dict[str, Any] = {
            "serviceId": 107,
            "apiVer": self._settings.api_version,
            "auth": self._build_auth(),
            "products": [p.model_dump(exclude_none=True) for p in products],
        }
        data = await self._post(payload)
        return InventoryResponse.model_validate(data)

    async def get_categories(self, list_type: CategoryListTypeName) -> CategoriesResponse:
        """Service 101 — Research List (categories/themes/esg)."""
        payload: dict[str, Any] = {
            "serviceId": 101,
            "apiVer": self._settings.api_version,
            "auth": self._build_auth(),
            "listType": list_type,
        }
        data = await self._post(payload)
        return CategoriesResponse.model_validate(data)
