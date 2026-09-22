from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from parser.domain.entities.cabinet import Cabinet
    from parser.domain.entities.group import Group
    from parser.domain.entities.lesson_time_range import LessonTimeRange
    from parser.domain.entities.lesson_title import LessonTitle


@dataclass(frozen=True)
class LessonItem:
    time_range: LessonTimeRange
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
    group: Group
    lessons: Iterable[LessonItem]

    def __post_init__(self):
        if not isinstance(self.lessons, tuple):
            object.__setattr__(self, "lessons", tuple(self.lessons))

    def __hash__(self) -> int:
        return hash((self.group, self.lessons))

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, DayScheduleItem):
            return NotImplemented

        return (self.group, self.lessons) == (value.group, value.lessons)
