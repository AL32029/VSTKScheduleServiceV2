import asyncio
import logging
import ssl
from ssl import SSLContext
from typing import cast

import aiofiles
import sqlalchemy.exc
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from .settings import BaseDevDatabaseSettings, BaseProdDatabaseSettings

logger = logging.getLogger(__name__)


class DatabaseEngineManager:
    def __init__(
        self,
        settings: "BaseDevDatabaseSettings | BaseProdDatabaseSettings",
    ) -> None:
        logger.info("Initialization of the database manager has begun")
        self._config: BaseDevDatabaseSettings | BaseProdDatabaseSettings = settings
        self._engine: AsyncEngine | None = None
        self._lock = asyncio.Lock()
        logger.info("The database manager has been successfully initialized")

    async def get_engine(self) -> AsyncEngine:
        logger.info("Obtaining the database engine")
        if self._engine is None:
            async with self._lock:
                if self._engine is None:
                    logger.warning(
                        "The database engine is missing; create a new engine"
                    )
                    self._engine = await self._build_engine()

        logger.info("The database engine has been obtained")
        return cast(AsyncEngine, self._engine)

    async def rotate(self) -> bool:
        logger.info("The rotation of database secrets has begun")
        async with self._lock:
            old_engine = self._engine
            try:
                logger.info("Initialization of the new database engine assembly")
                new_engine = await self._build_engine()
                logger.info(
                    "The assembly of the new database engine has been successfully "
                    "completed"
                )

                logger.info(
                    "Checking the database connection status via the new engine"
                )
                async with new_engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                logger.info(
                    "The check of the database connection status "
                    "via the new engine was successful"
                )

                self._engine = new_engine

                if old_engine is not None:
                    logger.info(
                        "Adding a task to disconnect connections to the database "
                        "via the old engine"
                    )
                    asyncio.create_task(self._dispose_engine(old_engine))
                    logger.info(
                        "The task to disconnect from the database via the old "
                        "engine has been successfully added"
                    )

                logger.info(
                    "The database secret rotation has been completed successfully"
                )
                return True
            except (sqlalchemy.exc.SQLAlchemyError, TimeoutError, ConnectionError):
                logger.exception(
                    "An error occurred during the rotation of database secrets"
                )
                return False

    async def dispose(self, delay: float = 15.0) -> None:
        if self._engine is not None:
            await self._dispose_engine(self._engine, delay)

    @property
    def watchfiles_ssl_files(self) -> set[str]:
        if isinstance(self._config, BaseProdDatabaseSettings):
            return {
                path
                for path in [
                    self._config.SSL_CA_CERT_FILE,
                    self._config.SSL_CERT_FILE,
                    self._config.SSL_KEY_FILE,
                ]
                if path
            }

        return set()

    async def _build_engine(self):
        logger.info("The database engine has begun to be assembled")

        engine_url = await self._build_engine_url()

        if_prod = isinstance(self._config, BaseProdDatabaseSettings)

        ssl_context = self._load_ssl_context() if if_prod else None
        engine = create_async_engine(
            engine_url,
            pool_pre_ping=True,
            pool_size=self._config.POOL_SIZE,
            max_overflow=self._config.MAX_OVERFLOW,
            connect_args={"ssl": ssl_context} if if_prod else {},
        )

        logger.info("The database engine has been successfully created")
        return engine

    async def _dispose_engine(self, engine: AsyncEngine, delay: float = 30.0) -> None:
        logger.info(
            "The connections through the old database engine will "
            "be terminated in %s seconds",
            delay,
        )
        await asyncio.sleep(delay)
        logger.info("Disruption of connections via the old database engine")
        await engine.dispose()
        logger.info(
            "Connections through the old database engine have been successfully "
            "terminated"
        )

    def _load_ssl_context(self) -> SSLContext | None:
        if not isinstance(self._config, BaseProdDatabaseSettings):
            logger.warning(
                "Obtaining an SSL context is available only for the production mode "
                "of the system"
            )
            return None

        logger.info("The SSL context has been initialized")
        ssl_context = ssl.create_default_context(cafile=self._config.SSL_CA_CERT_FILE)
        ssl_context.load_cert_chain(
            certfile=self._config.SSL_CERT_FILE, keyfile=self._config.SSL_KEY_FILE
        )
        logger.info("The SSL context has been successfully established")
        return ssl_context

    async def _build_engine_url(self) -> URL:
        logger.info("The generation of the database connection URL has begun")
        if isinstance(self._config, BaseProdDatabaseSettings):
            async with aiofiles.open(self._config.SSL_CERT_FILE, "rb") as f:
                cert_data = await f.read()

            cert = x509.load_pem_x509_certificate(cert_data, default_backend())

            common_name = str(
                cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value
            )

            url = URL.create(
                "postgresql+asyncpg",
                host=self._config.HOST,
                port=self._config.PORT,
                username=common_name,
                database=self._config.BASE,
            )
        else:
            url = URL.create(
                "postgresql+asyncpg",
                host=self._config.HOST,
                port=self._config.PORT,
                username=self._config.USER,
                password=self._config.PASSWORD,
                database=self._config.BASE,
            )
        logger.info("The database connection URL has been successfully generated")
        return url
