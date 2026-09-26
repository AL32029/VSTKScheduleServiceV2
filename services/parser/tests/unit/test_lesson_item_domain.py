import pytest

from parser.domain.entities.cabinet import Cabinet
from parser.domain.entities.day_schedule import LessonItem
from parser.domain.entities.lesson_time_range import LessonTimeRange
from parser.domain.entities.lesson_title import LessonTitle
from tests.fixtures.lesson_items import LESSON_ITEMS, LESSONS


@pytest.mark.parametrize(("start", "end", "titles", "cabinets"), LESSONS)
def test_lesson_item_creation_success(start, end, titles, cabinets):
    _item = LessonItem(
        time_range=LessonTimeRange(start, end),
        name=[LessonTitle(title=title) for title in titles],
        cabinets=[Cabinet(title=title) for title in cabinets],
    )

    assert _item is not None

    assert isinstance(_item.time_range, LessonTimeRange)

    assert isinstance(_item.name, tuple)
    assert all(isinstance(title, LessonTitle) for title in _item.name)

    assert isinstance(_item.cabinets, tuple)
    assert all(isinstance(cabinet, Cabinet) for cabinet in _item.cabinets)


@pytest.mark.parametrize(("start", "end", "titles", "cabinets"), LESSONS)
def test_lesson_items_equality_success(start, end, titles, cabinets):
    _first_item = LessonItem(
        time_range=LessonTimeRange(start, end),
        name=[LessonTitle(title=title) for title in titles],
        cabinets=[Cabinet(title=title) for title in cabinets],
    )
    _second_item = LessonItem(
        time_range=LessonTimeRange(start, end),
        name=[LessonTitle(title=title) for title in titles],
        cabinets=[Cabinet(title=title) for title in cabinets],
    )

    assert _first_item == _second_item


@pytest.mark.parametrize(("start", "end", "titles", "cabinets"), LESSONS)
def test_lesson_items_hash_equality_success(start, end, titles, cabinets):
    _first_item = LessonItem(
        time_range=LessonTimeRange(start, end),
        name=[LessonTitle(title=title) for title in titles],
        cabinets=[Cabinet(title=title) for title in cabinets],
    )
    _second_item = LessonItem(
        time_range=LessonTimeRange(start, end),
        name=[LessonTitle(title=title) for title in titles],
        cabinets=[Cabinet(title=title) for title in cabinets],
    )

    assert hash(_first_item) == hash(_second_item)


@pytest.mark.parametrize("lesson_item", LESSON_ITEMS)
def test_lesson_item_equality_with_other_type_returns_not_implemented(lesson_item):
    assert lesson_item.__eq__(lesson_item.time_range) is NotImplemented
