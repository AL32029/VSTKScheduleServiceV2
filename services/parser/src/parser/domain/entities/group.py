import re
from dataclasses import dataclass
from functools import cached_property

from .base import ScheduleItem

_GROUP_NUMBER_PATTERN = re.compile(r"([А-Я]{1,3}-[0-9]{2,3})")


@dataclass(frozen=True)
class Group(ScheduleItem):
    def __post_init__(self):
        if not self.title.strip():
            raise ValueError("The title field cannot be empty")

        if not _GROUP_NUMBER_PATTERN.match(self.title):
            raise ValueError("Invalid group number")

        super().__post_init__()

    def __hash__(self) -> int:
        return super().__hash__()

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
        return Group(title=self.title)

    def __post_init__(self):
        if self.pos_x < 0:
            raise ValueError("The pos_x parameter cannot take a negative value")

        if self.pos_y < 0:
            raise ValueError("The pos_y parameter cannot take a negative value")

        super().__post_init__()

    def __hash__(self) -> int:
        return super().__hash__()

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, GroupParser):
            return NotImplemented

        return super().__eq__(value)
