"""Domain value types and shared enums."""

from enum import IntEnum, StrEnum
from typing import Annotated

from pydantic import Field


# --- Domain value types ---

ProductEntityId = Annotated[int, Field(description="SAGE product entity ID (prodEId)")]
SageProductCode = Annotated[str, Field(description="SAGE product code (SPC)")]
SupplierId = Annotated[int, Field(description="SAGE supplier ID")]


# --- Enums ---


class CategoryListType(StrEnum):
    """Service 101 list types."""

    CATEGORIES = "categories"
    THEMES = "themes"
    COLORS = "colors"
    ESG_FLAGS = "esg-flags"


class SearchOrderBy(StrEnum):
    """Sort options for product search results."""

    RELEVANCE = "relevance"
    PRICE_LOW = "priceLow"
    PRICE_HIGH = "priceHigh"
    NAME = "name"
    SUPPLIER = "supplier"


class ImageSize(IntEnum):
    """Pixel sizes accepted by the SAGE image CDN."""

    SMALL = 100
    THUMBNAIL = 150
    MEDIUM = 200
    LARGE = 300
    FULL = 1800
