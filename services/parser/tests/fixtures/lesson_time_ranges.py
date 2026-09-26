import datetime
from typing import Literal

from parser.domain.entities.lesson_time_range import LessonTimeRange

LESSON_TIME_RANGES: list[
    tuple[
        datetime.time,
        datetime.time,
        Literal["standard", "reduce"],
    ]
] = [
    (datetime.time(9, 0), datetime.time(9, 45), "standard"),
    (datetime.time(9, 55), datetime.time(10, 40), "standard"),
    (datetime.time(10, 50), datetime.time(11, 35), "standard"),
    (datetime.time(11, 45), datetime.time(12, 30), "standard"),
    (datetime.time(12, 40), datetime.time(13, 25), "standard"),
    (datetime.time(9, 0), datetime.time(9, 30), "reduce"),
    (datetime.time(9, 35), datetime.time(10, 5), "reduce"),
    (datetime.time(10, 10), datetime.time(10, 40), "reduce"),
    (datetime.time(10, 50), datetime.time(11, 20), "reduce"),
    (datetime.time(11, 25), datetime.time(11, 55), "reduce"),
]
LESSON_TIME_RANGE_ITEMS = [
    LessonTimeRange(start=start, end=end)
    for start, end, time_type in LESSON_TIME_RANGES
]
