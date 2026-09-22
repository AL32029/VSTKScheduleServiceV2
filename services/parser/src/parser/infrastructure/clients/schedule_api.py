from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from parser.domain.entities.day_schedule import DayScheduleItem
    from parser.domain.entities.group import Group
    from parser.domain.entities.lesson_time_range import LessonTimeRange


class ScheduleAPIClient(ABC):
    @abstractmethod
    async def fetch_schedule_by_url(
        self,
        schedule_at: Literal["today", "tomorrow"],
    ) -> (
        dict[
            str,
            str
            | date
            | tuple[date, date]
            | tuple[LessonTimeRange, ...]
            | list[Group]
            | dict[Group, DayScheduleItem],
        ]
        | None
    ):
        raise NotImplementedError
