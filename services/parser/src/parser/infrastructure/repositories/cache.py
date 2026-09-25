from abc import ABC, abstractmethod
from typing import Literal


class CacheRepository(ABC):
    @abstractmethod
    async def has_schedule_changes(
        self,
        schedule_hash: str,
        schedule_at: Literal["today", "tomorrow"],
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def cache_schedule_hash(
        self,
        schedule_hash: str,
        schedule_at: Literal["today", "tomorrow"],
    ) -> None:
        raise NotImplementedError
