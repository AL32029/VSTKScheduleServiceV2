from __future__ import annotations

import datetime
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cabinet import Cabinet
    from .lesson_time import LessonTime
    from .lesson_title import LessonTitle


@dataclass(frozen=True)
class ScheduleItem:
    index: str
    number: str

    def __hash__(self) -> int:
        return hash(self.index)

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, ScheduleItem):
            return NotImplemented

        return self.index == value.index


@dataclass(frozen=True)
class LessonItem:
    time_range: LessonTime
    name: LessonTitle
    cabinets: Iterable[Cabinet]

    def __post_init__(self):
        if not isinstance(self.cabinets, tuple):
            object.__setattr__(self, "cabinets", tuple(self.cabinets))

    def __hash__(self) -> int:
        return hash((self.time_range, self.name, self.cabinets))

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, LessonItem):
            return NotImplemented

        return (self.time_range, self.name, self.cabinets) == (
            value.time_range,
            value.name,
            value.cabinets,
        )


@dataclass(frozen=True)
class DayScheduleItem:
    schedule_at: datetime.date
    schedule_item: ScheduleItem
    lessons: tuple[LessonItem]

    def __post_init__(self):
        if not isinstance(self.lessons, tuple):
            object.__setattr__(self, "lessons", tuple(self.lessons))

    def __hash__(self) -> int:
        return hash((self.schedule_at, self.schedule_item, self.lessons))

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, DayScheduleItem):
            return NotImplemented

        return (self.schedule_at, self.schedule_item, self.lessons) == (
            value.schedule_at,
            value.schedule_item,
            value.lessons,
        )
