import pytest

from parser.domain.entities.lesson_title import LessonTitle
from tests.fixtures.lesson_titles import LESSON_TITLE_ITEMS, LESSON_TITLES


@pytest.mark.parametrize(("index", "title"), LESSON_TITLES)
def test_lesson_title_creation_success(index, title):
    _item = LessonTitle(title=title)

    assert _item is not None
    assert _item.title == title
    assert _item.index == index


@pytest.mark.parametrize("lesson_title", LESSON_TITLE_ITEMS)
def test_lesson_title_str_returns_title(lesson_title):
    assert str(lesson_title) == lesson_title.title


@pytest.mark.parametrize(("index", "title"), LESSON_TITLES)
def test_lesson_titles_equality_success(index, title):  # noqa: ARG001
    _first_item = LessonTitle(title=title)
    _second_item = LessonTitle(title=title)

    assert _first_item == _second_item


@pytest.mark.parametrize(("index", "title"), LESSON_TITLES)
def test_lesson_titles_hash_equality_success(index, title):  # noqa: ARG001
    _first_item = LessonTitle(title=title)
    _second_item = LessonTitle(title=title)

    assert hash(_first_item) == hash(_second_item)


def test_lesson_title_creation_with_empty_title_raises_error():
    with pytest.raises(ValueError, match="The title field cannot be empty"):
        LessonTitle(title="")


@pytest.mark.parametrize("lesson_title", LESSON_TITLE_ITEMS)
def test_lesson_title_equality_with_other_type_returns_not_implemented(lesson_title):
    assert lesson_title.__eq__(lesson_title.title) is NotImplemented
