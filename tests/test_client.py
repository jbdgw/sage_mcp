"""Tests for SageClient — httpx mocked, verifying payload construction and response parsing."""

from __future__ import annotations

from unittest.mock import AsyncMock
from typing import Any

import pytest

from sage_mcp.client.sage_client import SageClient
from sage_mcp.types.errors import SageAPIError
from sage_mcp.types.requests import InventoryProductRef, SearchRec
from tests.conftest import (
    CATEGORIES_RESPONSE_OK,
    DETAIL_RESPONSE_OK,
    ERROR_RESPONSE_INVALID_CREDENTIALS,
    ERROR_RESPONSE_INVENTORY_STRING_ERRNUM,
    ERROR_RESPONSE_LEGACY_UPPERCASE,
    ERROR_RESPONSE_PRODUCT_NOT_FOUND,
    ERROR_RESPONSE_SEARCH_INSUFFICIENT,
    INVENTORY_RESPONSE_OK,
    SEARCH_RESPONSE_OK,
    make_httpx_response,
)


def sent_payload(mock_http_client: AsyncMock) -> dict[str, Any]:
    call_kwargs = mock_http_client.post.call_args
    return call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")


# --- _post (internal) ---


class TestClientPost:
    async def test_raises_on_lowercase_err_num(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        """SAGE returns lowercase errNum — the real wire format."""
        mock_http_client.post.return_value = make_httpx_response(
            ERROR_RESPONSE_INVALID_CREDENTIALS
        )
        with pytest.raises(SageAPIError) as exc_info:
            await sage_client._post({"serviceId": 103})
        assert exc_info.value.err_num == 10008
        assert exc_info.value.is_auth_error is True

    async def test_raises_on_string_err_num(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        """Service 107 returns errNum as a numeric STRING ('10701') — this
        previously slipped through and the tool returned empty data silently."""
        mock_http_client.post.return_value = make_httpx_response(
            ERROR_RESPONSE_INVENTORY_STRING_ERRNUM
        )
        with pytest.raises(SageAPIError) as exc_info:
            await sage_client._post({"serviceId": 107})
        assert exc_info.value.err_num == 10701
        assert "at least one product" in exc_info.value.err_msg

    async def test_raises_on_legacy_uppercase_err_num(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(
            ERROR_RESPONSE_LEGACY_UPPERCASE
        )
        with pytest.raises(SageAPIError) as exc_info:
            await sage_client._post({"serviceId": 103})
        assert exc_info.value.err_num == 10008

    async def test_returns_data_on_success(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(SEARCH_RESPONSE_OK)
        result = await sage_client._post({"serviceId": 103})
        assert result["ok"] is True


# --- Auth block ---


class TestAuthBlock:
    def test_build_auth_returns_correct_keys(self, sage_client: SageClient) -> None:
        auth = sage_client._build_auth()
        assert auth["acctId"] == 12345
        assert auth["loginId"] == "testuser"
        assert auth["key"] == "test-secret-key"


# --- search_products (Service 103) ---


class TestSearchProducts:
    async def test_happy_path_returns_search_response(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(SEARCH_RESPONSE_OK)
        search = SearchRec(keywords="water bottle")
        resp = await sage_client.search_products(search)
        assert resp.ok is True
        assert resp.totalFound == 2
        assert len(resp.products) == 2
        assert resp.products[0].spc == "NBJXC-SZZDO"

    async def test_payload_uses_documented_pagination_fields(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(SEARCH_RESPONSE_OK)
        search = SearchRec(keywords="pen", priceLow=1.0, priceHigh=5.0, maxRecs=25, startNum=1)
        await sage_client.search_products(search)

        payload = sent_payload(mock_http_client)
        assert payload["serviceId"] == 103
        assert payload["search"]["keywords"] == "pen"
        assert payload["search"]["priceLow"] == 1.0
        assert payload["search"]["maxRecs"] == 25
        assert payload["search"]["startNum"] == 1
        assert "limit" not in payload["search"]

    async def test_extra_return_fields_included(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(SEARCH_RESPONSE_OK)
        search = SearchRec(
            keywords="flashlight",
            extraReturnFields="ITEMNUM,CATEGORY,DESCRIPTION",
        )
        await sage_client.search_products(search)
        payload = sent_payload(mock_http_client)
        assert payload["search"]["extraReturnFields"] == "ITEMNUM,CATEGORY,DESCRIPTION"

    async def test_raises_on_insufficient_criteria(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(
            ERROR_RESPONSE_SEARCH_INSUFFICIENT
        )
        with pytest.raises(SageAPIError) as exc_info:
            await sage_client.search_products(SearchRec())
        assert exc_info.value.err_num == 10301


# --- get_product_detail (Service 105) ---


class TestGetProductDetail:
    async def test_happy_path_returns_product_detail(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(DETAIL_RESPONSE_OK)
        resp = await sage_client.get_product_detail(prod_eid=105917761)
        assert resp.product.prodEId == 105917761
        assert resp.product.spc == "NBJXC-SZZDO"
        assert resp.product.supplier is not None
        assert resp.product.supplier.coName == "Ariel Premium Supply Inc"

    async def test_payload_sends_include_supp_info_as_int(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(DETAIL_RESPONSE_OK)
        await sage_client.get_product_detail(prod_eid=105917761, include_supplier_info=True)
        payload = sent_payload(mock_http_client)
        assert payload["includeSuppInfo"] == 1
        assert isinstance(payload["includeSuppInfo"], int)

    async def test_accepts_spc_string(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(DETAIL_RESPONSE_OK)
        await sage_client.get_product_detail(prod_eid="NBJXC-SZZDO")
        payload = sent_payload(mock_http_client)
        assert payload["prodEId"] == "NBJXC-SZZDO"

    async def test_raises_on_product_not_found(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(
            ERROR_RESPONSE_PRODUCT_NOT_FOUND
        )
        with pytest.raises(SageAPIError) as exc_info:
            await sage_client.get_product_detail(prod_eid=999999999)
        assert exc_info.value.err_num == 10501


# --- check_inventory (Service 107) ---


class TestCheckInventory:
    async def test_happy_path_returns_inventory(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(INVENTORY_RESPONSE_OK)
        resp = await sage_client.check_inventory(
            products=[InventoryProductRef(productId=105917761)]
        )
        assert len(resp.products) == 1
        assert resp.products[0].onHand == 56341

    async def test_payload_sends_products_array(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        """Service 107 requires {"products": [...]} — the old top-level
        prodEId always returned error 10701."""
        mock_http_client.post.return_value = make_httpx_response(INVENTORY_RESPONSE_OK)
        await sage_client.check_inventory(
            products=[
                InventoryProductRef(productId=105917761),
                InventoryProductRef(productId=771822521),
            ]
        )
        payload = sent_payload(mock_http_client)
        assert payload["serviceId"] == 107
        assert payload["products"] == [
            {"productId": 105917761},
            {"productId": 771822521},
        ]
        assert "prodEId" not in payload

    async def test_raises_on_api_error(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(
            ERROR_RESPONSE_INVENTORY_STRING_ERRNUM
        )
        with pytest.raises(SageAPIError):
            await sage_client.check_inventory(products=[])


# --- get_categories (Service 101) ---


class TestGetCategories:
    async def test_happy_path_returns_categories(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(CATEGORIES_RESPONSE_OK)
        resp = await sage_client.get_categories(list_type="categories")
        assert len(resp.items) == 2
        assert resp.items[0].id == 118
        assert resp.items[0].name == "Flashlights"

    async def test_payload_has_no_parent_id(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        """Service 101 has no parentId field — the list is flat."""
        mock_http_client.post.return_value = make_httpx_response(CATEGORIES_RESPONSE_OK)
        await sage_client.get_categories(list_type="themes")
        payload = sent_payload(mock_http_client)
        assert payload["serviceId"] == 101
        assert payload["listType"] == "themes"
        assert "parentId" not in payload

    async def test_esg_list_type(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(CATEGORIES_RESPONSE_OK)
        await sage_client.get_categories(list_type="esg")
        payload = sent_payload(mock_http_client)
        assert payload["listType"] == "esg"
