"""Response models for SAGE Connect API services.

All models use ``extra="allow"`` to capture undocumented fields
the SAGE API may return without breaking deserialization.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# --- Search (Service 103) ---


class ProductSearchHit(BaseModel):
    """A single product from search results."""

    model_config = {"extra": "allow"}

    prodEId: int = Field(description="Product entity ID")
    spc: str = Field(default="", description="SAGE product code")
    name: str = Field(default="", description="Product name")
    prc: str = Field(default="", description="Price range string (e.g. '0.66 - 1.42')")
    thumbPic: str = Field(default="", description="Thumbnail image URL")

    # Extra return fields (populated when extraReturnFields is set)
    category: str | None = Field(None, alias="CATEGORY")
    description: str | None = Field(None, alias="DESCRIPTION")
    colors: str | None = Field(None, alias="COLORS")
    themes: str | None = Field(None, alias="THEMES")
    supplier: str | None = Field(None, alias="SUPPLIER")
    lineName: str | None = Field(None, alias="LINE")
    prodTime: str | None = Field(None, alias="PRODTIME")
    itemNum: str | None = Field(None, alias="ITEMNUM")


class SearchResponse(BaseModel):
    """Service 103 search response."""

    model_config = {"extra": "allow"}

    ok: bool = False
    searchResponseMsg: str = ""
    totalFound: int = 0
    products: list[ProductSearchHit] = Field(default_factory=list)


# --- Product Detail (Service 105) ---


class SupplierInfo(BaseModel):
    """Supplier contact information from product detail."""

    model_config = {"extra": "allow"}

    coName: str = Field(default="", description="Company name")
    contactName: str = Field(default="", description="Contact person")
    email: str = Field(default="", description="Contact email")
    web: str = Field(default="", description="Website URL")


class ProductImage(BaseModel):
    """An image from the product detail ``pics`` array."""

    model_config = {"extra": "allow"}

    url: str = Field(default="", description="Image URL")
    hasLogo: int = Field(default=0, description="1=with logo sample, 0=blank product")
    caption: str = Field(default="", description="Image caption")


class ProductDetail(BaseModel):
    """Full product detail from Service 105."""

    model_config = {"extra": "allow"}

    prodEId: int = Field(description="Product entity ID")
    category: str = Field(default="", description="Product category")
    suppId: int = Field(default=0, description="Supplier ID")
    lineName: str = Field(default="", description="Product line name")
    spc: str = Field(default="", description="SAGE product code")
    prName: str = Field(default="", description="Product name")
    description: str = Field(default="", description="Full product description")
    qty: list[str] = Field(default_factory=list, description="Quantity breakpoints (strings)")
    prc: list[str] = Field(default_factory=list, description="Prices parallel to qty (strings)")
    priceIncludes: str = Field(default="", description="What the price includes")
    supplier: SupplierInfo | None = None
    pics: list[ProductImage] = Field(default_factory=list, description="Product images")


class ProductDetailResponse(BaseModel):
    """Service 105 detail response wrapper."""

    model_config = {"extra": "allow"}

    product: ProductDetail


# --- Categories (Service 101) ---


class CategoryItem(BaseModel):
    """A single category/theme/color list entry."""

    model_config = {"extra": "allow"}

    id: str = Field(default="", description="Category identifier")
    name: str = Field(default="", description="Display name")
    description: str | None = Field(None, description="Category description")
    parentId: str | None = Field(None, description="Parent category ID")
    hasChildren: bool = Field(default=False, description="Has subcategories")
    productCount: int | None = Field(None, description="Products in category")


class CategoriesResponse(BaseModel):
    """Service 101 categories response."""

    model_config = {"extra": "allow"}

    items: list[CategoryItem] = Field(default_factory=list)


# --- Inventory (Service 107) ---


class InventoryItem(BaseModel):
    """A single inventory entry per warehouse/SKU."""

    model_config = {"extra": "allow"}

    productId: str = Field(default="", description="Product identifier")
    warehouseId: str = Field(default="", description="Warehouse identifier")
    warehouseName: str = Field(default="", description="Warehouse display name")
    sku: str = Field(default="", description="SKU for this variant")
    stockLevel: int = Field(default=0, description="Total stock level")
    availableQuantity: int = Field(default=0, description="Available to order")
    leadTime: int = Field(default=0, description="Lead time in business days")
    expectedRestockDate: str | None = Field(None, description="ISO date of next restock")
    attributes: dict[str, str] = Field(
        default_factory=dict, description="Variant attributes (color, size)"
    )


class InventoryResponse(BaseModel):
    """Service 107 inventory response."""

    model_config = {"extra": "allow"}

    inventory: list[InventoryItem] = Field(default_factory=list)
