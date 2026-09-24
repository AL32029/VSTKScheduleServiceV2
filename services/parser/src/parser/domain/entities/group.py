import re
from dataclasses import dataclass
from functools import cached_property

from .base import ScheduleItem

_GROUP_NUMBER_PATTERN = re.compile(r"([А-Я]{1,3}-[0-9]{2,3})")


@dataclass(frozen=True)
class Group(ScheduleItem):
    is_active: bool

    def __post_init__(self):
        if not _GROUP_NUMBER_PATTERN.match(self.title):
            raise ValueError("Invalid group number")

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, Group):
            return NotImplemented

        return super().__eq__(value)


@dataclass(frozen=True)
class GroupParser(Group):
    pos_x: int
    pos_y: int

    @cached_property
    def group(self) -> Group:
        return Group(title=self.title, is_active=self.is_active)

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, GroupParser):
            return NotImplemented

        return super().__eq__(value)
