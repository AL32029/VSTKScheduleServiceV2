import logging
from typing import Annotated

from arq import ArqRedis
from dishka import FromComponent, Provider, Scope, provide
from httpx import AsyncClient

from parser.infrastructure.clients.arq_tasks import ARQTasksClient
from parser.infrastructure.clients.httpx_schedule_api import HTTPXScheduleAPIClient
from parser.infrastructure.clients.schedule_api import ScheduleAPIClient
from parser.infrastructure.clients.tasks import TasksClient
from parser.infrastructure.repositories.cache import CacheRepository

logger = logging.getLogger(__name__)


class ClientsProvider(Provider):
    scope = Scope.REQUEST

    @provide(scope=Scope.APP)
    def httpx_async_client(self) -> AsyncClient:
        logger.debug(
            "Creating AsyncClient with base_url '%s'",
            "https://vgtk.by/schedule/lessons/",
        )
        return AsyncClient(base_url="https://vgtk.by/schedule/lessons/")

    @provide
    def schedule_api_client(
        self,
        httpx_client: AsyncClient,
        cache_repo: CacheRepository,
    ) -> ScheduleAPIClient:
        logger.debug("Creating HTTPXScheduleAPIClient")
        return HTTPXScheduleAPIClient(
            httpx_client=httpx_client,
            cache_repo=cache_repo,
        )

    @provide
    def tasks_client(
        self,
        redis_client: Annotated[ArqRedis, FromComponent("redis_arq")],
    ) -> TasksClient:
        return ARQTasksClient(redis_client=redis_client)
