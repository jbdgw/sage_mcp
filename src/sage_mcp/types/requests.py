"""Request payload models for SAGE Connect API services.

Field names match the official SAGE Connect docs exactly (Service 103
Request Field Layout, 2025-08 revision). ``extra="forbid"`` so invented
fields fail loudly instead of being silently ignored by SAGE.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SearchSort = Literal["BESTMATCH", "PRICE", "PRICEHIGHLOW", "POPULARITY", "PREFGROUP"]

CategoryListTypeName = Literal["categories", "themes", "esg"]


class SearchRec(BaseModel):
    """Search parameters for Service 103 (Product Search).

    All fields are optional — combine as needed. Maps directly to the
    SAGE ``search`` object in the wire payload (camelCase).
    """

    model_config = {"extra": "forbid", "populate_by_name": True}

    # Core search
    quickSearch: str | None = Field(
        default=None, description="Smart search — SAGE decides if input is a category, keyword, or SPC"
    )
    keywords: str | None = Field(default=None, description="Free-text keyword search")
    categories: str | None = Field(
        default=None, description="Category name or number (comma-separated for multiple)"
    )
    spc: str | None = Field(default=None, description="SAGE product code")
    itemNum: str | None = Field(default=None, description="Supplier's actual item number")
    itemNumExact: bool | None = Field(default=None, description="Exact item number matches only")
    itemName: str | None = Field(default=None, description="Product's item name")

    # Pricing / quantity
    priceLow: float | None = Field(default=None, description="Minimum price filter", ge=0)
    priceHigh: float | None = Field(default=None, description="Maximum price filter", ge=0)
    qty: int | None = Field(default=None, description="Quantity for pricing", gt=0)
    hideOldPricing: bool | None = Field(default=None, description="Hide pricing on expired products")

    # Filters
    colors: str | None = Field(default=None, description="Color filter")
    themes: str | None = Field(default=None, description="Theme filter")
    madeIn: str | None = Field(default=None, description="Two-digit country code")
    envFriendly: bool | None = Field(default=None, description="Eco-friendly products only")
    recyclable: bool | None = None
    verified: bool | None = Field(default=None, description="SAGE-verified products only")
    newProduct: bool | None = None
    popular: bool | None = Field(default=None, description="Popular items only")
    esg: str | None = Field(default=None, description="Comma-separated ESG/diversity flag IDs")
    allAudiences: bool | None = None
    endUserOnly: bool | None = Field(default=None, description="Only products OK to show end users")
    unionShop: bool | None = None
    updatedSince: str | None = Field(default=None, description="ISO 8601 UTC datetime filter")

    # Production
    prodTime: int | None = Field(
        default=None, description="Production time in working days (0/blank = any)", ge=0
    )
    includeRush: bool | None = Field(default=None, description="Include rush-service suppliers")

    # Supplier scoping
    prefGroups: str | None = Field(default=None, description="Supplier preference group IDs")
    suppId: int | None = Field(default=None, description="Supplier SAGE # to search within")
    lineName: str | None = Field(default=None, description="Specific supplier line name")
    siteCountry: str | None = Field(default=None, description="Two-digit site country code")

    # PromoSearch settings
    applyPsSearchRestrictions: bool | None = None
    applyPsPriceAdjustments: bool | None = Field(
        default=None, description="Apply global PromoSearch price adjustments"
    )

    # Response shaping
    sort: SearchSort | None = Field(default=None, description="Sort order (default BESTMATCH)")
    thumbPicRes: int | None = Field(
        default=None, description="Thumbnail resolution px: 100/150/200/300/1800 (default 150)"
    )
    extraReturnFields: str | None = Field(
        default=None, description="Comma-separated extra fields — materially increases response size"
    )
    maxTotalItems: int | None = Field(
        default=None, description="Cap on total matches (SAGE default 1000, max 50000)", gt=0
    )
    startNum: int | None = Field(default=None, description="First record to return (1-based)", gt=0)
    maxRecs: int | None = Field(default=None, description="Max records per page", gt=0)


class SearchProductsRequest(BaseModel):
    """Full wire payload for Service 103."""

    serviceId: int = 103
    apiVer: int = 130
    auth: dict[str, str | int]
    search: dict[str, str | int | float | bool]
    ref: str | None = Field(default=None, max_length=15)
    endBuyerSearch: bool | None = None


class ProductDetailRequest(BaseModel):
    """Full wire payload for Service 105."""

    serviceId: int = 105
    apiVer: int = 130
    auth: dict[str, str | int]
    prodEId: str | int
    includeSuppInfo: int = Field(default=1, description="1=include supplier info, 0=exclude")
    applyPsPriceAdjustments: bool | None = None
    ref: str | None = Field(default=None, max_length=15)


class InventoryProductRef(BaseModel):
    """One product to look up in Service 107 — by productId, or sageNum+itemNum."""

    model_config = {"extra": "forbid"}

    productId: int | None = None
    sageNum: int | None = Field(default=None, description="Supplier's SAGE # (ignored if productId set)")
    itemNum: str | None = Field(default=None, description="Item number (ignored if productId set)")


class InventoryRequest(BaseModel):
    """Full wire payload for Service 107 — takes an ARRAY of products."""

    serviceId: int = 107
    apiVer: int = 130
    auth: dict[str, str | int]
    products: list[InventoryProductRef]
    ref: str | None = Field(default=None, max_length=15)


class CategoryRequest(BaseModel):
    """Full wire payload for Service 101 (Research List).

    Valid listType values: "categories", "themes", "esg" — the service
    returns a flat id/name list with no parent/child hierarchy.
    """

    serviceId: int = 101
    apiVer: int = 130
    auth: dict[str, str | int]
    listType: CategoryListTypeName
    ref: str | None = Field(default=None, max_length=15)
