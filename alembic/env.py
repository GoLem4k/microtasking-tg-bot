from __future__ import annotations

import asyncio
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

sys.path.append(".")

from db.db_config import get_settings
from db.models import Base


# ---------- Alembic config ----------

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_async_url() -> str:
    settings = get_settings()
    return settings.async_database_url


def get_sync_url() -> str:
    settings = get_settings()
    host = "db" if settings.USE_DOCKER_DB else settings.DB_HOST
    return (
        f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{host}:{settings.DB_PORT}/{settings.DB_NAME}"
    )


# ---------- offline ----------

def run_migrations_offline() -> None:
    url = get_sync_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------- online ----------

def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable: AsyncEngine = create_async_engine(
        get_async_url(),
        poolclass=pool.NullPool,
        future=True,
    )

    async with connectable.connect() as async_connection:
        await async_connection.run_sync(do_run_migrations)


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()