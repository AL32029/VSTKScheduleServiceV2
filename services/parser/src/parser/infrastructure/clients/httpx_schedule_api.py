import asyncio
import datetime
import logging
import re
from collections.abc import Iterable
from datetime import date
from re import Pattern
from typing import Any, ClassVar, Literal

import httpx
import numpy
from bs4 import BeautifulSoup, Tag
from httpx import AsyncClient
from numpy import argwhere, dtype, ndarray, vectorize

from parser.domain.entities.cabinet import Cabinet
from parser.domain.entities.day_schedule import DayScheduleItem, LessonItem
from parser.domain.entities.group import Group, GroupParser
from parser.domain.entities.lesson_time_range import LessonTimeRange
from parser.domain.entities.lesson_title import LessonTitle
from parser.infrastructure.clients.schedule_api import ScheduleAPIClient
from parser.infrastructure.config.system_settings import system_settings

logger = logging.getLogger(__name__)


class HTTPXScheduleAPIClient(ScheduleAPIClient):
    _DATE_WORD_PATTERN: ClassVar[Pattern] = re.compile(
        r"((\d{1,2})\s*+([а-я]+)\s*+(\d{4}))"
    )
    _DATE_NUMBERED_PATTERN: ClassVar[Pattern] = re.compile(
        r"((\d{1,2}).(\d{2}).(\d{4}))"
    )
    _LESSONS_TIME_PATTERN: ClassVar[Pattern] = re.compile(
        r"^(\d{1,2})[.:](\d{1,2})\s*[—\-–−-]"
        r"\s*(\d{1,2})[.:](\d{1,2})$"
    )

    _GROUP_NUMBER_PATTERN: ClassVar[Pattern] = re.compile(r"([А-Я]{1,3}-[0-9]{2,3})")

    _MONTH_TO_NUMBER: ClassVar[dict] = {
        "января": 1,
        "февраля": 2,
        "марта": 3,
        "апреля": 4,
        "мая": 5,
        "июня": 6,
        "июля": 7,
        "августа": 8,
        "сентября": 9,
        "октября": 10,
        "ноября": 11,
        "декабря": 12,
    }

    def __init__(self, client: AsyncClient):
        self._client = client

    async def fetch_schedule_by_url(
        self, schedule_at: Literal["today", "tomorrow"]
    ) -> (
        dict[
            str,
            str
            | date
            | tuple[date, date]
            | tuple[LessonTimeRange, ...]
            | list[Group]
            | list[Cabinet]
            | list[LessonTitle]
            | dict[Group, DayScheduleItem],
        ]
        | None
    ):
        logger.info("Starting schedule parsing for %s", schedule_at)
        _url = (
            f"day-{schedule_at}.php"
            if self._client.base_url
            else f"https://vgtk.by/schedule/lessons/day-{schedule_at}.php"
        )

        logger.info("Fetching HTML for the schedule (%s)", schedule_at)
        _html_content = await self._fetch_html_content(_url)

        if _html_content is None:
            logger.warning(
                "The website did not return HTML for the schedule (%s)",
                schedule_at,
            )
            return None

        logger.info(
            "The website returned HTML for the schedule (%s)",
            schedule_at,
        )

        logger.info("Extracting the schedule table for %s", schedule_at)
        _schedule_table = self._parse_schedule_table(_html_content)

        if _schedule_table is None:
            logger.warning(
                "The HTML for the schedule (%s) does not contain a schedule table",
                schedule_at,
            )
            return None

        logger.info(
            "Successfully retrieved the schedule table for %s",
            schedule_at,
        )

        # TODO: Добавить проверку хэша таблицы в Redis и
        #  прекращение парсинга при совпадении хэша

        logger.info("Converting the schedule table for %s into a matrix", schedule_at)
        _schedule_matrix = self._generate_matrix_from_table(_schedule_table)

        if _schedule_matrix is None or _schedule_matrix.size == 0:
            logger.warning(
                "Failed to convert the schedule table for %s into a matrix",
                schedule_at,
            )
            return None

        logger.info(
            "Successfully converted the schedule table for %s into a matrix",
            schedule_at,
        )

        logger.info(
            "Extracting the schedule date from the schedule matrix for %s", schedule_at
        )

        _schedule_dates = self._extract_dates(_schedule_matrix, schedule_at)

        if not _schedule_dates:
            logger.warning(
                "No date matching the requested schedule type was found for %s",
                schedule_at,
            )
            return None

        logger.info(
            "Successfully extracted the date from the schedule matrix for %s",
            schedule_at,
        )

        logger.info(
            "Extracting time ranges from the schedule matrix for %s", schedule_at
        )

        _time_ranges = self._extract_time_ranges(_schedule_matrix)

        if not _time_ranges:
            logger.warning(
                "No time ranges were found in the schedule matrix for %s", schedule_at
            )
            return None

        logger.info("Successfully extracted time ranges for %s", schedule_at)

        logger.info("Extracting groups from the schedule matrix for %s", schedule_at)

        _groups_parser = self._extract_groups(_schedule_matrix)

        if not _groups_parser:
            logger.warning(
                "No groups were found in the schedule matrix for %s", schedule_at
            )
            return None

        logger.info("Successfully extracted groups for %s", schedule_at)

        logger.info(
            "Extracting day schedules from the schedule matrix for %s", schedule_at
        )

        _day_schedules = self._extract_day_schedules(
            _schedule_matrix, _time_ranges, _groups_parser
        )

        if not _day_schedules:
            logger.warning(
                "No day schedules were extracted from the schedule matrix for %s",
                schedule_at,
            )
            return None

        logger.info("Successfully extracted day schedules for %s", schedule_at)

        logger.info(
            "Extracting cabinets and lesson titles from the day schedules for %s",
            schedule_at,
        )

        _cabinets_return, _lesson_titles_return = self._extract_cabinets_and_titles(
            _day_schedules
        )

        if not _cabinets_return and not _lesson_titles_return:
            logger.warning(
                "No cabinets or lesson titles were extracted from the day "
                "schedules for %s",
                schedule_at,
            )

        logger.info(
            "Successfully extracted cabinets and lesson titles for %s", schedule_at
        )

        return {
            "schedule_at": schedule_at,
            "schedule_date_range": _schedule_dates,
            "time_ranges": _time_ranges,
            "groups": [g.group for g in _groups_parser],
            "cabinets": list(_cabinets_return),
            "lesson_titles": list(_lesson_titles_return),
            "day_schedules": _day_schedules,
        }

    async def _fetch_html_content(self, url: str) -> str | None:
        _attempts_count = 3

        _full_url = url
        if self._client.base_url and not url.startswith(("http://", "https://")):
            _full_url = str(self._client.base_url).rstrip("/") + "/" + url.lstrip("/")

        logger.debug("Fetching HTML content from %s", _full_url)

        for attempt in range(_attempts_count):
            try:
                logger.debug(
                    "Sending GET request to %s (attempt %d/%d)",
                    _full_url,
                    attempt + 1,
                    _attempts_count,
                )
                response = await self._client.get(url)

                if response.is_client_error:
                    logger.debug(
                        "Received a client error from %s (status code: %s)",
                        _full_url,
                        response.status_code,
                    )
                    return None

                response.raise_for_status()

                logger.debug("Successfully fetched HTML content from %s", _full_url)
                return response.text

            except (
                httpx.Timeout,
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.NetworkError,
                httpx.TransportError,
            ) as err:
                logger.debug(
                    "Request to %s failed on attempt %d/%d: %s",
                    _full_url,
                    attempt + 1,
                    _attempts_count,
                    err,
                )
                if attempt < _attempts_count - 1:
                    logger.debug("Retrying request to %s after a delay", _full_url)
                    await asyncio.sleep(2**attempt)
                    continue
                logger.debug(
                    "All attempts to fetch HTML content from %s have failed", _full_url
                )
                raise err
        return None

    @staticmethod
    def _parse_schedule_table(html_content: str) -> Tag | None:
        logger.debug("Parsing the HTML content for the schedule table")
        soup = BeautifulSoup(html_content, "lxml")
        table = soup.find("table", class_="excel")

        if table is None:
            logger.debug("The schedule table was not found in the HTML content")
        else:
            logger.debug("The schedule table was found in the HTML content")

        return table

    @staticmethod
    def _generate_matrix_from_table(
        table: Tag,
    ) -> ndarray[tuple[int, int], dtype[Any]] | None:
        logger.debug("Generating a matrix from the schedule table")
        rows_raw = [tr.find_all("td") for tr in table.find_all("tr")]
        rows_count = len(rows_raw)

        logger.debug("Found %d rows in the schedule table", rows_count)

        if rows_count == 0:
            logger.debug("The schedule table contains no rows")
            return None

        max_cols = 0
        rows = []

        for row in rows_raw:
            row_data = []
            row_cols = 0
            for cell in row:
                colspan = int(cell.get("colspan", "1"))
                rowspan = int(cell.get("rowspan", "1"))
                text = cell.text or ""
                row_data.append((text, rowspan, colspan))
                row_cols += colspan
            rows.append(row_data)
            max_cols = max(max_cols, row_cols)

        logger.debug("The schedule table has a maximum of %d columns", max_cols)

        if max_cols == 0:
            logger.debug("The schedule table contains no columns")
            return None

        matrix = numpy.full((rows_count, max_cols), None, dtype=object)

        for r_idx, row_data in enumerate(rows):
            c_idx = 0
            for text, rowspan, colspan in row_data:
                while c_idx < max_cols and matrix[r_idx][c_idx] is not None:
                    c_idx += 1
                if c_idx + colspan > max_cols or r_idx + rowspan > rows_count:
                    logger.debug(
                        "Skipping cell at row %d, column %d: it "
                        "exceeds the matrix bounds",
                        r_idx,
                        c_idx,
                    )
                    continue
                matrix[r_idx : r_idx + rowspan, c_idx : c_idx + colspan] = text
                c_idx += colspan

        logger.debug(
            "Generated a matrix with shape %s from the schedule table", matrix.shape
        )
        return matrix

    @staticmethod
    def _expand_dates(
        dates: Iterable[datetime.date],
    ) -> datetime.date | list[datetime.date] | None:
        logger.debug("Expanding the date sequence")
        _dates = sorted(dates)

        if not _dates:
            logger.debug("The date sequence is empty")
            return None

        if len(_dates) == 1:
            logger.debug("The date sequence contains a single date: %s", _dates[0])
            return _dates[0]

        if len(_dates) > 2:
            start, end = _dates[0], _dates[-1]
            expanded = [
                start + datetime.timedelta(days=i)
                for i in range((end - start).days + 1)
            ]
            logger.debug(
                "Expanded the date sequence from %s to %s into %d dates",
                start,
                end,
                len(expanded),
            )
            return expanded

        logger.debug("The date sequence contains two dates: %s", _dates)
        return _dates

    def _filter_and_reduce_dates(
        self,
        date_list: tuple[datetime.date, ...],
        today: datetime.date,
        schedule_type: str,
    ) -> datetime.date | tuple[datetime.date, datetime.date] | None:
        logger.debug(
            "Filtering dates for schedule type '%s' (today is %s)",
            schedule_type,
            today,
        )
        tomorrow = today + datetime.timedelta(days=1)

        if len(date_list) == 2:
            start, end = date_list[0], date_list[1]
            dates_for_filter = [
                start + datetime.timedelta(days=i)
                for i in range((end - start).days + 1)
            ]
        else:
            expanded = self._expand_dates(date_list)
            if expanded is None:
                logger.debug("Failed to expand the date list before filtering")
                return None
            elif isinstance(expanded, datetime.date):
                dates_for_filter = [expanded]
            else:
                dates_for_filter = expanded

        if schedule_type == "today":
            filtered = [d for d in dates_for_filter if d == today]
        else:
            filtered = [d for d in dates_for_filter if d >= tomorrow]

        logger.debug(
            "Filtered %d dates out of %d for schedule type '%s'",
            len(filtered),
            len(dates_for_filter),
            schedule_type,
        )

        if not filtered:
            return None
        if len(filtered) == 1:
            return filtered[0]
        return filtered[0], filtered[-1]

    def _extract_dates(
        self,
        matrix: ndarray[tuple[int, int], dtype[Any]],
        schedule_at: Literal["today", "tomorrow"],
    ) -> datetime.date | tuple[datetime.date, datetime.date] | None:
        logger.debug("Extracting dates from the schedule matrix for %s", schedule_at)

        match_func = vectorize(
            lambda s: (
                s
                and bool(
                    self._DATE_WORD_PATTERN.findall(s)
                    or self._DATE_NUMBERED_PATTERN.findall(s)
                )
            )
        )

        mask = match_func(matrix)

        if not (matrix_mask := matrix[mask]).any():
            logger.debug("No date-like strings were found in the schedule matrix")
            return None

        _date_list: set[datetime.date] = set()

        for m_mask in matrix_mask:
            if schedule_date := self._DATE_WORD_PATTERN.findall(m_mask):
                for d in schedule_date:
                    _date_list.add(
                        datetime.date(
                            day=int(d[1]),
                            month=int(self._MONTH_TO_NUMBER[d[2]]),
                            year=int(d[3]),
                        )
                    )

            if schedule_date := self._DATE_NUMBERED_PATTERN.findall(m_mask):
                for d in schedule_date:
                    _date_list.add(
                        datetime.date(day=int(d[1]), month=int(d[2]), year=int(d[3]))
                    )

        date_list: tuple[datetime.date, ...] = tuple(sorted(_date_list))

        logger.debug(
            "Extracted %d unique dates from the schedule matrix", len(date_list)
        )

        if not date_list:
            logger.debug("No dates were extracted from the schedule matrix")
            return None

        today = datetime.datetime.now(system_settings.timezone).date()
        _date_list_result = self._filter_and_reduce_dates(date_list, today, schedule_at)

        if not _date_list_result:
            logger.debug(
                "The extracted dates do not match the schedule type (%s)", schedule_at
            )
            return None

        logger.debug("Resulting date(s) for %s: %s", schedule_at, _date_list_result)
        return _date_list_result

    def _extract_time_ranges(
        self, matrix: ndarray[tuple[int, int], dtype[Any]]
    ) -> tuple[LessonTimeRange, ...] | None:
        logger.debug("Extracting time ranges from the schedule matrix")

        match_func = vectorize(
            lambda s: s and bool(self._LESSONS_TIME_PATTERN.match(s))
        )

        mask = match_func(matrix)

        if not (matrix_mask := matrix[mask]).any():
            logger.debug("No time-range strings were found in the schedule matrix")
            return None

        lessons_time = []

        for l_t in matrix_mask:
            match = self._LESSONS_TIME_PATTERN.match(l_t)

            time_item = LessonTimeRange(
                start=datetime.time(
                    hour=int(match.group(1)),
                    minute=int(match.group(2)),
                ),
                end=datetime.time(
                    hour=int(match.group(3)),
                    minute=int(match.group(4)),
                ),
            )

            if time_item in lessons_time:
                logger.debug(
                    "Duplicate time range %s found, stopping extraction",
                    time_item,
                )
                break

            lessons_time.append(time_item)

        logger.debug("Extracted %d unique time ranges", len(lessons_time))
        return tuple(sorted(lessons_time, key=lambda x: x.start))

    def _extract_groups(
        self,
        matrix: ndarray[tuple[int, int], dtype[Any]],
    ) -> tuple[GroupParser, ...] | None:
        logger.debug("Extracting groups from the schedule matrix")

        match_func = vectorize(
            lambda s: s and bool(self._GROUP_NUMBER_PATTERN.match(s))
        )

        mask = match_func(matrix)

        if not (matrix_mask := matrix[mask]).any():
            logger.debug("No group-like strings were found in the schedule matrix")
            return None

        groups = [
            GroupParser(title=g, pos_x=int(x), pos_y=int(y), is_active=True)
            for g, (y, x) in zip(matrix_mask, argwhere(mask), strict=False)
        ]

        logger.debug("Extracted %d unique groups", len(groups))
        return tuple(sorted(groups, key=lambda x: x.index))

    def _extract_day_schedules(  # noqa: C901
        self,
        schedule_matrix: ndarray[tuple[int, int], dtype[Any]],
        time_ranges: tuple[LessonTimeRange, ...],
        groups_parser: tuple[GroupParser, ...],
    ) -> dict[Group, DayScheduleItem] | None:
        logger.debug(
            "Extracting day schedules for %d groups and %d time ranges",
            len(groups_parser),
            len(time_ranges),
        )

        group_day_schedules: dict[Group, DayScheduleItem] = {}

        lessons_count = len(time_ranges)

        for group_parser in groups_parser:
            logger.debug(
                "Processing group %s at position (y=%d, x=%d)",
                group_parser.group,
                group_parser.pos_y,
                group_parser.pos_x,
            )

            lessons: list[LessonItem] = []

            group_lessons = [
                lesson
                for l_idx, lesson in enumerate(
                    schedule_matrix[
                        group_parser.pos_y + 1 : group_parser.pos_y + 1 + lessons_count,
                        group_parser.pos_x : group_parser.pos_x + 2,
                    ]
                )
                if self._LESSONS_TIME_PATTERN.match(
                    schedule_matrix[group_parser.pos_y + 1 + l_idx, 1]
                )
            ]

            logger.debug(
                "Found %d raw lesson rows for group %s",
                len(group_lessons),
                group_parser.group,
            )

            for l_idx, (lesson, cabinets) in enumerate(group_lessons):
                if lesson is None or not lesson.strip():
                    logger.debug(
                        "Skipping empty lesson at index %d for group %s",
                        l_idx,
                        group_parser.group,
                    )
                    continue

                cabinets = tuple(cabinets.split("/")) if cabinets else ()

                logger.debug(
                    "Adding lesson '%s' with cabinets %s for group %s",
                    lesson,
                    cabinets,
                    group_parser.group,
                )

                lessons.append(
                    LessonItem(
                        time_range=time_ranges[l_idx],
                        name=[LessonTitle(title=l_t) for l_t in lesson.split("/")],
                        cabinets=tuple(Cabinet(cab) for cab in cabinets),
                    )
                )

            if lessons:
                while lessons and str(lessons[-1].name).lower() == "обед":
                    logger.debug(
                        "Removing trailing 'обед' lesson for group %s",
                        group_parser.group,
                    )
                    lessons.pop()

                while lessons and str(lessons[0].name).lower() == "обед":
                    logger.debug(
                        "Removing leading 'обед' lesson for group %s",
                        group_parser.group,
                    )
                    lessons.pop(0)

                if not lessons:
                    logger.debug(
                        "No lessons left for group %s after removing 'обед'",
                        group_parser.group,
                    )
                    continue

                group_day_schedules[group_parser.group] = DayScheduleItem(
                    group=group_parser.group,
                    lessons=lessons,
                )

                logger.debug(
                    "Stored %d lessons for group %s",
                    len(lessons),
                    group_parser.group,
                )
            else:
                logger.debug("No lessons found for group %s", group_parser.group)

        if not group_day_schedules:
            logger.debug("No day schedules were built for any group")
            return None

        logger.debug("Built day schedules for %d groups", len(group_day_schedules))
        return group_day_schedules

    def _extract_cabinets_and_titles(
        self,
        day_schedules: dict[Group, DayScheduleItem],
    ) -> tuple[list[Cabinet], list[LessonTitle]]:
        logger.debug(
            "Extracting cabinets and lesson titles from %d day schedules",
            len(day_schedules),
        )

        _cabinets_return = set()
        _lesson_titles_return = set()

        for group, day_schedule in day_schedules.items():
            if not day_schedule.lessons:
                logger.debug("Skipping group %s: it has no lessons", group)
                continue

            for lesson in day_schedule.lessons:
                if lesson.cabinets:
                    _cabinets_return.update(lesson.cabinets)

                _lesson_titles_return.update(lesson.name)

            logger.debug(
                "Processed %d lessons for group %s",
                len(day_schedule.lessons),
                group,
            )

        logger.debug(
            "Extracted %d unique cabinets and %d unique lesson titles",
            len(_cabinets_return),
            len(_lesson_titles_return),
        )

        return list(_cabinets_return), list(_lesson_titles_return)
