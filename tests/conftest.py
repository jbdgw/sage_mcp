"""Shared fixtures for SAGE MCP tests.

Response fixtures mirror the REAL wire format observed live on
2026-07-09 (which diverges from the docs in places): extraReturnFields
come back mostly UPPERCASE but ``suppID``/``line`` mixed-case, errors
use lowercase ``errNum``/``errMsg`` (sometimes numeric strings), and
Service 101 returns integer ids.
"""

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


# --- Canonical Sage API response fixtures (real wire shapes) ---


SEARCH_RESPONSE_OK: dict[str, Any] = {
    "ok": True,
    "searchResponseMsg": "",
    "totalFound": 2,
    "products": [
        {
            "prodEId": 105917761,
            "spc": "NBJXC-SZZDO",
            "name": "Atrium 25 oz Aluminum Bottle",
            "prc": "4.80 - 6.03",
            "thumbPic": "https://www.promoplace.com/ws/ws.dll/QPic?SN=60462&P=105917761&RS=150",
            # extraReturnFields: mostly UPPERCASE, but suppID/line mixed-case
            "ITEMNUM": "DBT-AT19",
            "CATEGORY": "Bottles",
            "DESCRIPTION": "Atrium 25 ounce Aluminum Bottle, single-wall construction",
            "COLORS": "Black, Blue, Gray",
            "THEMES": "Drinking, Office, Sports",
            "SUPPLIER": "Ariel Premium Supply",
            "suppID": 60462,
            "line": "Ariel Line",
            "PRODTIME": "5 to 7 working days",
        },
        {
            "prodEId": 771822521,
            "spc": "FBJGK-GMSTH",
            "prName": "Mini Flashlight Key Ring",
            "prc": "0.66 - 1.42",
            "thumbPic": "https://www.promoplace.com/ws/ws.dll/QPic?SN=50000&P=771822521&RS=150",
            "SUPPLIER": "Leed's",
            "suppID": 50000,
        },
    ],
    "legalNote": "ALL DATA (C) 2026 SAGE.",
}

DETAIL_RESPONSE_OK: dict[str, Any] = {
    "product": {
        "prodEId": 105917761,
        "category": "Bottles",
        "suppId": 60462,
        "lineName": "Ariel Line/Lin Line/Nayad",
        "spc": "NBJXC-SZZDO",
        "prName": "Atrium 25 oz Aluminum Bottle",
        "description": "Atrium 25 ounce Aluminum Bottle, single-wall construction",
        "dimensions": '10" H x 2.75" Diameter',
        "itemNum": "DBT-AT19",
        "qty": ["50", "100", "250", "500", "1000", "0"],
        "prc": ["6.03", "5.28", "5.12", "4.97", "4.80", ""],
        "net": ["3.62", "3.17", "3.08", "2.99", "2.88", ""],
        "priceCode": "CCCCC",
        "currency": "USD",
        "priceIncludes": "1 color;1 side;1 location",
        "options": [
            {
                "name": "Imprint",
                "pricingIsTotal": 0,
                "priceCode": "GGGGG",
                "values": [
                    {
                        "value": "Digital print: Full-Color Digital Print",
                        "prc": ["1.25", "1.25", "1.25", "1.25", "1.25", "0.00"],
                        "net": ["1.00", "1.00", "1.00", "1.00", "1.00", "0.00"],
                    }
                ],
            }
        ],
        "setupChg": "60",
        "setupChgCode": "G",
        "prodTime": "5 to 7 working days",
        "madeInCountry": "CN",
        "verified": 1,
        # Live inventory embedded in detail (Service 105)
        "onHand": "56341",
        "skus": [
            {
                "attributes": [{"typeId": 10, "value": "Black"}],
                "onHand": 5991,
                "onOrder": 0,
                "warehouseCountry": "US",
            },
            {
                "attributes": [{"typeId": 10, "value": "Blue"}],
                "onHand": 4464,
                "onOrder": 3000,
                "onOrderExpectedDate": "2026-07-29",
                "warehouseCountry": "US",
            },
        ],
        "inventoryLastUpdated": "2026-07-10T00:00:29Z",
        "expDate": "2026-12-31",
        "discontinued": 0,
        "active": 1,
        "supplier": {
            "suppId": 60462,
            "coName": "Ariel Premium Supply Inc",
            "contactName": "",
            "email": "customerservice@arielpremium.com",
            "web": "www.arielpremium.com",
            "tel": "314.890.0330",
            "mCity": "St Louis",
            "mState": "MO",
            "esg": "Asian/Pacific Islander owned, Minority owned",
            "prefGroupIDs": "15405",
            "prefGroups": "DGW Branded",
            # Multi-KB policy blob that must NOT leak into MCP payloads
            "generalInfo": {
                "artInfo": "Email digital artwork to customerservice@arielpremium.com",
                "imprintMethods": "Pad Printing, Screen Printing, Laser Engraving",
                "termsInfo": "A signed credit app & resale cert required for new accts.",
            },
        },
        "pics": [
            {
                "url": "https://www.promoplace.com/ws/ws.dll/QPic?SN=60462&P=105917761&RS=300&I=1",
                "hasLogo": 1,
                "caption": "",
                "index": 1,
            },
            {
                "url": "https://www.promoplace.com/ws/ws.dll/QPic?SN=60462&P=105917761&RS=300&I=3",
                "hasLogo": 0,
                "caption": "Black",
                "index": 3,
            },
        ],
    },
    "legalNote": "ALL DATA (C) 2026 SAGE.",
}

