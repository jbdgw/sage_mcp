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

Blank numerics: SAGE sends ``""`` on optional numeric fields to mean "we
have no figure" — observed live 2026-08-28 on ``onHand`` for prodEIds
325484683 and 796511591, both of which publish full net pricing. A plain
``int`` field raises ``int_parsing`` on that blank (a ``default=`` does NOT
rescue it), and one blank takes the entire response down, so downstream
callers see a parse failure that is indistinguishable from "this supplier
publishes no cost". **Never declare a new SAGE integer as a bare ``int``.**
Use one of:

- ``BlankAsNone`` — anything measured (stock, counts, optional ids), where
  a blank genuinely means unknown. ``None`` and ``0`` stay distinct: ``None``
  = SAGE has no figure, ``0`` = known-empty. Collapsing them turns "unknown
  stock" into a false out-of-stock claim, so nothing may derive
  "unlimited"/"in stock" from a ``None``.
- ``BlankAsZero`` / ``BlankAsOne`` — non-optional flags and ids whose
  absent-value really is that default (``hasLogo``, ``suppId``, ``active``).

Garbage still fails: only whitespace-only strings normalize, ``"abc"``
raises. These are not general "coerce anything" validators. Required
identifiers (``prodEId``, ``CategoryItem.id``) stay bare ``int`` — a blank
there is a real error, not a missing figure.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import AliasChoices, BaseModel, BeforeValidator, Field

_PROD_EID_ALIAS = AliasChoices("prodEId", "prodEid")


# --- Blank-numeric normalization (see module docstring) ---


def _blank_to_none(v: object) -> object:
    """SAGE sends "" for "we have no figure" on optional numerics — that is unknown, not zero.

    Only whitespace-only strings become None; "abc" is still a validation error, and a real 0
    still means "known, none in stock". Scoped to SAGE response models by construction.
    """
    if isinstance(v, str) and not v.strip():
        return None
    return v


def _blank_to_default(default: int) -> object:
    """Build a validator mapping blank/absent → ``default`` for non-optional flag/id ints."""

    def _coerce(v: object) -> object:
        return default if _blank_to_none(v) is None else v

    return BeforeValidator(_coerce)


BlankAsNone = Annotated[int | None, BeforeValidator(_blank_to_none)]
"""Optional SAGE integer: "" / "   " / absent → None; "123" → 123; "abc" → ValidationError.

Use for anything measured (stock, counts, optional ids) where absence is genuinely unknown.
"""

BlankAsZero = Annotated[int, _blank_to_default(0)]
"""Non-optional SAGE integer whose absent-value is 0 anyway (flags, ids, counts) — never stock."""

BlankAsOne = Annotated[int, _blank_to_default(1)]
"""Non-optional SAGE integer defaulting to 1 (``active``), so a blank cannot flip it to 0."""

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
    suppId: BlankAsNone = Field(
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
    totalFound: BlankAsZero = Field(default=0, description="Total matches (capped by maxTotalItems)")
    products: list[ProductSearchHit] = Field(default=[])
    legalNote: str = ""


# --- Shared inventory shapes (Services 105 + 107) ---


class SkuAttribute(BaseModel):
    """Variant attribute: typeId 10=Color, 11=Size, 12=Shape, 99=Other."""

    model_config = {"extra": "ignore"}

    typeId: BlankAsZero = 0
    name: str = ""
    value: str = ""


class SkuRecord(BaseModel):
    """Per-variant stock record shared by product detail and inventory status."""

    model_config = {"extra": "ignore"}

    attributes: list[SkuAttribute] = Field(default=[])
    onHand: BlankAsNone = Field(
        default=None,
        description="Units on hand; null = SAGE published no figure (999,999,999 = unlimited)",
    )
    onOrder: BlankAsNone = Field(
        default=None, description="Units on order; null = no figure published"
    )
    onOrderExpectedDate: str | None = None
    refreshLeadDays: BlankAsNone = None
    warehouseId: BlankAsNone = None
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

    suppId: BlankAsZero = Field(default=0, description="Supplier's SAGE ID")
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
    hasLogo: BlankAsZero = Field(default=0, description="1=with logo sample, 0=blank product")
    caption: str = Field(default="", description="Image caption (often the color)")
    index: BlankAsZero = 0


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
    pricingIsTotal: BlankAsZero = 0
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
    suppId: BlankAsZero = Field(default=0, description="Supplier's SAGE ID")
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
    verified: BlankAsZero = 0
    envFriendly: BlankAsZero = 0
    recyclable: BlankAsZero = 0
    newProduct: BlankAsZero = 0
    productCompliance: str = ""
    warningLbl: str = ""

    # Live inventory (also available standalone via Service 107)
    onHand: BlankAsNone = Field(
        default=None,
        description="Total units on hand across variants; null = SAGE published no figure",
    )
    skus: list[SkuRecord] = Field(default=[])
    inventoryLastUpdated: str = ""

    # Lifecycle
    comment: str = ""
    expDate: str = Field(default="", description="Pricing expiration date")
    discontinued: BlankAsZero = 0
    active: BlankAsOne = 1

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

    productId: BlankAsZero = Field(default=0, description="SAGE-internal Service 107 product ID")
    prodEId: int | None = Field(
        default=None, description="The prodEId this entry answers (set by the MCP server)"
    )
    sageNum: BlankAsNone = Field(default=None, description="Supplier's SAGE #")
    itemNum: int | str | None = Field(default=None, description="Supplier's item number")
    ok: bool | None = None
    onHand: BlankAsNone = Field(
        default=None,
        description="Total units on hand; null = SAGE published no figure (999,999,999 = unlimited)",
    )
    skus: list[SkuRecord] = Field(default=[])
    lastUpdated: str = ""


class InventoryResponse(BaseModel):
    """Service 107 inventory response."""

    model_config = {"extra": "ignore"}

    ok: bool = False
    products: list[InventoryProduct] = Field(default=[])
