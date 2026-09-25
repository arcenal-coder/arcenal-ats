"""Alembic migration context for ARCenal ATS."""

from __future__ import annotations

from os import environ

from alembic import context
from sqlalchemy import engine_from_config, pool

from arcenal_ats.database import Base
import arcenal_ats.models  # noqa: F401


config = context.config
target_metadata = Base.metadata
database_url = environ.get("ARCENAL_ATS_DATABASE_URL")

if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
