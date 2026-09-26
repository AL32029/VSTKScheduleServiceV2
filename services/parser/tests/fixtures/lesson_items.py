import datetime

from parser.domain.entities.cabinet import Cabinet
from parser.domain.entities.day_schedule import LessonItem
from parser.domain.entities.lesson_time_range import LessonTimeRange
from parser.domain.entities.lesson_title import LessonTitle

LESSONS = [
    (
        datetime.time(9, 0),
        datetime.time(9, 45),
        ("Математика",),
        ("42к",),
    ),
    (
        datetime.time(9, 55),
        datetime.time(10, 40),
        ("Допризывная подготовка",),
        ("52к",),
    ),
    (
        datetime.time(10, 50),
        datetime.time(11, 35),
        ("Ин. яз.",),
        ("21", "409"),
    ),
    (
        datetime.time(11, 45),
        datetime.time(12, 30),
        ("Тех. мех.",),
        ("315",),
    ),
    (
        datetime.time(12, 40),
        datetime.time(13, 25),
        ("ТП ЖБИ",),
        ("404",),
    ),
    (
        datetime.time(13, 35),
        datetime.time(14, 20),
        ("Основы бетоноведения",),
        ("404",),
    ),
    (
        datetime.time(14, 30),
        datetime.time(15, 15),
        ("Мех. оборудование",),
        ("упм. 1, л. 6",),
    ),
]

LESSON_ITEMS = [
    LessonItem(
        time_range=LessonTimeRange(start, end),
        name=[LessonTitle(title=title) for title in titles],
        cabinets=[Cabinet(title=title) for title in cabinets],
    )
    for start, end, titles, cabinets in LESSONS
]
