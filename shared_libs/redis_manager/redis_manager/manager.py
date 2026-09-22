import asyncio
import logging
from typing import Literal

import redis.exceptions
from arq.connections import ArqRedis, RedisSettings, create_pool
from redis.asyncio import Redis

from .settings import BaseDevRedisSettings, BaseProdRedisSettings

logger = logging.getLogger(__name__)


class RedisClientManager:
    def __init__(
        self,
        settings: BaseDevRedisSettings | BaseProdRedisSettings,
        redis_type: Literal["main", "arq"],
    ) -> None:
        if redis_type not in ("main", "arq"):
            raise ValueError("The redis_type argument must accept either main or arq")

        logger.info("Initialization of the redis manager has begun")

        self._config = settings
        self._redis_type = redis_type
        self._client: Redis | ArqRedis | None = None
        self._lock = asyncio.Lock()
        self._close_tasks: set[asyncio.Task[None]] = set()

        logger.info("The redis manager has been successfully initialized")

    async def get_client(self) -> Redis | ArqRedis:
        logger.info("Obtaining the redis client")
        if self._client is not None:
            logger.info("The redis client has been obtained")
            return self._client

        async with self._lock:
            if self._client is not None:
                logger.info("The redis client has been obtained")
                return self._client

            logger.warning("The redis client is missing; create a new client")
            self._client = await self._create_client()
            logger.info("The redis client has been obtained")
            return self._client

    async def rotate(self) -> bool:
        logger.info("The rotation of redis secrets has begun")

        async with self._lock:
            old_client = self._client
            try:
                logger.info("Initialization of the new redis client assembly")
                new_client = await self._create_client()
                logger.info(
                    "The assembly of the new redis client has been successfully "
                    "completed"
                )

                logger.info("Checking the redis connection status via the new client")
                await asyncio.wait_for(new_client.ping(), timeout=5.0)
                logger.info(
                    "The check of the redis connection status via the new client "
                    "was successful"
                )

                self._client = new_client

                if old_client is not None:
                    logger.info(
                        "Adding a task to disconnect connections to the redis "
                        "via the old client"
                    )
                    task = asyncio.create_task(
                        self._close_client(old_client, delay=30.0),
                        name=f"redis-close-{id(old_client)}",
                    )
                    self._close_tasks.add(task)
                    task.add_done_callback(self._close_tasks.discard)
                    logger.info(
                        "The task to disconnect from the redis via the old "
                        "client has been successfully added"
                    )

                logger.info("The redis secret rotation has been completed successfully")
                return True

            except (
                redis.exceptions.RedisError,
                TimeoutError,
                ConnectionError,
                OSError,
            ):
                logger.exception(
                    "An error occurred during the rotation of redis secrets"
                )
                if "new_client" in locals() and new_client is not None:
                    await self._close_client(new_client, delay=0.0)
                return False

    async def close(self, delay: float = 0.0) -> None:
        async with self._lock:
            if self._client is not None:
                await self._close_client(self._client, delay=delay)
                self._client = None

        if self._close_tasks:
            await asyncio.gather(*self._close_tasks, return_exceptions=True)
            self._close_tasks.clear()

    @property
    def watchfiles_ssl_files(self) -> set[str]:
        if isinstance(self._config, BaseProdRedisSettings):
            return {
                path
                for path in (
                    self._config.SSL_CA_CERT_FILE,
                    self._config.SSL_CERT_FILE,
                    self._config.SSL_KEY_FILE,
                )
                if path
            }
        return set()

    @property
    def arq_settings(self) -> RedisSettings:
        if self._redis_type != "arq":
            raise RuntimeError("get_arq_settings available only for redis_type='arq'")

        is_prod = isinstance(self._config, BaseProdRedisSettings)

        return RedisSettings(
            host=self._config.HOST,
            port=self._config.PORT,
            database=self._config.DB_NUMBER,
            username=getattr(self._config, "USERNAME", None),
            password=getattr(self._config, "PASSWORD", None),
            ssl=is_prod,
            ssl_certfile=getattr(self._config, "SSL_CERT_FILE", None)
            if is_prod
            else None,
            ssl_keyfile=getattr(self._config, "SSL_KEY_FILE", None)
            if is_prod
            else None,
            ssl_ca_certs=getattr(self._config, "SSL_CA_CERT_FILE", None)
            if is_prod
            else None,
            ssl_cert_reqs=getattr(self._config, "SSL_CERT_REQS", "required")
            if is_prod
            else "required",
            ssl_check_hostname=getattr(self._config, "SSL_CHECK_HOSTNAME", True)
            if is_prod
            else False,
            conn_timeout=getattr(self._config, "CONN_TIMEOUT", 1),
            conn_retries=getattr(self._config, "CONN_RETRIES", 5),
            conn_retry_delay=getattr(self._config, "CONN_RETRY_DELAY", 1),
            max_connections=getattr(self._config, "MAX_CONNECTIONS", None),
        )

    async def _create_client(self) -> Redis | ArqRedis:
        logger.info("The redis client has begun to be assembled")
        is_prod = isinstance(self._config, BaseProdRedisSettings)
        common_kwargs = {
            "host": self._config.HOST,
            "port": self._config.PORT,
            "ssl": is_prod,
            "ssl_certfile": getattr(self._config, "SSL_CERT_FILE", None)
            if is_prod
            else None,
            "ssl_keyfile": getattr(self._config, "SSL_KEY_FILE", None)
            if is_prod
            else None,
            "ssl_ca_certs": getattr(self._config, "SSL_CA_CERT_FILE", None)
            if is_prod
            else None,
            "ssl_cert_reqs": getattr(self._config, "SSL_CERT_REQS", "required")
            if is_prod
            else "required",
            "ssl_check_hostname": getattr(self._config, "SSL_CHECK_HOSTNAME", True)
            if is_prod
            else False,
            "username": getattr(self._config, "USERNAME", None),
            "password": getattr(self._config, "PASSWORD", None),
            "max_connections": getattr(self._config, "MAX_CONNECTIONS", None),
        }

        if self._redis_type == "main":
            client = Redis(
                db=self._config.DB_NUMBER,
                **common_kwargs,
            )
        else:
            settings = RedisSettings(
                database=self._config.DB_NUMBER,
                conn_timeout=getattr(self._config, "CONN_TIMEOUT", 1),
                conn_retries=getattr(self._config, "CONN_RETRIES", 5),
                conn_retry_delay=getattr(self._config, "CONN_RETRY_DELAY", 1),
                **common_kwargs,
            )
            client = await create_pool(settings)

        logger.info("The redis client has been successfully created")
        return client

    async def _close_client(
        self,
        client: Redis | ArqRedis,
        delay: float = 30.0,
    ) -> None:
        if delay > 0:
            logger.info(
                "The connections through the old redis client will "
                "be terminated in %s seconds",
                delay,
            )
            await asyncio.sleep(delay)

        logger.info("Disruption of connections via the old redis client")
        try:
            await client.aclose(close_connection_pool=True)
            logger.info(
                "Connections through the old redis client have "
                "been successfully terminated"
            )
        except Exception:
            logger.exception(
                "An error occurred while terminating connections "
                "via the old redis client"
            )
