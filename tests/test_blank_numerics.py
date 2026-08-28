"""SAGE sends "" on optional numeric fields to mean "we have no figure".

Regression tests for the 2026-08-28 data-loss bug: a blank ``onHand`` raised
``int_parsing`` and took the whole ProductDetailResponse with it, so the KB's
cost lookup saw zero price breaks and blocked the presentation. Live repro
prodEIds: 325484683 (Bath Promotions CANDLE-14B-S-BOX-E) and 796511591
(Vivid Giftworks AS504).

Two invariants under test everywhere:
  * blank ("" / "   ") normalizes — to None for stock, to the default for flags
  * garbage ("abc") still raises; this is not a general "coerce anything" escape
"""

import pytest
from pydantic import ValidationError

from sage_mcp.types.responses import (
    CategoryItem,
    InventoryProduct,
    ProductDetail,
    ProductDetailResponse,
    ProductImage,
    ProductSearchHit,
    SearchResponse,
    SkuAttribute,
    SkuRecord,
    SupplierInfo,
)

BLANKS = ["", "   ", "\t"]


class TestOnHandUnknownIsNotZero:
    """None = SAGE published no figure; 0 = known-empty. Never collapse them."""

    @pytest.mark.parametrize("blank", BLANKS)
    def test_sku_record_blank_on_hand_is_none(self, blank: str) -> None:
        assert SkuRecord(onHand=blank).onHand is None

    @pytest.mark.parametrize("blank", BLANKS)
    def test_product_detail_blank_on_hand_is_none(self, blank: str) -> None:
        assert ProductDetail(prodEId=325484683, onHand=blank).onHand is None

    @pytest.mark.parametrize("blank", BLANKS)
    def test_inventory_product_blank_on_hand_is_none(self, blank: str) -> None:
        assert InventoryProduct(onHand=blank).onHand is None

    def test_blank_on_order_is_none(self) -> None:
        assert SkuRecord(onOrder="").onOrder is None

    def test_real_zero_stays_zero(self) -> None:
        """A published 0 means "known, none in stock" — distinct from unknown."""
        assert SkuRecord(onHand=0).onHand == 0
        assert ProductDetail(prodEId=1, onHand=0).onHand == 0
        assert InventoryProduct(onHand=0).onHand == 0

    def test_absent_on_hand_is_none_not_zero(self) -> None:
        assert SkuRecord().onHand is None
        assert ProductDetail(prodEId=1).onHand is None
        assert InventoryProduct().onHand is None

    def test_numeric_string_still_coerces(self) -> None:
        """The wire sends onHand as a string when it HAS a figure — keep that working."""
        assert ProductDetail(prodEId=1, onHand="56341").onHand == 56341
        assert SkuRecord(onHand="5991").onHand == 5991
        assert InventoryProduct(onHand="56341").onHand == 56341


class TestGarbageStillFails:
    """Only whitespace-only strings normalize. Do not widen this."""

    @pytest.mark.parametrize("garbage", ["abc", "1.5.2", "N/A", "twelve"])
    def test_non_numeric_string_raises(self, garbage: str) -> None:
        with pytest.raises(ValidationError):
            SkuRecord(onHand=garbage)
        with pytest.raises(ValidationError):
            ProductDetail(prodEId=1, onHand=garbage)
        with pytest.raises(ValidationError):
            InventoryProduct(onHand=garbage)

    def test_garbage_in_flag_fields_raises(self) -> None:
        with pytest.raises(ValidationError):
            ProductImage(hasLogo="abc")
        with pytest.raises(ValidationError):
            SupplierInfo(suppId="abc")


