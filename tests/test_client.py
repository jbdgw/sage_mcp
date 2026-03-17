"""Tests for SageClient — httpx mocked, verifying payload construction and response parsing."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from sage_mcp.client.sage_client import SageClient
from sage_mcp.types.errors import SageAPIError
from sage_mcp.types.requests import SearchRec
from tests.conftest import (
    CATEGORIES_RESPONSE_OK,
    DETAIL_RESPONSE_OK,
    ERROR_RESPONSE_INVALID_CREDENTIALS,
    ERROR_RESPONSE_PRODUCT_NOT_FOUND,
    ERROR_RESPONSE_SEARCH_INSUFFICIENT,
    INVENTORY_RESPONSE_OK,
    SEARCH_RESPONSE_OK,
    make_httpx_response,
)


# --- _post (internal) ---


class TestClientPost:
    async def test_raises_sage_api_error_on_err_num(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(
            ERROR_RESPONSE_INVALID_CREDENTIALS
        )
        with pytest.raises(SageAPIError) as exc_info:
            await sage_client._post({"serviceId": 103})
        assert exc_info.value.err_num == 10008
        assert exc_info.value.is_auth_error is True

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
        search = SearchRec(keywords="flashlight")
        resp = await sage_client.search_products(search)
        assert resp.ok is True
        assert resp.totalFound == 2
        assert len(resp.products) == 2
        assert resp.products[0].spc == "FBJGK-GMSTH"

    async def test_payload_includes_search_rec_fields(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(SEARCH_RESPONSE_OK)
        search = SearchRec(keywords="pen", priceLow=1.0, priceHigh=5.0, limit=50)
        await sage_client.search_products(search)

        # Verify the payload sent to httpx
        call_kwargs = mock_http_client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["serviceId"] == 103
        assert payload["search"]["keywords"] == "pen"
        assert payload["search"]["priceLow"] == 1.0
        assert payload["search"]["limit"] == 50

    async def test_extra_return_fields_included(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(SEARCH_RESPONSE_OK)
        search = SearchRec(
            keywords="flashlight",
            extraReturnFields="ITEMNUM,CATEGORY,DESCRIPTION",
        )
        await sage_client.search_products(search)
        call_kwargs = mock_http_client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
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
        resp = await sage_client.get_product_detail(prod_eid=345733702)
        assert resp.product.prodEId == 345733702
        assert resp.product.spc == "NIRTG-MOFVA"
        assert resp.product.supplier is not None
        assert resp.product.supplier.coName == "Nexbelt LLC"

    async def test_payload_sends_include_supp_info_as_int(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(DETAIL_RESPONSE_OK)
        await sage_client.get_product_detail(prod_eid=345733702, include_supplier_info=True)
        call_kwargs = mock_http_client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["includeSuppInfo"] == 1
        assert isinstance(payload["includeSuppInfo"], int)

    async def test_accepts_spc_string(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(DETAIL_RESPONSE_OK)
        await sage_client.get_product_detail(prod_eid="NIRTG-MOFVA")
        call_kwargs = mock_http_client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["prodEId"] == "NIRTG-MOFVA"

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
        resp = await sage_client.check_inventory(product_id="345733702")
        assert len(resp.inventory) == 1
        assert resp.inventory[0].stockLevel == 1500

    async def test_payload_structure(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(INVENTORY_RESPONSE_OK)
        await sage_client.check_inventory(product_id="345733702")
        call_kwargs = mock_http_client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["serviceId"] == 107
        assert payload["prodEId"] == "345733702"

    async def test_raises_on_api_error(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(
            ERROR_RESPONSE_PRODUCT_NOT_FOUND
        )
        with pytest.raises(SageAPIError):
            await sage_client.check_inventory(product_id="000")


# --- get_categories (Service 101) ---


class TestGetCategories:
    async def test_happy_path_returns_categories(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(CATEGORIES_RESPONSE_OK)
        resp = await sage_client.get_categories(list_type="categories")
        assert len(resp.items) == 2
        assert resp.items[0].name == "Flashlights"

    async def test_payload_includes_list_type_and_parent(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(CATEGORIES_RESPONSE_OK)
        await sage_client.get_categories(list_type="themes", parent_id="42")
        call_kwargs = mock_http_client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["serviceId"] == 101
        assert payload["listType"] == "themes"
        assert payload["parentId"] == "42"

    async def test_parent_id_omitted_when_none(
        self, sage_client: SageClient, mock_http_client: AsyncMock
    ) -> None:
        mock_http_client.post.return_value = make_httpx_response(CATEGORIES_RESPONSE_OK)
        await sage_client.get_categories(list_type="categories")
        call_kwargs = mock_http_client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert "parentId" not in payload
