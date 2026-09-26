from dataclasses import dataclass

from .base import ScheduleItem


@dataclass(frozen=True)
class Cabinet(ScheduleItem):
    def __hash__(self) -> int:
        return super().__hash__()

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, Cabinet):
            return NotImplemented

        return super().__eq__(value)