CATEGORIES_RESPONSE_OK: dict[str, Any] = {
    "ok": True,
    "items": [
        {"id": 118, "name": "Flashlights"},
        {"id": 224, "name": "Address Books"},
    ],
    "legalNote": "ALL DATA (C) 2026 SAGE.",
}

INVENTORY_RESPONSE_OK: dict[str, Any] = {
    "ok": True,
    "products": [
        {
            "productId": 105917761,
            "sageNum": 60462,
            "itemNum": "DBT-AT19",
            "ok": True,
            "onHand": 56341,
            "skus": [
                {
                    "attributes": [{"typeId": 10, "value": "Black"}],
                    "onHand": 5991,
                    "onOrder": 0,
                },
                {
                    "attributes": [{"typeId": 10, "value": "Blue"}],
                    "onHand": 4464,
                    "onOrder": 3000,
                    "onOrderExpectedDate": "2026-07-29",
                    "memo": "hot item, stock will run out quickly",
                },
            ],
            "lastUpdated": "2026-07-10T00:00:29Z",
        }
    ],
}

# Real SAGE errors use lowercase errNum/errMsg — sometimes numeric strings.
ERROR_RESPONSE_INVALID_CREDENTIALS: dict[str, Any] = {
    "ok": False,
    "errNum": 10008,
    "errMsg": "Incorrect AcctID, LoginID or Token",
}

ERROR_RESPONSE_PRODUCT_NOT_FOUND: dict[str, Any] = {
    "ok": False,
    "errNum": 10501,
    "errMsg": "Product not found",
}

ERROR_RESPONSE_SEARCH_INSUFFICIENT: dict[str, Any] = {
    "ok": False,
    "errNum": 10301,
    "errMsg": "Not enough search criteria specified",
}

ERROR_RESPONSE_INVENTORY_STRING_ERRNUM: dict[str, Any] = {
    "inventory": [],
    "ok": False,
    "errNum": "10701",
    "errMsg": "Include at least one product in the request.",
}

ERROR_RESPONSE_LEGACY_UPPERCASE: dict[str, Any] = {
    "ErrNum": 10008,
    "ErrMsg": "Incorrect AcctID, LoginID or Token",
}
