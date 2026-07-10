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
    """Service 101 list types (per docs: categories, themes, esg)."""

    CATEGORIES = "categories"
    THEMES = "themes"
    ESG = "esg"


class SearchSortOrder(StrEnum):
    """Sort options accepted by Service 103 ``sort`` field."""

    BESTMATCH = "BESTMATCH"
    PRICE = "PRICE"
    PRICEHIGHLOW = "PRICEHIGHLOW"
    POPULARITY = "POPULARITY"
    PREFGROUP = "PREFGROUP"


class ImageSize(IntEnum):
    """Pixel sizes accepted by the SAGE image CDN (RS= query param)."""

    SMALL = 100
    THUMBNAIL = 150
    MEDIUM = 200
    LARGE = 300
    FULL = 1800
