import random

from parser.domain.entities.cabinet import Cabinet

# ====================== [ВАЛИДНЫЕ ЗНАЧЕНИЯ] ======================
VALID_CABINET_NUMBERS = [
    ("11", "11"),
    ("12к", "12К"),
    ("31", "31"),
    ("315", "315"),
    ("42к", "42К"),
    ("52к", "52К"),
    ("сз3", "СЗ3"),
    ("упм1л6", "упм. 1, л. 6"),
]

# ====================== [СУЩНОСТИ] ======================
_CABINET_INDEX, _CABINET_NUMBER = random.choice(VALID_CABINET_NUMBERS)
CABINET_ITEM = Cabinet(title=_CABINET_NUMBER)
CABINET_ITEM_NOT_SAVED = Cabinet(title="22к")
CABINET_ITEM_NOT_USED = Cabinet(title="33к")
USED_CABINET_ITEMS = [Cabinet(title=number) for _, number in VALID_CABINET_NUMBERS]
ALL_CABINET_ITEMS = sorted(
    [*USED_CABINET_ITEMS, CABINET_ITEM_NOT_USED], key=lambda x: x.index
)
