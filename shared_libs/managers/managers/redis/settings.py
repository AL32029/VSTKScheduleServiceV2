from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class BaseDevRedisSettings(BaseSettings):
    HOST: str
    PORT: int

    DB_NUMBER: int

    MAX_CONNECTIONS: int = Field(15)


class BaseProdRedisSettings(BaseSettings):
    HOST: str
    PORT: int

    DB_NUMBER: int

    MAX_CONNECTIONS: int = Field(15)

    SSL_CERT_REQS: Literal["none", "optional", "required"] = Field("required")

    SSL_CERT_FILE: str = Field("/vault/secrets/redis-tls.crt")
    SSL_KEY_FILE: str = Field("/vault/secrets/redis-tls.key")
    SSL_CA_CERT_FILE: str = Field("/vault/secrets/redis-tls.ca")

    SSL_CHECK_HOSTNAME: bool = Field(True)
