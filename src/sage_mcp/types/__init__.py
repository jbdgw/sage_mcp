"""Typed data contracts for the SAGE Connect API."""

from sage_mcp.types.auth import SageAuth
from sage_mcp.types.common import (
    CategoryListType,
    ImageSize,
    ProductEntityId,
    SageProductCode,
    SearchOrderBy,
    SupplierId,
)
from sage_mcp.types.errors import SageAPIError, SageErrorCode
from sage_mcp.types.requests import (
    CategoryRequest,
    InventoryRequest,
    ProductDetailRequest,
    SearchProductsRequest,
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

__all__ = [
    "CategoryItem",
    "CategoryListType",
    "CategoryRequest",
    "CategoriesResponse",
    "ImageSize",
    "InventoryItem",
    "InventoryRequest",
    "InventoryResponse",
    "ProductDetail",
    "ProductDetailRequest",
    "ProductDetailResponse",
    "ProductEntityId",
    "ProductImage",
    "ProductSearchHit",
    "SageAPIError",
    "SageAuth",
    "SageErrorCode",
    "SageProductCode",
    "SearchOrderBy",
    "SearchProductsRequest",
    "SearchRec",
    "SearchResponse",
    "SupplierId",
    "SupplierInfo",
]
