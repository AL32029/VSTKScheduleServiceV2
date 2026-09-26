import asyncio
import datetime
import itertools
import logging

from dishka import Scope

from parser.infrastructure.clients.schedule_api import ScheduleAPIClient
from parser.infrastructure.clients.tasks import TasksClient
from parser.infrastructure.dishka.container import generate_dishka_container
from parser.infrastructure.repositories.schedule import ScheduleRepository

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting the schedule parsing application")

    _container = generate_dishka_container()

    async with _container(scope=Scope.REQUEST) as container:
        logger.debug("Request-scoped container has been created")

        schedule_api = await container.get(ScheduleAPIClient)
        logger.debug("Resolved ScheduleAPIClient")

        _schedule_repo = await container.get(ScheduleRepository)
        logger.debug("Resolved ScheduleRepository")

        _tasks_client = await container.get(TasksClient)
        logger.debug("Resolved TasksClient")

        for _schedule_type in "today", "tomorrow":
            logger.info("Processing the schedule for %s", _schedule_type)

            _schedule = await schedule_api.fetch_schedule_by_url(_schedule_type)

            if _schedule is None:
                logger.info(
                    "No schedule data was returned for %s, skipping", _schedule_type
                )
                continue

            logger.info(
                "Actualizing groups for %s (%d groups)",
                _schedule_type,
                len(_schedule.get("groups")),
            )
            _group_changes = await _schedule_repo.actualize_groups(
                _schedule.get("groups")
            )

            logger.info(
                "Actualizing cabinets for %s (%d cabinets)",
                _schedule_type,
                len(_schedule.get("cabinets")),
            )
            _cabinet_changes = await _schedule_repo.actualize_cabinets(
                _schedule.get("cabinets")
            )

            logger.info(
                "Actualizing lesson titles for %s (%d titles)",
                _schedule_type,
                len(_schedule.get("lesson_titles")),
            )
            _lesson_title_changes = await _schedule_repo.actualize_lesson_titles(
                _schedule.get("lesson_titles")
            )

            logger.info(
                "Actualizing lesson time ranges for %s (%d ranges)",
                _schedule_type,
                len(_schedule.get("time_ranges")),
            )
            _lesson_time_changes = await _schedule_repo.actualize_lesson_times(
                _schedule.get("time_ranges")
            )

            _day_schedule_from, _day_schedule_to = None, None

            _schedule_dates: datetime.date | tuple[datetime.date, datetime.date] = (
                _schedule.get("schedule_date_range")
            )

            if isinstance(_schedule_dates, datetime.date):
                _day_schedule_from = _schedule_dates
            else:
                _day_schedule_from, _day_schedule_to = (
                    _schedule_dates[0],
                    _schedule_dates[1],
                )

            logger.info(
                "Actualizing day schedules for %s (from=%s, to=%s, %d day schedules)",
                _schedule_type,
                _day_schedule_from,
                _day_schedule_to,
                len(_schedule.get("day_schedules")),
            )
            _day_schedules_changes = await _schedule_repo.actualize_day_schedules(
                schedules_from=_day_schedule_from,
                schedules_to=_day_schedule_to,
                day_schedules=[
                    day_schedule
                    for _, day_schedule in _schedule.get("day_schedules").items()
                ],
            )

            _groups_to_clear_cache = list(
                itertools.chain.from_iterable(_group_changes.values())
            )

            if _groups_to_clear_cache:
                logger.info(
                    "Enqueuing the group cache clearing task for %s",
                    _schedule_type,
                )
                await _tasks_client.enqueue_clear_group_cache_task(
                    _groups_to_clear_cache
                )

            _cabinets_to_clear_cache = list(
                itertools.chain.from_iterable(_cabinet_changes.values())
            )

            if _cabinets_to_clear_cache:
                logger.info(
                    "Enqueuing the cabinet cache clearing task for %s",
                    _schedule_type,
                )
                await _tasks_client.enqueue_clear_cabinet_cache_task(
                    _cabinets_to_clear_cache
                )

            _groups_schedule_to_clear_cache = list(
                itertools.chain.from_iterable(
                    _day_schedules_changes.get("groups").values()
                )
            )

            if _groups_schedule_to_clear_cache:
                logger.info(
                    "Enqueuing the group schedule cache clearing task for %s",
                    _schedule_type,
                )
                await _tasks_client.enqueue_clear_group_schedule_cache_task(
                    _groups_schedule_to_clear_cache, _schedule_type
                )

            _cabinets_schedule_to_clear_cache = list(
                itertools.chain.from_iterable(
                    _day_schedules_changes.get("cabinets").values()
                )
            )

            if _cabinets_schedule_to_clear_cache:
                logger.info(
                    "Enqueuing the cabinet schedule cache clearing task for %s",
                    _schedule_type,
                )
                await _tasks_client.enqueue_clear_cabinet_schedule_cache_task(
                    _cabinets_schedule_to_clear_cache, _schedule_type
                )

            _groups_schedule_to_notify = _day_schedules_changes.get("groups")

            if list(itertools.chain.from_iterable(_groups_schedule_to_notify.values())):
                logger.info(
                    "Enqueuing the group schedule notification task for %s",
                    _schedule_type,
                )
                await _tasks_client.enqueue_send_group_schedule_notification_task(
                    _groups_schedule_to_notify,
                    _schedule_type,
                    _schedule_dates,
                )

            _cabinets_schedule_to_notify = _day_schedules_changes.get("cabinets")

            if list(
                itertools.chain.from_iterable(_cabinets_schedule_to_notify.values())
            ):
                logger.info(
                    "Enqueuing the cabinet schedule notification task for %s",
                    _schedule_type,
                )
                await _tasks_client.enqueue_send_cabinet_schedule_notification_task(
                    _cabinets_schedule_to_notify,
                    _schedule_type,
                    _schedule_dates,
                )

    logger.info("The schedule parsing application has finished")


asyncio.run(main())
