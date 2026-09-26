import random

from parser.domain.entities.group import Group, GroupParser

# ====================== [ВАЛИДНЫЕ ЗНАЧЕНИЯ] ======================
VALID_GROUP_NUMBERS = [("жби21", "ЖБИ-21"), ("ос21", "ОС-21"), ("пэс215", "ПЭС-215")]

# ====================== [СУЩНОСТИ] ======================
_GROUP_INDEX, _GROUP_NUMBER = random.choice(VALID_GROUP_NUMBERS)
GROUP_ITEM = Group(title=_GROUP_NUMBER)
GROUP_ITEM_NOT_SAVED = Group(title="ЖБИ-11")
GROUP_ITEMS = [Group(title=number) for _, number in VALID_GROUP_NUMBERS]
GROUP_PARSER_ITEMS = [
    GroupParser(title=number, pos_x=0, pos_y=0)
    for _, number in VALID_GROUP_NUMBERS
]
