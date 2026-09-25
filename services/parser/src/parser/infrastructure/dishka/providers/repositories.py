import logging
from typing import Annotated

from dishka import FromComponent, Provider, Scope, provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from parser.infrastructure.repositories.cache import CacheRepository
from parser.infrastructure.repositories.redis_cache import RedisCacheRepository
from parser.infrastructure.repositories.schedule import ScheduleRepository
from parser.infrastructure.repositories.sqlalchemy_schedule import (
    SQLAlchemyScheduleRepository,
)

logger = logging.getLogger(__name__)


class RepositoriesProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def schedule_repository(
        self,
        db_session: AsyncSession,
    ) -> ScheduleRepository:
        logger.debug("Creating SQLAlchemyScheduleRepository")
        return SQLAlchemyScheduleRepository(session=db_session)

    @provide
    def cache_repository(
        self,
        redis_client: Annotated[Redis, FromComponent("redis_main")],
    ) -> CacheRepository:
        logger.debug("Creating RedisCacheRepository with the redis_main client")
        return RedisCacheRepository(client=redis_client)
