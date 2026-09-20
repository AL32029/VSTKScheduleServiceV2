from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class BaseDevDatabaseSettings(BaseSettings):
    HOST: str
    PORT: int

    USER: str | None = Field(None)
    PASSWORD: str | None = Field(None)

    BASE: str

    POOL_SIZE: int = Field(5)
    MAX_OVERFLOW: int = Field(10)


class BaseProdDatabaseSettings(BaseSettings):
    HOST: str
    PORT: int

    BASE: str

    POOL_SIZE: int = Field(5)
    MAX_OVERFLOW: int = Field(10)

    SSL_CERT_REQS: Literal["none", "optional", "required"] = Field("required")

    SSL_CERT_FILE: str = Field(default="/vault/secrets/database-tls.crt")
    SSL_KEY_FILE: str = Field(default="/vault/secrets/database-tls.key")
    SSL_CA_CERT_FILE: str = Field(default="/vault/secrets/database-tls.ca")

    SSL_CHECK_HOSTNAME: bool = Field(True)
