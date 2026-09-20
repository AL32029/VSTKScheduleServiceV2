from dataclasses import dataclass


@dataclass(frozen=True)
class LessonTitle:
    index: str
    title: str

    def __hash__(self) -> int:
        return hash((self.index, self.title))

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, LessonTitle):
            return NotImplemented

        return (self.index, self.title) == (value.index, value.title)
