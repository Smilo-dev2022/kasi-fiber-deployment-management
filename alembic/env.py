import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import application metadata
try:
    # Ensure app is importable when running from project root
    from app.core.deps import Base, DATABASE_URL
except Exception:  # pragma: no cover - fallback when app isn't importable yet
    Base = None
    DATABASE_URL = os.getenv("DATABASE_URL", "")


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None and os.path.exists(config.config_file_name):
    fileConfig(config.config_file_name)


# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = getattr(Base, "metadata", None)


def _set_sqlalchemy_url_from_env() -> None:
    url_from_ini = config.get_main_option("sqlalchemy.url")
    if not url_from_ini or url_from_ini.startswith("sqlite:///"):
        # Prefer env var/DATABASE_URL from the app
        url = os.getenv("DATABASE_URL", DATABASE_URL)
        if url:
            # Ensure we use psycopg v3 driver if DSN lacks explicit driver
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+psycopg://", 1)
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg://", 1)
            config.set_main_option("sqlalchemy.url", url)


def run_migrations_offline() -> None:
    _set_sqlalchemy_url_from_env()
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    _set_sqlalchemy_url_from_env()
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

