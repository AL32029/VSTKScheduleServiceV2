from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from parser.domain.entities.cabinet import Cabinet
    from parser.domain.entities.day_schedule import DayScheduleItem
    from parser.domain.entities.group import Group
    from parser.domain.entities.lesson_time_range import LessonTimeRange
    from parser.domain.entities.lesson_title import LessonTitle


class ScheduleRepository(ABC):
    @abstractmethod
    async def get_all_groups(self) -> list[Group]:
        raise NotImplementedError

    @abstractmethod
    async def get_all_cabinets(self) -> list[Cabinet]:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    async def actualize_cabinets(
        self,
        cabinets: Iterable[Cabinet],
    ) -> dict[Literal["inserted"], list[dict]]:
        raise NotImplementedError

    @abstractmethod
    async def actualize_lesson_titles(
        self,
        lesson_titles: Iterable[LessonTitle],
    ) -> dict[Literal["inserted"], list[dict]]:
        raise NotImplementedError

    @abstractmethod
    async def actualize_lesson_times(
        self,
        lesson_times: Iterable[LessonTimeRange],
    ) -> dict[Literal["inserted", "closed", "unchanged"], list[dict]]:
        raise NotImplementedError

    @abstractmethod
    async def actualize_day_schedules(
        self,
        schedules_from: datetime.date,
        day_schedules: Iterable[DayScheduleItem],
        schedules_to: datetime.date | None = None,
    ) -> dict[
        Literal["groups", "cabinets"],
        dict[
            Literal["published", "modified", "deleted"],
            list[dict[Literal["index", "number"], str]],
        ],
    ]:
        raise NotImplementedError
