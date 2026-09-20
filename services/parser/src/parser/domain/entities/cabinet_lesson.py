from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .base import LessonItem

if TYPE_CHECKING:
    from .group import Group


@dataclass(frozen=True)
class CabinetLesson(LessonItem):
    group: Group

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, CabinetLesson):
            return NotImplemented

        return super().__eq__(value)
