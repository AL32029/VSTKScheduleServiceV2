import pytest

from parser.domain.entities.group import GroupParser
from tests.fixtures.groups import (
    GROUP_ITEM,
    GROUP_ITEMS,
    GROUP_PARSER_ITEMS,
    VALID_GROUP_NUMBERS,
)


@pytest.mark.parametrize(("index", "title"), VALID_GROUP_NUMBERS)
def test_group_parser_creation_success(index, title):
    _item = GroupParser(title=title, pos_x=0, pos_y=0)

    assert _item is not None
    assert _item.title == title
    assert _item.index == index


@pytest.mark.parametrize("group", GROUP_PARSER_ITEMS)
def test_group_parser_str_returns_title(group):
    assert str(group) == group.title


@pytest.mark.parametrize(("index", "title"), VALID_GROUP_NUMBERS)
def test_groups_equality_success(index, title):  # noqa: ARG001
    _first_item = GroupParser(title=title, pos_x=0, pos_y=0)
    _second_item = GroupParser(title=title, pos_x=0, pos_y=0)

    assert _first_item == _second_item


@pytest.mark.parametrize(("index", "title"), VALID_GROUP_NUMBERS)
def test_groups_hash_equality_success(index, title):  # noqa: ARG001
    _first_item = GroupParser(title=title, pos_x=0, pos_y=0)
    _second_item = GroupParser(title=title, pos_x=0, pos_y=0)

    assert hash(_first_item) == hash(_second_item)


def test_group_parser_creation_with_empty_title_raises_error():
    with pytest.raises(ValueError, match="The title field cannot be empty"):
        GroupParser(title="", pos_x=0, pos_y=0)


def test_group_parser_creation_with_invalid_title_format_raises_error():
    with pytest.raises(ValueError, match="Invalid group number"):
        GroupParser(title="invalid_title", pos_x=0, pos_y=0)


@pytest.mark.parametrize("group", GROUP_PARSER_ITEMS)
def test_group_parser_equality_with_other_type_returns_not_implemented(group):
    assert group.__eq__(group.title) is NotImplemented


def test_group_parser_creation_with_negative_coordinates_raises_error():
    with pytest.raises(
        ValueError, match="The pos_x parameter cannot take a negative value"
    ):
        GroupParser(title=GROUP_ITEM.title, pos_x=-1, pos_y=1)

    with pytest.raises(
        ValueError, match="The pos_y parameter cannot take a negative value"
    ):
        GroupParser(title=GROUP_ITEM.title, pos_x=1, pos_y=-1)


@pytest.mark.parametrize(
    ("group_parser", "group"),
    zip(
        GROUP_PARSER_ITEMS,
        GROUP_ITEMS,
        strict=False,
    ),
)
def test_group_parser_group_property_returns_group_success(group_parser, group):
    assert group_parser.group == group
