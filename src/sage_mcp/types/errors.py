"""Error codes and typed exceptions for the SAGE Connect API."""

from enum import IntEnum


class SageErrorCode(IntEnum):
    """Known SAGE API error codes."""

    # General errors (100xx)
    GENERAL_ERROR = 10001
    SERVICE_UNAVAILABLE = 10002
    INVALID_HOST = 10003
    SSL_REQUIRED = 10004
    NO_POST_CONTENT = 10005
    INVALID_API_VERSION = 10006
    INVALID_ACCOUNT = 10007
    INVALID_CREDENTIALS = 10008
    INVALID_SERVICE_ID = 10009
    SERVICE_NOT_ENABLED = 10010
    ADVANTAGE_REQUIRED = 10011
    WORKPLACE_REQUIRED = 10012
    QUERY_LIMIT_REACHED = 10013

    # Search errors (103xx)
    SEARCH_INSUFFICIENT_CRITERIA = 10301
    SEARCH_ERROR = 10302
    SEARCH_TOO_MANY_ACTIVE = 10303
    SEARCH_SYSTEM_ERROR = 10304

    # Detail errors (105xx)
    PRODUCT_NOT_FOUND = 10501
    SUPPLIER_NOT_FOUND = 10502


_RETRYABLE_CODES = frozenset({
    SageErrorCode.SERVICE_UNAVAILABLE,
    SageErrorCode.SEARCH_TOO_MANY_ACTIVE,
    SageErrorCode.SEARCH_SYSTEM_ERROR,
})

_AUTH_CODES = frozenset({
    SageErrorCode.INVALID_ACCOUNT,
    SageErrorCode.INVALID_CREDENTIALS,
    SageErrorCode.ADVANTAGE_REQUIRED,
    SageErrorCode.WORKPLACE_REQUIRED,
    SageErrorCode.QUERY_LIMIT_REACHED,
})


class SageAPIError(Exception):
    """Typed error raised when the SAGE API returns a non-zero error code."""

    def __init__(self, err_num: int, err_msg: str) -> None:
        self.err_num = err_num
        self.err_msg = err_msg
        super().__init__(f"SAGE API error {err_num}: {err_msg}")

    @property
    def is_retryable(self) -> bool:
        return self.err_num in _RETRYABLE_CODES

    @property
    def is_auth_error(self) -> bool:
        return self.err_num in _AUTH_CODES
