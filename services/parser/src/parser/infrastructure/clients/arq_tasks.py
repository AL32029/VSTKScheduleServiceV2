import datetime
from collections.abc import Iterable
from typing import Literal

from arq import ArqRedis
from arq.jobs import Job

from parser.infrastructure.clients.tasks import TasksClient


class ARQTasksClient(TasksClient):
    def __init__(self, redis_client: ArqRedis):
        self._client = redis_client

    async def enqueue_clear_group_cache_task(
        self,
        groups: Iterable[dict[Literal["index", "number"], str]],
    ) -> Job | None:
        job = await self._client.enqueue_job(
            "clear_group_cache",
            _queue_name="cache",
            groups=list(groups),
        )

        return job

    async def enqueue_clear_cabinet_cache_task(
        self,
        cabinets: Iterable[dict[Literal["index", "number"], str]],
    ) -> Job | None:
        job = await self._client.enqueue_job(
            "clear_cabinet_cache",
            _queue_name="cache",
            cabinets=list(cabinets),
        )

        return job

    async def enqueue_clear_group_schedule_cache_task(
        self,
        groups: Iterable[dict[Literal["index", "number"], str]],
        schedule_at: Literal["today", "tomorrow"],
    ) -> Job | None:
        job = await self._client.enqueue_job(
            "clear_group_schedule_cache",
            _queue_name="cache",
            groups=list(groups),
            schedule_at=schedule_at,
        )

        return job

    async def enqueue_clear_cabinet_schedule_cache_task(
        self,
        cabinets: Iterable[dict[Literal["index", "number"], str]],
        schedule_at: Literal["today", "tomorrow"],
    ) -> Job | None:
        job = await self._client.enqueue_job(
            "clear_cabinet_schedule_cache",
            _queue_name="cache",
            cabinets=list(cabinets),
            schedule_at=schedule_at,
        )

        return job

    async def enqueue_send_group_schedule_notification_task(
        self,
        changes: dict[
            Literal["deleted", "modified", "published"],
            Iterable[dict[Literal["index", "number"], str]],
        ],
        schedule_at: Literal["today", "tomorrow"],
        schedule_dates: datetime.date | tuple[datetime.date, datetime.date],
    ) -> Job | None:
        job = await self._client.enqueue_job(
            "send_group_schedule_notification",
            _queue_name="notifications",
            changes=changes,
            schedule_at=schedule_at,
            schedule_date=schedule_dates,
            _defer_by=15,
        )

        return job

    async def enqueue_send_cabinet_schedule_notification_task(
        self,
        changes: dict[
            Literal["deleted", "modified", "published"],
            Iterable[dict[Literal["index", "number"], str]],
        ],
        schedule_at: Literal["today", "tomorrow"],
        schedule_dates: datetime.date | tuple[datetime.date, datetime.date],
    ) -> Job | None:
        job = await self._client.enqueue_job(
            "send_cabinet_schedule_notification",
            _queue_name="notifications",
            changes=changes,
            schedule_at=schedule_at,
            schedule_date=schedule_dates,
            _defer_by=15,
        )

        return job
