from parser.domain.entities.lesson_title import LessonTitle

LESSON_TITLES = [
    ("отсм", "ОТСМ"),
    ("мехоборудование", "Мех. оборудование"),
    ("техмех", "Тех. мех."),
    ("оаиап", "ОАиАП"),
    ("ккп", "ККП"),
    ("ибвконтви", "ИБ в конт. ВИ"),
    ("допризывнаяподготовка", "Допризывная подготовка"),
]
LESSON_TITLE_ITEMS = [LessonTitle(title=title) for _, title in LESSON_TITLES]
