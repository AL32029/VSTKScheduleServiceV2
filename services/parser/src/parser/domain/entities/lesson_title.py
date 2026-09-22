from dataclasses import dataclass

from parser.domain.entities.base import ScheduleItem


@dataclass(frozen=True)
class LessonTitle(ScheduleItem):
    def __post_init__(self):
        object.__setattr__(self, "title", " ".join(self.title.split()))

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, LessonTitle):
            return NotImplemented

        return super().__eq__(value)
