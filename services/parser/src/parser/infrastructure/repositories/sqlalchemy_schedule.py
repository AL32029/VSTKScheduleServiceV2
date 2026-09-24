import datetime
import logging
from collections.abc import Iterable
from typing import Literal, cast

from sqlalchemy import bindparam, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from parser.domain.entities.cabinet import Cabinet
from parser.domain.entities.day_schedule import DayScheduleItem
from parser.domain.entities.group import Group
from parser.domain.entities.lesson_time_range import LessonTimeRange
from parser.domain.entities.lesson_title import LessonTitle
from parser.infrastructure.repositories.schedule import ScheduleRepository

logger = logging.getLogger(__name__)


class SQLAlchemyScheduleRepository(ScheduleRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_all_groups(self) -> list[Group]:
        logger.debug("Fetching all groups from the database")

        stmt = select(func.get_all_groups(type_=JSONB))

        result: list[dict] = (
            await self._session.execute(stmt)
        ).scalar_one_or_none() or []

        groups = [
            Group(
                title=cast(str, group.get("number")),
                is_active=cast(bool, group.get("is_active")),
            )
            for group in result
        ]

        logger.debug("Fetched %d groups from the database", len(groups))
        return groups

    async def get_all_cabinets(self) -> list[Cabinet]:
        logger.debug("Fetching all cabinets from the database")

        stmt = select(func.get_all_cabinets(type_=JSONB))

        result: list[dict] = (
            await self._session.execute(stmt)
        ).scalar_one_or_none() or []

        cabinets = [Cabinet(title=cast(str, group.get("number"))) for group in result]

        logger.debug("Fetched %d cabinets from the database", len(cabinets))
        return cabinets

    async def actualize_groups(
        self,
        groups: Iterable[Group],
    ) -> dict[
        Literal[
            "deactivated",
            "activated",
            "inserted",
        ],
        list[dict],
    ]:
        groups = list(groups)

        logger.debug("Actualizing %d groups in the database", len(groups))

        stmt = select(
            func.check_group_updates(
                bindparam(
                    "groups",
                    value=[{"index": g.index, "number": g.title} for g in groups],
                    type_=JSONB,
                )
            )
        )

        result: dict[
            Literal[
                "deactivated",
                "activated",
                "inserted",
            ],
            list[dict],
        ] = (await self._session.execute(stmt)).scalar_one()

        logger.debug(
            "Groups actualization result: deactivated=%d, activated=%d, inserted=%d",
            len(result.get("deactivated", [])),
            len(result.get("activated", [])),
            len(result.get("inserted", [])),
        )

        return result

    async def actualize_cabinets(
        self,
        cabinets: Iterable[Cabinet],
    ) -> dict[Literal["inserted"], list[dict]]:
        cabinets = list(cabinets)

        logger.debug("Actualizing %d cabinets in the database", len(cabinets))

        stmt = select(
            func.check_cabinet_updates(
                bindparam(
                    "cabinets",
                    value=[{"index": c.index, "number": c.title} for c in cabinets],
                    type_=JSONB,
                )
            )
        )

        result: dict[Literal["inserted"], list[dict]] = (
            await self._session.execute(stmt)
        ).scalar_one()

        logger.debug(
            "Cabinets actualization result: inserted=%d",
            len(result.get("inserted", [])),
        )

        return result

    async def actualize_lesson_titles(
        self,
        lesson_titles: Iterable[LessonTitle],
    ) -> dict[Literal["inserted"], list[dict]]:
        lesson_titles = list(lesson_titles)

        logger.debug("Actualizing %d lesson titles in the database", len(lesson_titles))

        stmt = select(
            func.check_lesson_title_updates(
                bindparam(
                    "titles",
                    value=[
                        {
                            "index": t.index,
                            "original_title": t.title,
                        }
                        for t in lesson_titles
                    ],
                    type_=JSONB,
                )
            )
        )

        result: dict[Literal["inserted"], list[dict]] = (
            await self._session.execute(stmt)
        ).scalar_one()

        logger.debug(
            "Lesson titles actualization result: inserted=%d",
            len(result.get("inserted", [])),
        )

        return result

    async def actualize_lesson_times(
        self,
        lesson_times: Iterable[LessonTimeRange],
    ) -> dict[Literal["inserted", "closed", "unchanged"], list[dict]]:
        lesson_times = list(lesson_times)

        logger.debug(
            "Actualizing %d lesson time ranges in the database", len(lesson_times)
        )

        stmt = select(
            func.check_lesson_time_updates(
                bindparam(
                    "times",
                    value=[
                        {
                            "time_type": t.time_type,
                            "lesson_start": t.start.strftime("%H:%M"),
                            "lesson_end": t.end.strftime("%H:%M"),
                        }
                        for t in lesson_times
                    ],
                    type_=JSONB,
                )
            )
        )

        result: dict[Literal["inserted", "closed", "unchanged"], list[dict]] = (
            await self._session.execute(stmt)
        ).scalar_one()

        logger.debug(
            "Lesson times actualization result: inserted=%d, closed=%d, unchanged=%d",
            len(result.get("inserted", [])),
            len(result.get("closed", [])),
            len(result.get("unchanged", [])),
        )

        return result

    async def actualize_day_schedules(
        self,
        schedules_from: datetime.date,
        day_schedules: Iterable[DayScheduleItem],
        schedules_to: datetime.date | None = None,
    ) -> dict[
        Literal["groups", "cabinets"],
        dict[Literal["published", "modified", "deleted"], list[dict]],
    ]:
        day_schedules = list(day_schedules)

        logger.debug(
            "Actualizing day schedules from %s to %s for %d groups",
            schedules_from,
            schedules_to or schedules_from,
            len(day_schedules),
        )

        lessons_value = [
            {
                "group_index": d_l.group.index,
                "time_range": {
                    "start": lesson.time_range.start.strftime("%H:%M"),
                    "end": lesson.time_range.end.strftime("%H:%M"),
                },
                "titles": [l_t.index for l_t in lesson.name],
                "cabinets": [l_c.index for l_c in lesson.cabinets],
            }
            for d_l in day_schedules
            if d_l.lessons
            for lesson in d_l.lessons
        ]

        logger.debug("Prepared %d lesson entries for actualization", len(lessons_value))

        stmt = select(
            func.check_lesson_updates(
                schedules_from,
                schedules_to or schedules_from,
                bindparam(
                    "lessons",
                    value=lessons_value,
                    type_=JSONB,
                ),
            )
        )

        result: dict[
            Literal["groups", "cabinets"],
            dict[Literal["published", "modified", "deleted"], list[dict]],
        ] = (await self._session.execute(stmt)).scalar_one()

        groups_result = result.get("groups", {})
        cabinets_result = result.get("cabinets", {})

        logger.debug(
            "Day schedules actualization result for groups: "
            "published=%d, modified=%d, deleted=%d",
            len(groups_result.get("published", [])),
            len(groups_result.get("modified", [])),
            len(groups_result.get("deleted", [])),
        )
        logger.debug(
            "Day schedules actualization result for cabinets: "
            "published=%d, modified=%d, deleted=%d",
            len(cabinets_result.get("published", [])),
            len(cabinets_result.get("modified", [])),
            len(cabinets_result.get("deleted", [])),
        )

        return result
