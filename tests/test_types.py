"""Tests for type layer: model construction, serialization, error classification."""

import pytest

from sage_mcp.types.auth import SageAuth
from sage_mcp.types.common import CategoryListType, ImageSize, SearchOrderBy
from sage_mcp.types.errors import SageAPIError, SageErrorCode
from sage_mcp.types.requests import (
    CategoryRequest,
    InventoryRequest,
    ProductDetailRequest,
    SearchRec,
)
from sage_mcp.types.responses import (
    CategoriesResponse,
    CategoryItem,
    InventoryItem,
    InventoryResponse,
    ProductDetail,
    ProductDetailResponse,
    ProductImage,
    ProductSearchHit,
    SearchResponse,
    SupplierInfo,
)


# --- SageAuth ---


class TestSageAuth:
    def test_constructs_with_required_fields(self) -> None:
        auth = SageAuth(acctId=12345, key="secret-key")
        assert auth.acctId == 12345
        assert auth.loginId == ""
        assert auth.key == "secret-key"

    def test_serializes_to_camelcase_dict(self) -> None:
        auth = SageAuth(acctId=99, loginId="user1", key="k")
        d = auth.model_dump()
        assert d == {"acctId": 99, "loginId": "user1", "key": "k"}

    def test_rejects_missing_acct_id(self) -> None:
        with pytest.raises(Exception):
            SageAuth(key="k")  # type: ignore[call-arg]


# --- SearchRec ---


class TestSearchRec:
    def test_empty_search_rec_is_valid(self) -> None:
        rec = SearchRec()
        d = rec.model_dump(exclude_none=True)
        assert d == {}

    def test_full_search_rec_serializes(self) -> None:
        rec = SearchRec(
            keywords="flashlight",
            categories="Flashlights",
            spc="FBJGK-GMSTH",
            priceLow=0.50,
            priceHigh=10.00,
            qty=100,
            colors="Red",
            themes="Safety",
            madeIn="US",
            envFriendly=True,
            verified=True,
            prodTime="5 Days",
            productionDays=5,
            orderBy="priceLow",
            pageSize=25,
            pageNumber=1,
            limit=1000,
        )
        d = rec.model_dump(exclude_none=True)
        assert d["keywords"] == "flashlight"
        assert d["priceLow"] == 0.50
        assert d["limit"] == 1000
        assert d["envFriendly"] is True

    def test_extra_fields_allowed(self) -> None:
        rec = SearchRec(keywords="pen", futureField="yes")  # type: ignore[call-arg]
        d = rec.model_dump(exclude_none=True)
        assert d["futureField"] == "yes"

    def test_price_low_rejects_negative(self) -> None:
        with pytest.raises(Exception):
            SearchRec(priceLow=-1.0)

    def test_qty_rejects_zero(self) -> None:
        with pytest.raises(Exception):
            SearchRec(qty=0)


# --- Request Payloads ---


class TestRequestPayloads:
    def test_search_request_defaults(self) -> None:
        from sage_mcp.types.requests import SearchProductsRequest

        req = SearchProductsRequest(
            auth={"acctId": 1, "key": "k"},
            search={"keywords": "pen"},
        )
        assert req.serviceId == 103
        assert req.apiVer == 130

    def test_product_detail_request_include_supp_info_is_int(self) -> None:
        req = ProductDetailRequest(
            auth={"acctId": 1, "key": "k"},
            prodEId=345733702,
        )
        assert req.includeSuppInfo == 1
        assert isinstance(req.includeSuppInfo, int)

    def test_inventory_request_service_id(self) -> None:
        req = InventoryRequest(
            auth={"acctId": 1, "key": "k"},
            prodEId="345733702",
        )
        assert req.serviceId == 107

    def test_category_request_list_type(self) -> None:
        req = CategoryRequest(
            auth={"acctId": 1, "key": "k"},
            listType="categories",
        )
        assert req.serviceId == 101
        assert req.listType == "categories"


# --- Response Models ---


class TestSearchResponse:
    def test_parses_sage_search_response(self) -> None:
        raw = {
            "ok": True,
            "searchResponseMsg": "",
            "totalFound": 1000,
            "products": [
                {
                    "prodEId": 771822521,
                    "spc": "FBJGK-GMSTH",
                    "name": "Mini Flashlight Key Ring",
                    "prc": "0.66 - 1.42",
                    "thumbPic": "https://www.promoplace.com/ws/ws.dll/QPic?SN=50000&P=771822521&RS=150",
                }
            ],
        }
        resp = SearchResponse.model_validate(raw)
        assert resp.ok is True
        assert resp.totalFound == 1000
        assert len(resp.products) == 1
        assert resp.products[0].prodEId == 771822521
        assert resp.products[0].prc == "0.66 - 1.42"

    def test_empty_products_list(self) -> None:
        resp = SearchResponse.model_validate({"ok": True, "totalFound": 0, "products": []})
        assert resp.products == []

    def test_extra_fields_preserved(self) -> None:
        raw = {"ok": True, "totalFound": 0, "products": [], "newSageField": "surprise"}
        resp = SearchResponse.model_validate(raw)
        assert resp.model_extra is not None
        assert resp.model_extra.get("newSageField") == "surprise"


