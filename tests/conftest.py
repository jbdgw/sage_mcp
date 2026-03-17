"""Shared fixtures for SAGE MCP tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from sage_mcp.client.sage_client import SageClient
from sage_mcp.settings import SageSettings


@pytest.fixture
def sage_settings() -> SageSettings:
    """Test settings — no real credentials needed for unit tests."""
    return SageSettings(
        acct_id=12345,
        login_id="testuser",
        auth_key="test-secret-key",
    )


@pytest.fixture
def mock_http_client() -> AsyncMock:
    """A mocked httpx.AsyncClient."""
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def sage_client(mock_http_client: AsyncMock, sage_settings: SageSettings) -> SageClient:
    """SageClient backed by a mocked httpx.AsyncClient."""
    return SageClient(http_client=mock_http_client, settings=sage_settings)


def make_httpx_response(data: dict[str, Any], status_code: int = 200) -> httpx.Response:
    """Build a real httpx.Response from a dict payload."""
    import json

    return httpx.Response(
        status_code=status_code,
        content=json.dumps(data).encode(),
        headers={"content-type": "application/json"},
        request=httpx.Request("POST", "https://www.promoplace.com/ws/ws.dll/ConnectAPI"),
    )


# --- Canonical Sage API response fixtures ---


SEARCH_RESPONSE_OK: dict[str, Any] = {
    "ok": True,
    "searchResponseMsg": "",
    "totalFound": 2,
    "products": [
        {
            "prodEId": 771822521,
            "spc": "FBJGK-GMSTH",
            "name": "Mini Flashlight Key Ring",
            "prc": "0.66 - 1.42",
            "thumbPic": "https://www.promoplace.com/ws/ws.dll/QPic?SN=50000&P=771822521&RS=150",
        },
        {
            "prodEId": 999000111,
            "spc": "ZZZZZ-YYYYY",
            "name": "LED Pen Light",
            "prc": "1.20 - 3.50",
            "thumbPic": "https://www.promoplace.com/ws/ws.dll/QPic?SN=50000&P=999000111&RS=150",
        },
    ],
}

DETAIL_RESPONSE_OK: dict[str, Any] = {
    "product": {
        "prodEId": 345733702,
        "category": "Belts, Belt Buckles",
        "suppId": 51530,
        "lineName": "Nexbelt",
        "spc": "NIRTG-MOFVA",
        "prName": "Custom Logo Fast Eddie Buckle",
        "description": "The Golfer's Survival tool",
        "qty": ["24", "100", "200", "250", "350"],
        "prc": ["74.70", "67.50", "62.10", "58.50", "56.70"],
        "priceIncludes": "Full color;1 side;1 location",
        "supplier": {
            "coName": "Nexbelt LLC",
            "contactName": "Ross Rodriguez",
            "email": "outdoorsales@nexbelt.com",
            "web": "www.promoplace.com/nexbelt",
        },
        "pics": [
            {"url": "https://example.com/pic1.jpg", "hasLogo": 1, "caption": "Logo view"},
            {"url": "https://example.com/pic2.jpg", "hasLogo": 0, "caption": ""},
        ],
    }
}

CATEGORIES_RESPONSE_OK: dict[str, Any] = {
    "items": [
        {"id": "1", "name": "Flashlights", "hasChildren": True, "productCount": 500},
        {"id": "2", "name": "Pens", "parentId": "1", "hasChildren": False},
    ]
}

INVENTORY_RESPONSE_OK: dict[str, Any] = {
    "inventory": [
        {
            "productId": "345733702",
            "warehouseId": "WH1",
            "warehouseName": "Main Warehouse",
            "sku": "NB-FEB-001",
            "stockLevel": 1500,
            "availableQuantity": 1200,
            "leadTime": 5,
            "attributes": {"color": "Black"},
        }
    ]
}

ERROR_RESPONSE_INVALID_CREDENTIALS: dict[str, Any] = {
    "ErrNum": 10008,
    "ErrMsg": "Incorrect AcctID, LoginID or Token",
}

ERROR_RESPONSE_PRODUCT_NOT_FOUND: dict[str, Any] = {
    "ErrNum": 10501,
    "ErrMsg": "Product not found",
}

ERROR_RESPONSE_SEARCH_INSUFFICIENT: dict[str, Any] = {
    "ErrNum": 10301,
    "ErrMsg": "Not enough search criteria specified",
}
