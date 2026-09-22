import re
from dataclasses import dataclass
from functools import cached_property

_ITEM_INDEX_RE = re.compile(r"[^а-я0-9]", flags=re.IGNORECASE)


@dataclass(frozen=True)
class ScheduleItem:
    title: str

    def __post_init__(self):
        object.__setattr__(self, "title", self.title.strip())

    @cached_property
    def index(self) -> str:
        return _ITEM_INDEX_RE.sub("", self.title.lower())

    def __str__(self) -> str:
        return self.title

    def __hash__(self) -> int:
        return hash(self.index)

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, ScheduleItem):
            return NotImplemented

        return self.index == value.index
