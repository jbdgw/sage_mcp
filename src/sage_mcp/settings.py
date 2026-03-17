"""Application settings loaded from environment variables."""

from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class SageSettings(BaseSettings):
    """SAGE Connect API credentials and configuration."""

    model_config = {"env_prefix": "SAGE_"}

    acct_id: int
    login_id: str = ""
    auth_key: SecretStr
    api_url: str = "https://www.promoplace.com/ws/ws.dll/ConnectAPI"
    api_version: int = 130
    request_timeout_seconds: float = 30.0


class ServerSettings(BaseSettings):
    """MCP server transport configuration."""

    model_config = {"env_prefix": "MCP_"}

    host: str = "127.0.0.1"
    port: int = 9000
    transport: Literal["http", "stdio"] = "http"
