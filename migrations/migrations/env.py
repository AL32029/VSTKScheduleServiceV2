import asyncio
import os
import ssl
from logging.config import fileConfig
from ssl import SSLContext

from alembic import context
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from database_models import Base
from sqlalchemy import URL, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def _system_mode() -> str:
    return os.environ.get("BASE_SYSTEM_MODE", "prod")


def _load_ssl_context() -> SSLContext:
    ca_file = os.environ.get(
        "DATABASE_SSL_CA_CERT_FILE", "/vault/secrets/database-tls.ca"
    )
    cert_file = os.environ.get(
        "DATABASE_SSL_CERT_FILE", "/vault/secrets/database-tls.crt"
    )
    key_file = os.environ.get(
        "DATABASE_SSL_KEY_FILE", "/vault/secrets/database-tls.key"
    )

    ssl_context = ssl.create_default_context(cafile=ca_file)
    ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)

    cert_reqs = os.environ.get("DATABASE_SSL_CERT_REQS", "required")
    if cert_reqs == "none":
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    elif cert_reqs == "optional":
        ssl_context.verify_mode = ssl.CERT_OPTIONAL
    else:
        ssl_context.verify_mode = ssl.CERT_REQUIRED

    check_hostname = os.environ.get("DATABASE_SSL_CHECK_HOSTNAME", "true").lower() in (
        "1",
        "true",
        "yes",
    )
    ssl_context.check_hostname = check_hostname

    return ssl_context


def _build_prod_url() -> str:
    cert_file = os.environ.get(
        "DATABASE_SSL_CERT_FILE", "/vault/secrets/database-tls.crt"
    )
    with open(cert_file, "rb") as f:
        cert = x509.load_pem_x509_certificate(f.read(), default_backend())

    common_name = str(
        cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value
    )

    host = os.environ["DATABASE_HOST"]
    port = int(os.environ.get("DATABASE_PORT", "5432"))
    database = os.environ["DATABASE_BASE"]

    return URL.create(
        "postgresql+asyncpg",
        host=host,
        port=port,
        username=common_name,
        database=database,
    ).render_as_string(hide_password=False)


def _build_url_and_connect_args() -> tuple[str, dict]:
    if _system_mode() == "prod":
        return _build_prod_url(), {"ssl": _load_ssl_context()}

    url = os.environ["MIGRATION_DATABASE_URL"]
    return url, {}


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url, _ = _build_url_and_connect_args()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url, connect_args = _build_url_and_connect_args()

    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
