# alembic/env.py
from __future__ import annotations

import asyncio
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

# --- add app package to path (adjust if needed) ---
sys.path.append(".")

from db.db_config import get_settings
from db.models import Base

# Alembic Config object
config = context.config

# Logging config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate
target_metadata = Base.metadata


def get_sync_url() -> str:
    """
    Build sync URL for MySQL (pymysql) from env vars via your Settings.
    """
    settings = get_settings()
    return (
        f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )


def get_async_url() -> str:
    """
    If you really want async engine for migrations (not required),
    build aiomysql URL.
    """
    settings = get_settings()
    return (
        f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )


def run_migrations_offline() -> None:
    """
    Offline mode: emit SQL to scripts, no DB connection.
    """
    url = get_sync_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Configure Alembic with a connection and run migrations.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Async wrapper that uses an async engine but hands a sync connection
    back to Alembic.
    """
    connectable: AsyncEngine = create_async_engine(
        get_async_url(),
        poolclass=pool.NullPool,
        future=True,
    )

    async with connectable.connect() as async_connection:
        await async_connection.run_sync(do_run_migrations)


def run_migrations_online() -> None:
    """
    Entry point for online migrations.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
