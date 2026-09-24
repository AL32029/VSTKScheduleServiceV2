from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Time,
    column,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .bot_items import BotUserCabinetSubscribeORM, BotUserGroupSubscribeORM


# ============== [Базовые ORM-модели] ==============
class GroupORM(Base):
    __tablename__ = "groups"

    index: Mapped[str] = mapped_column(
        String(6),
        primary_key=True,
    )
    number: Mapped[str] = mapped_column(String(7))

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
    )

    subscribes: Mapped[list[BotUserGroupSubscribeORM]] = relationship(
        "BotUserGroupSubscribeORM",
        back_populates="group",
        lazy="noload",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CabinetORM(Base):
    __tablename__ = "cabinets"

    index: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
    )
    number: Mapped[str] = mapped_column(String(48))

    lesson_cabinets: Mapped[list[LessonCabinetORM]] = relationship(
        "LessonCabinetORM",
        back_populates="cabinet",
        lazy="noload",
    )

    redirects_from: Mapped[list[CabinetRedirectORM]] = relationship(
        "CabinetRedirectORM",
        back_populates="cabinet_to",
        lazy="noload",
        passive_deletes=True,
    )
    redirect_to: Mapped[CabinetRedirectORM] = relationship(
        "CabinetRedirectORM",
        back_populates="cabinet_from",
        lazy="joined",
    )

    subscribes: Mapped[list[BotUserCabinetSubscribeORM]] = relationship(
        "BotUserCabinetSubscribeORM",
        back_populates="cabinet",
        lazy="noload",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class LessonTimeORM(Base):
    __tablename__ = "lesson_times"
    __table_args__ = (
        CheckConstraint(
            "time_type IN ('standard', 'reduced')",
            name="ck_lesson_times_time_type",
        ),
        Index(
            "idx_lesson_times_time_type_lesson_start",
            "time_type",
            "lesson_start",
            unique=True,
            postgresql_where="active_until IS NULL",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    time_type: Mapped[Literal["standard", "reduced"]] = mapped_column(String(24))

    lesson_start: Mapped[datetime.time] = mapped_column(Time)
    lesson_end: Mapped[datetime.time] = mapped_column(Time)

    active_from: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        server_default=func.now(),
    )
    active_until: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    lessons: Mapped[list[LessonORM]] = relationship(
        "LessonORM",
        back_populates="time_range",
        lazy="noload",
    )


class LessonTitleORM(Base):
    __tablename__ = "lesson_titles"
    __table_args__ = (
        Index(
            "idx_lesson_titles_effective_title_trgm",
            func.coalesce(column("custom_title"), column("original_title")),
            postgresql_using="gin",
            postgresql_ops={
                "coalesce": "gin_trgm_ops",
            },
        ),
    )

    index: Mapped[str] = mapped_column(
        String(256),
        primary_key=True,
    )
    original_title: Mapped[str] = mapped_column(String(256))
    custom_title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_countable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
    )

    redirects_from: Mapped[list[LessonTitleRedirectORM]] = relationship(
        "LessonTitleRedirectORM",
        back_populates="title_to",
        lazy="noload",
        passive_deletes=True,
    )
    redirect_to: Mapped[LessonTitleRedirectORM] = relationship(
        "LessonTitleRedirectORM",
        back_populates="title_from",
        lazy="joined",
    )

    lesson_titles: Mapped[list[LessonTitleORM]] = relationship(
        "LessonTitleORM",
        back_populates="lesson_title",
        lazy="noload",
    )


# ============== [ORM-модель урока] ==============
class LessonORM(Base):
    __tablename__ = "lessons"
    __table_args__ = (
        Index(
            "idx_lessons_lesson_at_group_index",
            "group_index",
            "lesson_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    lesson_at: Mapped[datetime.date] = mapped_column(Date)
    group_index: Mapped[str] = mapped_column(
        ForeignKey("groups.index", ondelete="RESTRICT")
    )
    time_range_id: Mapped[int] = mapped_column(
        ForeignKey("lesson_times.id", ondelete="RESTRICT")
    )

    time_range: Mapped[LessonTimeORM] = relationship(
        "LessonTimeORM",
        back_populates="lessons",
        lazy="joined",
    )

    cabinets: Mapped[list[LessonCabinetORM]] = relationship(
        "LessonCabinetORM",
        back_populates="lesson",
        lazy="selectin",
        order_by="LessonCabinetORM.cabinet_index",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    titles: Mapped[list[LessonTitleORM]] = relationship(
        "LessonTitleORM",
        back_populates="lesson",
        lazy="selectin",
        order_by="LessonTitleORM.lesson_title_index",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


# ============== [ORM-модели отношений] ==============
class LessonCabinetORM(Base):
    __tablename__ = "lesson_cabinets"
    __table_args__ = (
        CheckConstraint(
            "cabinet_index BETWEEN 0 AND 1",
            name="ck_lesson_cabinets_cabinet_index",
        ),
        Index(
            "idx_lesson_cabinets_lesson_id_cabinet_id",
            "lesson_id",
            "cabinet_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
    cabinet_id: Mapped[str] = mapped_column(
        ForeignKey("cabinets.index", ondelete="RESTRICT")
    )
    cabinet_index: Mapped[int] = mapped_column(SmallInteger)

    cabinet: Mapped[CabinetORM] = relationship(
        "CabinetORM",
        back_populates="lesson_cabinets",
        lazy="joined",
    )
    lesson: Mapped[LessonORM] = relationship(
        "LessonORM",
        back_populates="cabinets",
        lazy="noload",
    )


class LessonLessonTitleORM(Base):
    __tablename__ = "lesson_lesson_titles"
    __table_args__ = (
        CheckConstraint(
            "lesson_title_index BETWEEN 0 AND 1",
            name="ck_lesson_lesson_titles_lesson_title_index",
        ),
        Index(
            "idx_lesson_lesson_titles_lesson_id_lesson_title_id",
            "lesson_id",
            "lesson_title_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
    lesson_title_id: Mapped[str] = mapped_column(
        ForeignKey("lesson_titles.index", ondelete="RESTRICT")
    )
    lesson_title_index: Mapped[int] = mapped_column(SmallInteger)

    lesson_title: Mapped[LessonTitleORM] = relationship(
        "LessonTitleORM",
        back_populates="lesson_titles",
        lazy="joined",
    )
    lesson: Mapped[LessonORM] = relationship(
        "LessonORM",
        back_populates="titles",
        lazy="noload",
    )


class CabinetRedirectORM(Base):
    __tablename__ = "cabinet_redirects"
    __table_args__ = (
        CheckConstraint(
            "cabinet_from_index != cabinet_to_index",
            name="ck_cabinet_redirects_no_self",
        ),
    )

    cabinet_from_index: Mapped[str] = mapped_column(
        ForeignKey("cabinets.index", ondelete="RESTRICT"),
        primary_key=True,
    )
    cabinet_to_index: Mapped[str] = mapped_column(
        ForeignKey("cabinets.index", ondelete="RESTRICT")
    )

    cabinet_from: Mapped[CabinetORM] = relationship(
        "CabinetORM",
        back_populates="redirect_to",
    )
    cabinet_to: Mapped[CabinetORM] = relationship(
        "CabinetORM",
        back_populates="redirects_from",
    )


class LessonTitleRedirectORM(Base):
    __tablename__ = "lesson_title_redirects"
    __table_args__ = (
        CheckConstraint(
            "title_from_index != title_to_index",
            name="ck_lesson_title_redirects_no_self",
        ),
    )

    title_from_index: Mapped[str] = mapped_column(
        ForeignKey("lesson_titles.index", ondelete="RESTRICT"),
        primary_key=True,
    )
    title_to_index: Mapped[str] = mapped_column(
        ForeignKey("lesson_titles.index", ondelete="RESTRICT"),
    )

    title_from: Mapped[LessonTitleORM] = relationship(
        "LessonTitleORM",
        back_populates="redirect_to",
    )
    title_to: Mapped[LessonTitleORM] = relationship(
        "LessonTitleORM",
        back_populates="redirects_from",
    )
