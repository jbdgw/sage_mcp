"""Request payload models for SAGE Connect API services."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchRec(BaseModel):
    """Search parameters for Service 103 (Product Search).

    All fields are optional — combine as needed. Maps directly to the
    SAGE ``search`` object in the wire payload (camelCase).
    """

    model_config = {"extra": "allow", "populate_by_name": True}

    # Core search
    keywords: str | None = Field(None, description="Free-text keyword search")
    categories: str | None = Field(None, description="Category name or number")
    spc: str | None = Field(None, description="SAGE product code")

    # Pricing / quantity
    priceLow: float | None = Field(None, description="Minimum price filter", ge=0)
    priceHigh: float | None = Field(None, description="Maximum price filter", ge=0)
    qty: int | None = Field(None, description="Quantity for pricing", gt=0)

    # Filters
    colors: str | None = Field(None, description="Color filter")
    themes: str | None = Field(None, description="Theme filter")
    madeIn: str | None = Field(None, description="Two-digit country code")
    envFriendly: bool | None = Field(None, description="Eco-friendly products only")
    verified: bool | None = Field(None, description="SAGE-verified products only")

    # Production
    prodTime: str | None = Field(None, description="Production time filter")
    productionDays: int | None = Field(None, description="Max production days", gt=0)

    # Supplier preferences
    prefGroups: str | None = Field(None, description="Supplier preference group IDs")
    supplierFav: str | None = Field(None, description="Supplier favorites filter")

    # Advanced
    applyPsPriceAdjustments: bool | None = Field(
        None, description="Apply global PromoSearch price adjustments"
    )
    extraReturnFields: str | None = Field(
        None, description="Comma-separated extra fields to return"
    )

    # Pagination / sorting
    orderBy: str | None = Field(None, description="Sort order for results")
    pageSize: int | None = Field(None, description="Results per page", gt=0)
    pageNumber: int | None = Field(None, description="Page number (1-based)", gt=0)
    limit: int | None = Field(None, description="Max results to return", gt=0)


class SearchProductsRequest(BaseModel):
    """Full wire payload for Service 103."""

    serviceId: int = 103
    apiVer: int = 130
    auth: dict[str, str | int]
    search: dict[str, str | int | float | bool]
    ref: str | None = Field(None, max_length=15)
    endBuyerSearch: bool | None = None


class ProductDetailRequest(BaseModel):
    """Full wire payload for Service 105."""

    serviceId: int = 105
    apiVer: int = 130
    auth: dict[str, str | int]
    prodEId: str | int
    includeSuppInfo: int = Field(1, description="1=include supplier info, 0=exclude")
    applyPsPriceAdjustments: bool | None = None
    ref: str | None = Field(None, max_length=15)


class InventoryRequest(BaseModel):
    """Full wire payload for Service 107."""

    serviceId: int = 107
    apiVer: int = 130
    auth: dict[str, str | int]
    prodEId: str | int
    ref: str | None = Field(None, max_length=15)


class CategoryRequest(BaseModel):
    """Full wire payload for Service 101."""

    serviceId: int = 101
    apiVer: int = 130
    auth: dict[str, str | int]
    listType: str
    parentId: str | None = None
    ref: str | None = Field(None, max_length=15)
