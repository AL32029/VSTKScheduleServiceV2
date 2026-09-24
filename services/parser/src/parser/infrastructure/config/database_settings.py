import os
from typing import Literal

from database_manager.settings import BaseDevDatabaseSettings, BaseProdDatabaseSettings
from pydantic_settings import SettingsConfigDict


class DevDatabaseSettings(BaseDevDatabaseSettings):
    model_config = SettingsConfigDict(env_prefix="DATABASE_", extra="forbid")


class ProdDatabaseSettings(BaseProdDatabaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.getenv("DATABASE_SETTINGS_ENV", "/vault/secrets/database.env"),
        env_prefix="DATABASE_",
        extra="forbid",
    )


class DatabaseSettings:
    def __init__(self, mode: Literal["dev", "prod"] = "dev"):
        self.mode = mode
        self._config: DevDatabaseSettings | ProdDatabaseSettings = (
            DevDatabaseSettings() if mode == "dev" else ProdDatabaseSettings()
        )

    @property
    def config(self) -> "BaseDevDatabaseSettings | BaseProdDatabaseSettings":
        return self._config
