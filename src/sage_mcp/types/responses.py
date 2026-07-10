"""Response models for SAGE Connect API services.

All models use ``extra="ignore"`` so only the declared contract is
serialized back to MCP clients — the raw SAGE responses carry large
undocumented blobs (supplier policy text, duplicate alias keys) that
inflate payloads.

Alias note: SAGE returns most ``extraReturnFields`` keys UPPERCASE
(``DESCRIPTION``, ``CATEGORY``) but a few mixed-case (``suppID``,
``line``) — observed live 2026-07-09, diverging from the docs. Every
field therefore validates against AliasChoices covering both, and
serializes by clean field name.
"""

from __future__ import annotations

from pydantic import AliasChoices, BaseModel, Field

_PROD_EID_ALIAS = AliasChoices("prodEId", "prodEid")

# --- Search (Service 103) ---


class ProductSearchHit(BaseModel):
    """A single product from search results (ProductListRec)."""

    model_config = {"extra": "ignore", "populate_by_name": True}

    prodEId: int = Field(description="Product entity ID", validation_alias=_PROD_EID_ALIAS)
    spc: str = Field(default="", description="SAGE product code")
    name: str = Field(
        default="",
        description="Product name",
        validation_alias=AliasChoices("name", "prName"),
    )
    prc: str = Field(default="", description="Price range string (e.g. '0.66 - 1.42')")
    thumbPic: str = Field(default="", description="Thumbnail image URL")

    # Extra return fields (present only when requested via extraReturnFields)
    itemNum: str | None = Field(
        default=None, validation_alias=AliasChoices("ITEMNUM", "itemNum"),
        description="Supplier's item number",
    )
    category: str | None = Field(default=None, validation_alias=AliasChoices("CATEGORY", "category"))
    description: str | None = Field(
        default=None, validation_alias=AliasChoices("DESCRIPTION", "description")
    )
    colors: str | None = Field(default=None, validation_alias=AliasChoices("COLORS", "colors"))
    themes: str | None = Field(default=None, validation_alias=AliasChoices("THEMES", "themes"))
    supplier: str | None = Field(default=None, validation_alias=AliasChoices("SUPPLIER", "supplier"))
    suppId: int | None = Field(
        default=None, validation_alias=AliasChoices("suppID", "SUPPID", "suppId"),
        description="Supplier's SAGE ID",
    )
    lineName: str | None = Field(default=None, validation_alias=AliasChoices("line", "LINE", "lineName"))
    prodTime: str | None = Field(default=None, validation_alias=AliasChoices("PRODTIME", "prodTime"))


class SearchResponse(BaseModel):
    """Service 103 search response."""

    model_config = {"extra": "ignore"}

    ok: bool = False
    searchResponseMsg: str = ""
    totalFound: int = Field(default=0, description="Total matches (capped by maxTotalItems)")
    products: list[ProductSearchHit] = Field(default=[])
    legalNote: str = ""


# --- Shared inventory shapes (Services 105 + 107) ---


class SkuAttribute(BaseModel):
    """Variant attribute: typeId 10=Color, 11=Size, 12=Shape, 99=Other."""

    model_config = {"extra": "ignore"}

    typeId: int = 0
    name: str = ""
    value: str = ""


class SkuRecord(BaseModel):
    """Per-variant stock record shared by product detail and inventory status."""

    model_config = {"extra": "ignore"}

    attributes: list[SkuAttribute] = Field(default=[])
    onHand: int = Field(default=0, description="Units on hand (999,999,999 = unlimited)")
    onOrder: int = 0
    onOrderExpectedDate: str | None = None
    refreshLeadDays: int | None = None
    warehouseId: int | None = None
    warehouseCountry: str = ""
    warehouseZip: str = ""
    memo: str = ""
    unlimited: bool | None = None


# --- Product Detail (Service 105) ---


class SupplierInfo(BaseModel):
    """Supplier contact information from product detail.

    Deliberately excludes ``generalInfo`` (multi-KB policy/art-charge
    text) and ``pers*`` fields to keep MCP payloads lean.
    """

    model_config = {"extra": "ignore", "populate_by_name": True}

    suppId: int = Field(default=0, description="Supplier's SAGE ID")
    coName: str = Field(default="", description="Company name")
    lineName: str = ""
    contactName: str = Field(default="", description="Contact person")
    email: str = ""
    salesEmail: str = ""
    orderEmail: str = ""
    tel: str = ""
    tollFreeTel: str = ""
    web: str = Field(default="", description="Website URL")
    mCity: str = Field(default="", description="Mailing city")
    mState: str = ""
    mZip: str = ""
    mCountry: str = ""
    esg: str = Field(default="", description="ESG/diversity info")
    prefGroups: str = Field(
        default="", description="Preference group names (e.g. 'DGW Branded')"
    )
    prefGroupIds: str = Field(
        default="", validation_alias=AliasChoices("prefGroupIds", "prefGroupIDs")
    )
    comment: str = ""


