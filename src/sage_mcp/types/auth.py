"""Wire-format auth block for SAGE Connect API requests."""

from pydantic import BaseModel


class SageAuth(BaseModel):
    """Auth payload matching the SAGE API wire format (camelCase)."""

    acctId: int
    loginId: str = ""
    key: str
