from dishka import AsyncContainer
from dishka.async_container import make_async_container

from parser.infrastructure.config.database_settings import DatabaseSettings
from parser.infrastructure.config.redis_settings import RedisSettings
from parser.infrastructure.config.system_settings import SystemSettings, system_settings
from parser.infrastructure.dishka.providers.database import DatabaseProvider
from parser.infrastructure.dishka.providers.redis_main import RedisMainProvider


def generate_dishka_container() -> AsyncContainer:
    return make_async_container(
        DatabaseProvider(),
        RedisMainProvider(),
        context={
            SystemSettings: system_settings,
            DatabaseSettings: DatabaseSettings(mode=system_settings.SYSTEM_MODE),
            RedisSettings: RedisSettings(mode=system_settings.SYSTEM_MODE),
        },
    )
