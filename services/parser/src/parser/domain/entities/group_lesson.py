from dataclasses import dataclass

from .base import LessonItem


@dataclass(frozen=True)
class GroupLesson(LessonItem):
    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, GroupLesson):
            return NotImplemented

        return super().__eq__(value)
