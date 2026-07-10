"""Tests for type layer: model construction, serialization, error classification."""

import pytest
from pydantic import ValidationError

from sage_mcp.types.auth import SageAuth
from sage_mcp.types.common import CategoryListType, ImageSize, SearchSortOrder
from sage_mcp.types.errors import SageAPIError, SageErrorCode
from sage_mcp.types.requests import (
    CategoryRequest,
    InventoryProductRef,
    InventoryRequest,
    ProductDetailRequest,
    SearchRec,
)
from sage_mcp.types.responses import (
    CategoriesResponse,
    InventoryResponse,
    ProductDetailResponse,
    ProductImage,
    ProductSearchHit,
    SearchResponse,
)
from tests.conftest import (
    CATEGORIES_RESPONSE_OK,
    DETAIL_RESPONSE_OK,
    INVENTORY_RESPONSE_OK,
    SEARCH_RESPONSE_OK,
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

    def test_pagination_uses_documented_sage_fields(self) -> None:
        """Payload caps come from maxRecs/startNum/maxTotalItems — the fields
        SAGE actually reads (the old limit/pageSize/pageNumber were ignored,
        producing 1000-product / 1MB responses)."""
        rec = SearchRec(keywords="water bottle", maxRecs=25, startNum=26, maxTotalItems=200)
        d = rec.model_dump(exclude_none=True)
        assert d == {
            "keywords": "water bottle",
            "maxRecs": 25,
            "startNum": 26,
            "maxTotalItems": 200,
        }

    def test_invented_fields_are_rejected(self) -> None:
        """extra='forbid': fields SAGE silently ignores must fail loudly."""
        with pytest.raises(ValidationError):
            SearchRec(keywords="pen", limit=50)  # type: ignore[call-arg]
        with pytest.raises(ValidationError):
            SearchRec(pageSize=25)  # type: ignore[call-arg]
        with pytest.raises(ValidationError):
            SearchRec(orderBy="priceLow")  # type: ignore[call-arg]

    def test_sort_accepts_documented_values_only(self) -> None:
        rec = SearchRec(sort="PRICEHIGHLOW")
        assert rec.sort == "PRICEHIGHLOW"
        with pytest.raises(ValidationError):
            SearchRec(sort="priceLow")  # type: ignore[arg-type]

    def test_prod_time_is_working_days_int(self) -> None:
        rec = SearchRec(prodTime=5)
        assert rec.prodTime == 5
        with pytest.raises(ValidationError):
            SearchRec(prodTime="5 Days")  # type: ignore[arg-type]

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

    def test_inventory_request_takes_products_array(self) -> None:
        """Service 107 wants {"products": [{"productId": N}]} — a top-level
        prodEId gets error 10701."""
        req = InventoryRequest(
            auth={"acctId": 1, "key": "k"},
            products=[InventoryProductRef(productId=345733702)],
        )
        assert req.serviceId == 107
        assert req.products[0].productId == 345733702

    def test_inventory_ref_supports_sage_num_and_item_num(self) -> None:
        ref = InventoryProductRef(sageNum=60462, itemNum="DBT-AT19")
        assert ref.model_dump(exclude_none=True) == {"sageNum": 60462, "itemNum": "DBT-AT19"}

    def test_category_request_list_type(self) -> None:
        req = CategoryRequest(
            auth={"acctId": 1, "key": "k"},
            listType="esg",
        )
        assert req.serviceId == 101
        assert req.listType == "esg"

    def test_category_request_rejects_invalid_list_type(self) -> None:
        """'colors' and 'esg-flags' are not Service 101 list types."""
        with pytest.raises(ValidationError):
            CategoryRequest(auth={"acctId": 1, "key": "k"}, listType="colors")  # type: ignore[arg-type]


# --- Response Models ---


class TestSearchResponse:
    def test_parses_real_wire_response(self) -> None:
        resp = SearchResponse.model_validate(SEARCH_RESPONSE_OK)
        assert resp.ok is True
        assert resp.totalFound == 2
        assert resp.products[0].prodEId == 105917761
        assert resp.products[0].prc == "4.80 - 6.03"

    def test_second_product_name_parses_from_prname_variant(self) -> None:
        """SAGE alternates between 'name' and 'prName' keys per product."""
        resp = SearchResponse.model_validate(SEARCH_RESPONSE_OK)
        assert resp.products[1].name == "Mini Flashlight Key Ring"

    def test_supp_id_parses_from_mixed_case_suppid_key(self) -> None:
        """SAGE returns 'suppID' (not the documented 'SUPPID') — the field
        must populate from the real key, not silently stay None."""
        resp = SearchResponse.model_validate(SEARCH_RESPONSE_OK)
        assert resp.products[0].suppId == 60462
        assert resp.products[1].suppId == 50000

    def test_line_name_parses_from_lowercase_line_key(self) -> None:
        resp = SearchResponse.model_validate(SEARCH_RESPONSE_OK)
        assert resp.products[0].lineName == "Ariel Line"

    def test_uppercase_extra_fields_map_to_clean_names(self) -> None:
        resp = SearchResponse.model_validate(SEARCH_RESPONSE_OK)
        hit = resp.products[0]
        assert hit.itemNum == "DBT-AT19"
        assert hit.category == "Bottles"
        assert hit.supplier == "Ariel Premium Supply"
        assert hit.prodTime == "5 to 7 working days"

    def test_serialization_has_no_duplicate_alias_keys(self) -> None:
        """Output must contain each datum once under its clean field name —
        no SUPPID/suppID or LINE/line duplicates inflating the payload."""
        resp = SearchResponse.model_validate(SEARCH_RESPONSE_OK)
        dumped = resp.products[0].model_dump()
        assert dumped["suppId"] == 60462
        assert dumped["lineName"] == "Ariel Line"
        assert "SUPPID" not in dumped
        assert "suppID" not in dumped
        assert "line" not in dumped
        assert "LINE" not in dumped

    def test_unknown_extra_fields_are_dropped(self) -> None:
        raw = {"ok": True, "totalFound": 0, "products": [], "newSageField": "surprise"}
        resp = SearchResponse.model_validate(raw)
        assert "newSageField" not in resp.model_dump()

    def test_empty_products_list(self) -> None:
        resp = SearchResponse.model_validate({"ok": True, "totalFound": 0, "products": []})
        assert resp.products == []

    def test_supp_id_defaults_to_none_when_absent(self) -> None:
        hit = ProductSearchHit.model_validate(
            {"prodEId": 1, "spc": "ABC", "name": "Test", "prc": "1.00", "thumbPic": ""}
        )
        assert hit.suppId is None


class TestProductDetailResponse:
    def test_parses_real_wire_response(self) -> None:
        resp = ProductDetailResponse.model_validate(DETAIL_RESPONSE_OK)
        product = resp.product
        assert product.prodEId == 105917761
        assert product.spc == "NBJXC-SZZDO"
        assert product.qty == ["50", "100", "250", "500", "1000", "0"]
        assert product.net[0] == "3.62"
        assert product.supplier is not None
        assert product.supplier.coName == "Ariel Premium Supply Inc"
        assert len(product.pics) == 2
        assert product.pics[0].hasLogo == 1

    def test_detail_includes_live_inventory(self) -> None:
        """Service 105 embeds inventory — apps should not need a second
        check_inventory call after get_product_detail."""
        resp = ProductDetailResponse.model_validate(DETAIL_RESPONSE_OK)
        assert resp.product.onHand == 56341  # coerced from wire string "56341"
        assert resp.product.skus[1].onOrder == 3000
        assert resp.product.skus[1].onOrderExpectedDate == "2026-07-29"
        assert resp.product.inventoryLastUpdated == "2026-07-10T00:00:29Z"

    def test_supplier_general_info_blob_is_dropped(self) -> None:
        """The multi-KB generalInfo policy text must not reach MCP clients."""
        resp = ProductDetailResponse.model_validate(DETAIL_RESPONSE_OK)
        assert resp.product.supplier is not None
        dumped = resp.product.supplier.model_dump()
        assert "generalInfo" not in dumped
        assert dumped["prefGroups"] == "DGW Branded"
        assert dumped["prefGroupIds"] == "15405"  # wire key is prefGroupIDs

    def test_options_pricing_parses(self) -> None:
        resp = ProductDetailResponse.model_validate(DETAIL_RESPONSE_OK)
        option = resp.product.options[0]
        assert option.name == "Imprint"
        assert option.values[0].prc[0] == "1.25"

    def test_qty_and_prc_are_string_lists(self) -> None:
        """SAGE returns qty/prc as lists of strings, not numbers."""
        resp = ProductDetailResponse.model_validate(DETAIL_RESPONSE_OK)
        assert all(isinstance(q, str) for q in resp.product.qty)
        assert all(isinstance(p, str) for p in resp.product.prc)


class TestCategoriesResponse:
    def test_parses_integer_ids(self) -> None:
        """Service 101 returns int ids — a str-typed id crashed the tool
        with 786 validation errors on the live API."""
        resp = CategoriesResponse.model_validate(CATEGORIES_RESPONSE_OK)
        assert len(resp.items) == 2
        assert resp.items[0].id == 118
        assert resp.items[0].name == "Flashlights"


class TestInventoryResponse:
    def test_parses_products_array(self) -> None:
        """Service 107 responds with 'products', not 'inventory'."""
        resp = InventoryResponse.model_validate(INVENTORY_RESPONSE_OK)
        assert resp.ok is True
        product = resp.products[0]
        assert product.productId == 105917761
        assert product.onHand == 56341
        assert product.skus[0].attributes[0].value == "Black"
        assert product.skus[1].memo == "hot item, stock will run out quickly"
        assert product.lastUpdated == "2026-07-10T00:00:29Z"


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

    def test_inventory_no_products(self) -> None:
        assert SageErrorCode.INVENTORY_NO_PRODUCTS == 10701

    def test_list_invalid_type(self) -> None:
        assert SageErrorCode.LIST_INVALID_TYPE == 10102


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
        assert CategoryListType.THEMES == "themes"
        assert CategoryListType.ESG == "esg"

    def test_image_size_values(self) -> None:
        assert ImageSize.THUMBNAIL == 150
        assert ImageSize.FULL == 1800

    def test_search_sort_matches_sage_documented_values(self) -> None:
        assert SearchSortOrder.BESTMATCH == "BESTMATCH"
        assert SearchSortOrder.PRICEHIGHLOW == "PRICEHIGHLOW"
