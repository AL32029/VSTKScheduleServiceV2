import logging
from typing import Literal

from redis.asyncio import Redis

from parser.infrastructure.repositories.cache import CacheRepository

logger = logging.getLogger(__name__)


class RedisCacheRepository(CacheRepository):
    def __init__(self, client: Redis):
        self._client = client

    async def has_schedule_changes(
        self,
        schedule_hash: str,
        schedule_at: Literal["today", "tomorrow"],
    ) -> bool:
        logger.debug(
            "Checking the schedule hash for '%s' against the cached one "
            "(hash=%s)",
            schedule_at,
            schedule_hash,
        )

        cached_hash = await self._client.hget("schedule_hash", schedule_at)

        if cached_hash is None:
            logger.debug(
                "No cached hash was found for '%s'",
                schedule_at,
            )
            return True

        logger.debug(
            "Cached hash for '%s': %s",
            schedule_at,
            cached_hash,
        )

        return schedule_hash == cached_hash

    async def cache_schedule_hash(
        self,
        schedule_hash: str,
        schedule_at: Literal["today", "tomorrow"],
    ) -> None:
        logger.debug(
            "Caching the schedule hash for '%s' (hash=%s)",
            schedule_at,
            schedule_hash,
        )

        await self._client.hset(
            "schedule_hash",
            schedule_at,
            schedule_hash,
        )

        logger.debug("The schedule hash for '%s' has been cached", schedule_at)
