import logging
from collections.abc import AsyncIterable
from typing import cast

from database_manager.manager import DatabaseEngineManager
from database_manager.settings import BaseDevDatabaseSettings, BaseProdDatabaseSettings
from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from parser.infrastructure.config.database_settings import DatabaseSettings

logger = logging.getLogger(__name__)


class DatabaseProvider(Provider):
    scope = Scope.APP

    @provide
    def settings(
        self, settings: DatabaseSettings
    ) -> BaseDevDatabaseSettings | BaseProdDatabaseSettings:
        logger.debug(
            "Providing database settings (mode=%s, config=%s)",
            settings.mode,
            type(settings.config).__name__,
        )
        return settings.config

    @provide
    def manager(
        self, settings: BaseDevDatabaseSettings | BaseProdDatabaseSettings
    ) -> DatabaseEngineManager:
        logger.debug(
            "Creating DatabaseEngineManager with settings %s",
            type(settings).__name__,
        )
        return DatabaseEngineManager(settings=settings)

    @provide(scope=Scope.REQUEST)
    async def provide_session_maker(
        self, manager: "DatabaseEngineManager"
    ) -> async_sessionmaker[AsyncSession]:
        logger.debug("Creating async session maker from the database engine")

        session_maker = async_sessionmaker(
            cast(AsyncEngine, cast(object, await manager.get_engine())),
            expire_on_commit=False,
            class_=AsyncSession,
            autoflush=False,
        )

        logger.debug("Async session maker has been created")
        return session_maker

    @provide(scope=Scope.REQUEST)
    async def provide_session(
        self,
        session_maker: async_sessionmaker[AsyncSession],
    ) -> AsyncIterable[AsyncSession]:
        logger.debug("Requesting a new database session from the session maker")

        async with session_maker() as session:
            logger.debug("Database session has been opened: %s", session)
            try:
                logger.debug("Starting a new database transaction")
                async with session.begin():
                    logger.debug("Database transaction has been started")
                    yield session

                logger.debug("Database transaction committed successfully")
            except Exception as err:
                logger.debug(
                    "An error occurred during the database session, "
                    "the transaction will be rolled back: %s",
                    err,
                )
                raise
            finally:
                logger.debug("Closing the database session: %s", session)
                await session.aclose()
                logger.debug("Database session has been closed")
