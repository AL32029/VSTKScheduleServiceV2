import os
from typing import Literal

from pydantic_settings import SettingsConfigDict
from redis_manager.settings import BaseDevRedisSettings, BaseProdRedisSettings


class DevRedisSettings(BaseDevRedisSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_", extra="forbid")


class ProdRedisSettings(BaseProdRedisSettings):
    model_config = SettingsConfigDict(
        env_file=os.getenv("REDIS_SETTINGS_ENV", "/vault/secrets/redis.env"),
        env_prefix="REDIS_",
        extra="forbid",
    )


class RedisSettings:
    def __init__(self, mode: Literal["dev", "prod"] = "dev"):
        self.mode = mode
        self._config: DevRedisSettings | ProdRedisSettings = (
            DevRedisSettings() if mode == "dev" else ProdRedisSettings()
        )

    @property
    def config(self) -> DevRedisSettings | ProdRedisSettings:
        return self._config


class DevRedisARQSettings(BaseDevRedisSettings):
    model_config = SettingsConfigDict(env_prefix="ARQ_REDIS_", extra="forbid")


class ProdRedisARQSettings(BaseProdRedisSettings):
    model_config = SettingsConfigDict(
        env_file=os.getenv("ARQ_REDIS_SETTINGS_ENV", "/vault/secrets/redis.env"),
        env_prefix="ARQ_REDIS_",
        extra="forbid",
    )


class RedisARQSettings:
    def __init__(self, mode: Literal["dev", "prod"] = "dev"):
        self.mode: Literal["dev", "prod"] = mode
        self._config: DevRedisARQSettings | ProdRedisARQSettings = (
            DevRedisARQSettings() if mode == "dev" else ProdRedisARQSettings()
        )

    @property
    def config(self) -> DevRedisARQSettings | ProdRedisARQSettings:
        return self._config
