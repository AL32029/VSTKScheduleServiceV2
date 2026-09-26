import pytest

from parser.domain.entities.cabinet import Cabinet
from tests.fixtures.cabinets import USED_CABINET_ITEMS, VALID_CABINET_NUMBERS


@pytest.mark.parametrize(("index", "title"), VALID_CABINET_NUMBERS)
def test_cabinet_creation_success(index, title):
    _item = Cabinet(title=title)

    assert _item is not None
    assert _item.title == title
    assert _item.index == index


@pytest.mark.parametrize("cabinet", USED_CABINET_ITEMS)
def test_cabinet_str_returns_title(cabinet):
    assert str(cabinet) == cabinet.title


@pytest.mark.parametrize(("index", "title"), VALID_CABINET_NUMBERS)
def test_cabinets_equality_success(index, title):  # noqa: ARG001
    _first_item = Cabinet(title=title)
    _second_item = Cabinet(title=title)

    assert _first_item == _second_item


@pytest.mark.parametrize(("index", "title"), VALID_CABINET_NUMBERS)
def test_cabinets_hash_equality_success(index, title):  # noqa: ARG001
    _first_item = Cabinet(title=title)
    _second_item = Cabinet(title=title)

    assert hash(_first_item) == hash(_second_item)


def test_cabinet_creation_with_empty_title_raises_error():
    with pytest.raises(ValueError, match="The title field cannot be empty"):
        Cabinet(title="")


@pytest.mark.parametrize("cabinet", USED_CABINET_ITEMS)
def test_cabinet_equality_with_other_type_returns_not_implemented(cabinet):
    assert cabinet.__eq__(cabinet.title) is NotImplemented
