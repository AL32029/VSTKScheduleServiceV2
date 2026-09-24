import datetime
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


class SQLAlchemyScheduleRepository(ScheduleRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_all_groups(self) -> list[Group]:
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

        return groups

    async def get_all_cabinets(self) -> list[Cabinet]:
        stmt = select(func.get_all_cabinets(type_=JSONB))

        result: list[dict] = (
            await self._session.execute(stmt)
        ).scalar_one_or_none() or []

        cabinets = [Cabinet(title=cast(str, group.get("number"))) for group in result]

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

        return result

    async def actualize_cabinets(
        self,
        cabinets: Iterable[Cabinet],
    ) -> dict[Literal["inserted"], list[dict]]:
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

        return result

    async def actualize_lesson_titles(
        self,
        lesson_titles: Iterable[LessonTitle],
    ) -> dict[Literal["inserted"], list[dict]]:
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

        return result

    async def actualize_lesson_times(
        self,
        lesson_times: Iterable[LessonTimeRange],
    ) -> dict[Literal["inserted", "closed", "unchanged"], list[dict]]:
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
        stmt = select(
            func.check_lesson_updates(
                schedules_from,
                schedules_to or schedules_from,
                bindparam(
                    "lessons",
                    value=[
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
                    ],
                    type_=JSONB,
                ),
            )
        )

        result: dict[
            Literal["groups", "cabinets"],
            dict[Literal["published", "modified", "deleted"], list[dict]],
        ] = (await self._session.execute(stmt)).scalar_one()

        return result