class ProductImage(BaseModel):
    """An image from the product detail ``pics`` array."""

    model_config = {"extra": "ignore"}

    url: str = Field(default="", description="Image URL (RS= query param sets pixel size)")
    hasLogo: int = Field(default=0, description="1=with logo sample, 0=blank product")
    caption: str = Field(default="", description="Image caption (often the color)")
    index: int = 0


class OptionValue(BaseModel):
    """A single value within a product option (e.g. one imprint method)."""

    model_config = {"extra": "ignore"}

    value: str = ""
    prc: list[str] = Field(default=[])
    net: list[str] = Field(default=[])


class ProductOption(BaseModel):
    """A product option group (e.g. Imprint, Packaging, Add-Ons)."""

    model_config = {"extra": "ignore"}

    name: str = ""
    pricingIsTotal: int = 0
    priceCode: str = ""
    values: list[OptionValue] = Field(default=[])


class ProductDetail(BaseModel):
    """Full product detail from Service 105 (curated field set)."""

    model_config = {"extra": "ignore", "populate_by_name": True}

    prodEId: int = Field(description="Product entity ID", validation_alias=_PROD_EID_ALIAS)
    spc: str = Field(default="", description="SAGE product code")
    itemNum: str = Field(default="", description="Supplier's item number")
    prName: str = Field(default="", description="Product name")
    category: str = ""
    description: str = ""
    dimensions: str = ""
    keywords: str = ""
    colors: str = ""
    themes: str = ""
    suppId: int = Field(default=0, description="Supplier's SAGE ID")
    lineName: str = ""

    # Pricing (parallel arrays, indexes align with qty)
    qty: list[str] = Field(default=[], description="Quantity breakpoints")
    prc: list[str] = Field(default=[], description="Catalog prices per breakpoint")
    net: list[str] = Field(default=[], description="Confidential net cost per breakpoint")
    catPrc: list[str] = Field(default=[], description="Standard catalog pricing")
    priceCode: str = ""
    currency: str = ""
    priceIncludes: str = ""
    piecesPerUnit: list[str] = Field(default=[])
    options: list[ProductOption] = Field(default=[])

    # Decoration
    imprintArea: str = ""
    imprintLoc: str = ""
    secondImprintArea: str = ""
    secondImprintLoc: str = ""
    decorationMethod: str = ""
    setupChg: str = ""
    setupChgCode: str = ""
    repeatSetupChg: str = ""
    repeatSetupChgCode: str = ""
    addClrChg: str = ""
    addClrRunChg: list[str] = Field(default=[])

    # Logistics
    madeInCountry: str = ""
    assembledInCountry: str = ""
    decoratedInCountry: str = ""
    prodTime: str = Field(default="", description="Production time (e.g. '5 to 7 working days')")
    package: str = ""
    weightPerCarton: str = ""
    unitsPerCarton: str = ""
    cartonL: str = ""
    cartonW: str = ""
    cartonH: str = ""
    shipPointCountry: str = ""
    shipPointZip: str = ""

    # Flags / compliance
    verified: int = 0
    envFriendly: int = 0
    recyclable: int = 0
    newProduct: int = 0
    productCompliance: str = ""
    warningLbl: str = ""

    # Live inventory (also available standalone via Service 107)
    onHand: int = Field(default=0, description="Total units on hand across variants")
    skus: list[SkuRecord] = Field(default=[])
    inventoryLastUpdated: str = ""

    # Lifecycle
    comment: str = ""
    expDate: str = Field(default="", description="Pricing expiration date")
    discontinued: int = 0
    active: int = 1

    pics: list[ProductImage] = Field(default=[], description="Product images")
    supplier: SupplierInfo | None = None


class ProductDetailResponse(BaseModel):
    """Service 105 detail response wrapper."""

    model_config = {"extra": "ignore"}

    product: ProductDetail
    legalNote: str = ""


# --- Categories / Research List (Service 101) ---


class CategoryItem(BaseModel):
    """A single research-list entry — the API returns only id + name."""

    model_config = {"extra": "ignore"}

    id: int = Field(description="List value ID (use as category number in search)")
    name: str = Field(default="", description="Display name")


class CategoriesResponse(BaseModel):
    """Service 101 research list response."""

    model_config = {"extra": "ignore"}

    ok: bool = False
    items: list[CategoryItem] = Field(default=[])
    legalNote: str = ""


# --- Inventory Status (Service 107) ---


class InventoryProduct(BaseModel):
    """Inventory status for one product."""

    model_config = {"extra": "ignore"}

    productId: int = Field(default=0, description="SAGE-internal Service 107 product ID")
    prodEId: int | None = Field(
        default=None, description="The prodEId this entry answers (set by the MCP server)"
    )
    sageNum: int | None = Field(default=None, description="Supplier's SAGE #")
    itemNum: int | str | None = Field(default=None, description="Supplier's item number")
    ok: bool | None = None
    onHand: int = Field(default=0, description="Total units on hand (999,999,999 = unlimited)")
    skus: list[SkuRecord] = Field(default=[])
    lastUpdated: str = ""


class InventoryResponse(BaseModel):
    """Service 107 inventory response."""

    model_config = {"extra": "ignore"}

    ok: bool = False
    products: list[InventoryProduct] = Field(default=[])
