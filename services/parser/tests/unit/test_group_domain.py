import pytest

from parser.domain.entities.group import Group
from tests.fixtures.groups import GROUP_ITEMS, VALID_GROUP_NUMBERS


@pytest.mark.parametrize(("index", "title"), VALID_GROUP_NUMBERS)
def test_group_creation_success(index, title):
    _item = Group(title=title)

    assert _item is not None
    assert _item.title == title
    assert _item.index == index


@pytest.mark.parametrize("group", GROUP_ITEMS)
def test_group_str_returns_title(group):
    assert str(group) == group.title


@pytest.mark.parametrize(("index", "title"), VALID_GROUP_NUMBERS)
def test_groups_equality_success(index, title):  # noqa: ARG001
    _first_item = Group(title=title)
    _second_item = Group(title=title)

    assert _first_item == _second_item


@pytest.mark.parametrize(("index", "title"), VALID_GROUP_NUMBERS)
def test_groups_hash_equality_success(index, title):  # noqa: ARG001
    _first_item = Group(title=title)
    _second_item = Group(title=title)

    assert hash(_first_item) == hash(_second_item)


def test_group_creation_with_empty_title_raises_error():
    with pytest.raises(ValueError, match="The title field cannot be empty"):
        Group(title="")


def test_group_creation_with_invalid_title_format_raises_error():
    with pytest.raises(ValueError, match="Invalid group number"):
        Group(title="invalid_title")


@pytest.mark.parametrize("group", GROUP_ITEMS)
def test_group_equality_with_other_type_returns_not_implemented(group):
    assert group.__eq__(group.title) is NotImplemented
