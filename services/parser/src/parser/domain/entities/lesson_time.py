import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class LessonTime:
    start: datetime.time
    end: datetime.time

    def __hash__(self) -> int:
        return hash((self.start, self.end))

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, LessonTime):
            return NotImplemented

        return (self.start, self.end) == (value.start, value.end)
