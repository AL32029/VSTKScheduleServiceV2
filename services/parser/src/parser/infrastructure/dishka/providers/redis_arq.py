import logging
from collections.abc import AsyncIterable
from typing import Annotated

from arq import ArqRedis
from dishka import FromComponent, Provider, Scope, provide
from redis_manager.manager import RedisClientManager
from redis_manager.settings import BaseDevRedisSettings, BaseProdRedisSettings

from parser.infrastructure.config.redis_settings import RedisARQSettings

logger = logging.getLogger(__name__)


class RedisARQProvider(Provider):
    scope = Scope.APP
    component = "redis_arq"

    @provide
    def settings(
        self, settings: Annotated[RedisARQSettings, FromComponent("")]
    ) -> BaseDevRedisSettings | BaseProdRedisSettings:
        logger.debug(
            "Providing Redis settings (mode=%s, config=%s)",
            settings.mode,
            type(settings.config).__name__,
        )
        return settings.config

    @provide
    def manager(
        self, settings: BaseDevRedisSettings | BaseProdRedisSettings
    ) -> RedisClientManager:
        logger.debug(
            "Creating RedisClientManager with settings %s",
            type(settings).__name__,
        )
        return RedisClientManager(settings=settings, redis_type="arq")

    @provide(scope=Scope.REQUEST)
    async def provide_redis_client(
        self,
        manager: "RedisClientManager",
    ) -> AsyncIterable[ArqRedis]:
        logger.debug("Requesting a Redis client from the manager")

        client = await manager.get_client()

        logger.debug("Redis client has been obtained")

        yield client

        logger.debug("Redis client is no longer in use")
