from dishka import AsyncContainer
from dishka.async_container import make_async_container

from parser.infrastructure.config.database_settings import DatabaseSettings
from parser.infrastructure.config.system_settings import SystemSettings, system_settings
from parser.infrastructure.dishka.providers.database import DatabaseProvider


def generate_dishka_container() -> AsyncContainer:
    return make_async_container(
        DatabaseProvider(),
        context={
            SystemSettings: system_settings,
            DatabaseSettings: DatabaseSettings(mode=system_settings.SYSTEM_MODE),
        },
    )
