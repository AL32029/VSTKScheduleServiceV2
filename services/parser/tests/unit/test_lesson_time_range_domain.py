import datetime

import pytest

from parser.domain.entities.lesson_time_range import LessonTimeRange
from tests.fixtures.lesson_time_ranges import (
    LESSON_TIME_RANGE_ITEMS,
    LESSON_TIME_RANGES,
)


@pytest.mark.parametrize(("start", "end", "time_type"), LESSON_TIME_RANGES)
def test_lesson_time_range_creation_success(start, end, time_type):
    _item = LessonTimeRange(start, end)

    assert _item is not None
    assert _item.start == start
    assert _item.end == end
    assert _item.end >= _item.start
    assert _item.time_type == time_type


@pytest.mark.parametrize(("start", "end", "time_type"), LESSON_TIME_RANGES)
def test_lesson_time_range_creation_with_end_before_start_raises_error(
    start,
    end,
    time_type,  # noqa: ARG001
):
    with pytest.raises(
        ValueError, match="The end time of a pair cannot be earlier than its start time"
    ):
        LessonTimeRange(end, start)


def test_lesson_time_range_creation_with_duration_over_45_minutes_raises_error():
    with pytest.raises(
        ValueError,
        match="The difference between start and end cannot be more than 45 minutes",
    ):
        LessonTimeRange(datetime.time(9, 0), datetime.time(17, 5))


@pytest.mark.parametrize(("start", "end", "time_type"), LESSON_TIME_RANGES)
def test_lesson_time_ranges_equality_success(start, end, time_type):  # noqa: ARG001
    _first_item = LessonTimeRange(start, end)
    _second_item = LessonTimeRange(start, end)

    assert _first_item == _second_item


@pytest.mark.parametrize("time_range", LESSON_TIME_RANGE_ITEMS)
def test_group_parser_equality_with_other_type_returns_not_implemented(time_range):
    assert time_range.__eq__(time_range.start) is NotImplemented


@pytest.mark.parametrize(("start", "end", "time_type"), LESSON_TIME_RANGES)
def test_lesson_time_ranges_hash_equality_success(start, end, time_type):  # noqa: ARG001
    _first_item = LessonTimeRange(start, end)
    _second_item = LessonTimeRange(start, end)

    assert hash(_first_item) == hash(_second_item)