class TestBlankFlagsAndIdsFallToDefault:
    """Non-optional ints whose absent-value is a real default, not "unknown"."""

    def test_blank_supp_id_is_zero(self) -> None:
        assert SupplierInfo(suppId="").suppId == 0
        assert ProductDetail(prodEId=1, suppId="").suppId == 0

    def test_blank_image_flags_are_zero(self) -> None:
        img = ProductImage(hasLogo="", index="")
        assert img.hasLogo == 0
        assert img.index == 0

    def test_blank_compliance_flags_are_zero(self) -> None:
        p = ProductDetail(
            prodEId=1, verified="", envFriendly="", recyclable="", newProduct="", discontinued=""
        )
        assert (p.verified, p.envFriendly, p.recyclable, p.newProduct, p.discontinued) == (
            0,
            0,
            0,
            0,
            0,
        )

    def test_blank_active_keeps_its_nonzero_default(self) -> None:
        """``active`` defaults to 1 — a blank must not silently mark a product inactive."""
        assert ProductDetail(prodEId=1, active="").active == 1

    def test_blank_sku_attribute_type_id_is_zero(self) -> None:
        assert SkuAttribute(typeId="").typeId == 0

    def test_blank_total_found_is_zero(self) -> None:
        assert SearchResponse(totalFound="").totalFound == 0

    def test_blank_product_id_is_zero(self) -> None:
        assert InventoryProduct(productId="").productId == 0


class TestBlankOptionalIdsAreNone:
    def test_blank_search_hit_supp_id_is_none(self) -> None:
        assert ProductSearchHit(prodEId=1, suppID="").suppId is None

    def test_blank_optional_sku_fields_are_none(self) -> None:
        rec = SkuRecord(refreshLeadDays="", warehouseId="")
        assert rec.refreshLeadDays is None
        assert rec.warehouseId is None

    def test_blank_sage_num_is_none(self) -> None:
        assert InventoryProduct(sageNum="").sageNum is None


class TestRequiredIdsStillReject:
    """A blank on a REQUIRED identifier is a genuine error, not "unknown"."""

    def test_blank_prod_eid_raises(self) -> None:
        with pytest.raises(ValidationError):
            ProductSearchHit(prodEId="")
        with pytest.raises(ValidationError):
            ProductDetail(prodEId="")

    def test_blank_category_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            CategoryItem(id="")


class TestLiveRegression:
    """The exact shape that broke on 2026-08-28: blank onHand alongside real pricing."""

    def test_detail_response_with_blank_on_hand_keeps_pricing(self) -> None:
        payload = {
            "product": {
                "prodEId": 325484683,
                "spc": "CANDLE-14B-S-BOX-E",
                "prName": "Candle 14oz",
                "qty": ["50", "100", "250", "500", "1000", "2500"],
                "prc": ["36.00", "34.00", "33.75", "33.50", "33.25", "33.00"],
                "net": ["21.60", "20.40", "20.25", "20.10", "19.95", "19.80"],
                "onHand": "",
                "skus": [],
            },
            "legalNote": "ALL DATA (C) 2026 SAGE.",
        }
        resp = ProductDetailResponse.model_validate(payload)
        assert resp.product.onHand is None
        assert resp.product.qty == ["50", "100", "250", "500", "1000", "2500"]
        assert resp.product.net[0] == "21.60"


class TestRealWireFixture:
    """The conftest fixture mirroring the live 2026-08-28 payload."""

    def test_blank_onhand_fixture_parses_with_pricing_intact(self) -> None:
        from tests.conftest import DETAIL_RESPONSE_BLANK_ONHAND

        resp = ProductDetailResponse.model_validate(DETAIL_RESPONSE_BLANK_ONHAND)
        assert resp.product.onHand is None, "unknown stock must not be reported as 0"
        assert len(resp.product.net) == 6, "net cost must survive a blank stock figure"
        assert resp.product.net == ["21.60", "20.40", "20.25", "20.10", "19.95", "19.80"]
        assert resp.product.qty[0] == "50"

    def test_blank_onhand_serializes_as_null_not_zero(self) -> None:
        """MCP clients must be able to tell "unknown" from "out of stock"."""
        from tests.conftest import DETAIL_RESPONSE_BLANK_ONHAND

        dumped = ProductDetailResponse.model_validate(
            DETAIL_RESPONSE_BLANK_ONHAND
        ).model_dump()
        assert dumped["product"]["onHand"] is None
