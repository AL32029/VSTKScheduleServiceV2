from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .schedule_items import CabinetORM, GroupORM


class BotUserORM(Base):
    __tablename__ = "bot_users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        index=True,
    )

    joined_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        server_default=text("now()"),
    )
    last_activity_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        server_default=text("now()"),
    )

    user_metadata: Mapped[list[BotUserMetadataORM]] = relationship(
        "BotUserMetadataORM",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    group_subscribes: Mapped[list[BotUserGroupSubscribeORM]] = relationship(
        "BotUserGroupSubscribeORM",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    cabinet_subscribes: Mapped[list[BotUserCabinetSubscribeORM]] = relationship(
        "BotUserCabinetSubscribeORM",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class BotUserMetadataORM(Base):
    __tablename__ = "bot_users_metadata"
    __table_args__ = (
        Index(
            "idx_bot_users_metadata_user_id_key",
            "user_id",
            "key",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("bot_users.id", ondelete="CASCADE"))
    key: Mapped[str] = mapped_column(String(64))
    value: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    user: Mapped[BotUserORM] = relationship(
        "BotUserORM",
        back_populates="user_metadata",
        lazy="noload",
    )


class BotUserGroupSubscribeORM(Base):
    __tablename__ = "bot_user_group_subscribes"
    __table_args__ = (
        Index(
            "idx_bot_user_group_subscribes_user_id_group_index",
            "user_id",
            "group_index",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("bot_users.id", ondelete="CASCADE"))
    group_index: Mapped[str] = mapped_column(
        ForeignKey("groups.index", ondelete="CASCADE")
    )

    user: Mapped[BotUserORM] = relationship(
        "BotUserORM",
        back_populates="group_subscribes",
        lazy="noload",
    )
    group: Mapped[GroupORM] = relationship(
        "GroupORM",
        back_populates="subscribes",
    )


class BotUserCabinetSubscribeORM(Base):
    __tablename__ = "bot_user_cabinet_subscribes"
    __table_args__ = (
        Index(
            "idx_bot_user_cabinet_subscribes_user_id_cabinet_index",
            "user_id",
            "cabinet_index",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("bot_users.id", ondelete="CASCADE"))
    cabinet_index: Mapped[str] = mapped_column(
        ForeignKey("cabinets.index", ondelete="CASCADE")
    )

    user: Mapped[BotUserORM] = relationship(
        "BotUserORM",
        back_populates="cabinet_subscribes",
        lazy="noload",
    )
    cabinet: Mapped[CabinetORM] = relationship(
        "CabinetORM",
        back_populates="subscribes",
    )
