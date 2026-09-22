import datetime
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class LessonTimeRange:
    start: datetime.time
    end: datetime.time
    time_type: Literal["default", "reduce"] | None = None

    def __str__(self) -> str:
        return f"{self.start.strftime('%H:%M')} - {self.end.strftime('%H:%M')}"

    def __post_init__(self):
        if self.end < self.start:
            raise ValueError(
                "The end time of a pair cannot be earlier than its start time"
            )

        _today = datetime.datetime.now(datetime.UTC).today()

        _start_dt = datetime.datetime.combine(datetime.date.today(), self.start)
        _end_dt = datetime.datetime.combine(datetime.date.today(), self.end)

        if (_end_dt - _start_dt).total_seconds() == 60 * 45:
            object.__setattr__(self, "time_type", "default")
        elif (_end_dt - _start_dt).total_seconds() < 60 * 45:
            object.__setattr__(self, "time_type", "reduce")
        else:
            raise ValueError(
                "The difference between start and end cannot be more than 45 minutes"
            )

    def __hash__(self) -> int:
        return hash((self.start, self.end))

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, LessonTimeRange):
            return NotImplemented

        return (self.start, self.end) == (value.start, value.end)