class TestProductDetailResponse:
    def test_parses_sage_detail_response(self) -> None:
        raw = {
            "product": {
                "prodEId": 345733702,
                "category": "Belts, Belt Buckles",
                "suppId": 51530,
                "lineName": "Nexbelt",
                "spc": "NIRTG-MOFVA",
                "prName": "Custom Logo Fast Eddie Buckle",
                "description": "The Golfer's Survival tool",
                "qty": ["24", "100", "200", "250", "350"],
                "prc": ["74.70", "67.50", "62.10", "58.50", "56.70"],
                "priceIncludes": "Full color;1 side;1 location",
                "supplier": {
                    "coName": "Nexbelt LLC",
                    "contactName": "Ross Rodriguez",
                    "email": "outdoorsales@nexbelt.com",
                    "web": "www.promoplace.com/nexbelt",
                },
                "pics": [
                    {"url": "https://example.com/pic1.jpg", "hasLogo": 1, "caption": "Logo view"},
                    {"url": "https://example.com/pic2.jpg", "hasLogo": 0, "caption": ""},
                ],
            }
        }
        resp = ProductDetailResponse.model_validate(raw)
        product = resp.product
        assert product.prodEId == 345733702
        assert product.spc == "NIRTG-MOFVA"
        assert product.qty == ["24", "100", "200", "250", "350"]
        assert product.prc == ["74.70", "67.50", "62.10", "58.50", "56.70"]
        assert product.supplier is not None
        assert product.supplier.coName == "Nexbelt LLC"
        assert len(product.pics) == 2
        assert product.pics[0].hasLogo == 1

    def test_qty_and_prc_are_string_lists(self) -> None:
        """SAGE returns qty/prc as lists of strings, not numbers."""
        raw = {
            "product": {
                "prodEId": 1,
                "qty": ["24", "100"],
                "prc": ["74.70", "67.50"],
            }
        }
        resp = ProductDetailResponse.model_validate(raw)
        assert all(isinstance(q, str) for q in resp.product.qty)
        assert all(isinstance(p, str) for p in resp.product.prc)


class TestCategoriesResponse:
    def test_parses_category_items(self) -> None:
        raw = {
            "items": [
                {"id": "1", "name": "Flashlights", "hasChildren": True, "productCount": 500},
                {"id": "2", "name": "Pens", "parentId": "1", "hasChildren": False},
            ]
        }
        resp = CategoriesResponse.model_validate(raw)
        assert len(resp.items) == 2
        assert resp.items[0].hasChildren is True
        assert resp.items[1].parentId == "1"


class TestInventoryResponse:
    def test_parses_inventory_items(self) -> None:
        raw = {
            "inventory": [
                {
                    "productId": "345733702",
                    "warehouseId": "WH1",
                    "warehouseName": "Main Warehouse",
                    "sku": "NB-FEB-001",
                    "stockLevel": 1500,
                    "availableQuantity": 1200,
                    "leadTime": 5,
                    "attributes": {"color": "Black", "size": "One Size"},
                }
            ]
        }
        resp = InventoryResponse.model_validate(raw)
        assert len(resp.inventory) == 1
        item = resp.inventory[0]
        assert item.stockLevel == 1500
        assert item.attributes["color"] == "Black"


class TestProductImage:
    def test_has_logo_is_int_not_bool(self) -> None:
        img = ProductImage(url="https://example.com/pic.jpg", hasLogo=1)
        assert img.hasLogo == 1
        assert isinstance(img.hasLogo, int)


# --- Error Types ---


class TestSageErrorCode:
    def test_general_error_code_value(self) -> None:
        assert SageErrorCode.GENERAL_ERROR == 10001

    def test_search_insufficient_criteria(self) -> None:
        assert SageErrorCode.SEARCH_INSUFFICIENT_CRITERIA == 10301

    def test_product_not_found(self) -> None:
        assert SageErrorCode.PRODUCT_NOT_FOUND == 10501


class TestSageAPIError:
    def test_constructs_with_code_and_message(self) -> None:
        err = SageAPIError(10001, "General system error")
        assert err.err_num == 10001
        assert err.err_msg == "General system error"
        assert "10001" in str(err)

    def test_retryable_for_service_unavailable(self) -> None:
        err = SageAPIError(10002, "Service not available right now")
        assert err.is_retryable is True

    def test_not_retryable_for_invalid_credentials(self) -> None:
        err = SageAPIError(10008, "Incorrect credentials")
        assert err.is_retryable is False

    def test_auth_error_for_invalid_credentials(self) -> None:
        err = SageAPIError(10008, "Incorrect credentials")
        assert err.is_auth_error is True

    def test_auth_error_for_query_limit(self) -> None:
        err = SageAPIError(10013, "Query limit reached")
        assert err.is_auth_error is True

    def test_not_auth_error_for_search_error(self) -> None:
        err = SageAPIError(10302, "Search error")
        assert err.is_auth_error is False

    def test_retryable_for_too_many_active_searches(self) -> None:
        err = SageAPIError(10303, "Too many active searches")
        assert err.is_retryable is True


# --- Enums ---


class TestEnums:
    def test_category_list_type_values(self) -> None:
        assert CategoryListType.CATEGORIES == "categories"
        assert CategoryListType.ESG_FLAGS == "esg-flags"

    def test_image_size_values(self) -> None:
        assert ImageSize.THUMBNAIL == 150
        assert ImageSize.FULL == 1800

    def test_search_order_by_values(self) -> None:
        assert SearchOrderBy.RELEVANCE == "relevance"
        assert SearchOrderBy.PRICE_LOW == "priceLow"
