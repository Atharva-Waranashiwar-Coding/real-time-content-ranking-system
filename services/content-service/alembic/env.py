"""Alembic environment configuration for content-service database migrations.

This file contains the logic to manage database schemas.
"""

import logging
from logging.config import fileConfig

from alembic import context
from app import models  # noqa: F401
from app.core.config import config
from app.db.base import Base
from sqlalchemy import engine_from_config, pool

# This is the Alembic Config object, which provides the values to the needed placeholders
alembic_cfg = context.config

# Interpret the config file for Python logging.
if alembic_cfg.config_file_name is not None:
    fileConfig(alembic_cfg.config_file_name)
logger = logging.getLogger("alembic.env")

# Alembic runs synchronously, so use a sync PostgreSQL driver here.
alembic_cfg.set_main_option("sqlalchemy.url", config.DATABASE_URL.replace("+asyncpg", "+psycopg2"))

# Add models for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = alembic_cfg.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        alembic_cfg.get_section(alembic_cfg.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
