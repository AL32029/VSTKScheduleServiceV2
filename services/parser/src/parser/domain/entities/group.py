from dataclasses import dataclass

from .base import ScheduleItem


@dataclass(frozen=True)
class Group(ScheduleItem):
    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, Group):
            return NotImplemented

        return super().__eq__(value)
