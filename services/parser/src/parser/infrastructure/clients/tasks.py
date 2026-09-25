import datetime
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Literal

from arq.jobs import Job


class TasksClient(ABC):
    @abstractmethod
    async def enqueue_clear_group_cache_task(
        self,
        groups: Iterable[dict[Literal["index", "number"], str]],
    ) -> Job | None:
        raise NotImplementedError

    @abstractmethod
    async def enqueue_clear_cabinet_cache_task(
        self,
        cabinets: Iterable[dict[Literal["index", "number"], str]],
    ) -> Job | None:
        raise NotImplementedError

    @abstractmethod
    async def enqueue_clear_group_schedule_cache_task(
        self,
        groups: Iterable[dict[Literal["index", "number"], str]],
        schedule_at: Literal["today", "tomorrow"],
    ) -> Job | None:
        raise NotImplementedError

    @abstractmethod
    async def enqueue_clear_cabinet_schedule_cache_task(
        self,
        cabinets: Iterable[dict[Literal["index", "number"], str]],
        schedule_at: Literal["today", "tomorrow"],
    ) -> Job | None:
        raise NotImplementedError

    @abstractmethod
    async def enqueue_send_group_schedule_notification_task(
        self,
        changes: dict[
            Literal["deleted", "modified", "published"],
            Iterable[dict[Literal["index", "number"], str]],
        ],
        schedule_at: Literal["today", "tomorrow"],
        schedule_dates: datetime.date | tuple[datetime.date, datetime.date],
    ) -> Job | None:
        raise NotImplementedError

    @abstractmethod
    async def enqueue_send_cabinet_schedule_notification_task(
        self,
        changes: dict[
            Literal["deleted", "modified", "published"],
            Iterable[dict[Literal["index", "number"], str]],
        ],
        schedule_at: Literal["today", "tomorrow"],
        schedule_dates: datetime.date | tuple[datetime.date, datetime.date],
    ) -> Job | None:
        raise NotImplementedError
