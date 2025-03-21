"""Alembic environment configuration."""

import logging
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError

# Import all models to ensure they are registered with SQLAlchemy
from src.app.core.config import settings
from src.app.core.db.base import Base
from src.app.core.db.session import db_manager

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alembic.env")

try:
    # this is the Alembic Config object, which provides
    # access to the values within the .ini file in use.
    config = context.config

    # Interpret the config file for Python logging.
    # This line sets up loggers basically.
    if config.config_file_name is not None:
        fileConfig(config.config_file_name)

    # add your model's MetaData object here
    # for 'autogenerate' support
    target_metadata = Base.metadata

    # Get the database URL from environment variables
    database_url = os.getenv("DATABASE_URL")
    print(f"DATABASE_URL: {database_url}")
    if not database_url:
        # Try to get it from settings
        database_url = str(settings.DATABASE_URL) if settings.DATABASE_URL else None
    print(f"DATABASE_URL: {database_url}")

    # Log the database URL for debugging (mask sensitive parts)
    if database_url:
        db_url_parts = database_url.split("@")
        if len(db_url_parts) > 1:
            masked_url = f"****@{db_url_parts[1]}"
            logger.info(f"Using database URL: {masked_url}")
        else:
            logger.info("Database URL is not in the expected format")
    else:
        logger.error("DATABASE_URL not configured. Migrations cannot run.")
        sys.exit(1)

    # Override sqlalchemy.url with the actual database URL
    config.set_main_option("sqlalchemy.url", database_url)

    def run_migrations_offline() -> None:
        """Run migrations in 'offline' mode.

        This configures the context with just a URL
        and not an Engine, though an Engine is acceptable
        here as well.  By skipping the Engine creation
        we don't even need a DBAPI to be available.

        Calls to context.execute() here emit the given string to the
        script output.
        """
        url = config.get_main_option("sqlalchemy.url")
        context.configure(
            url=url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )

        with context.begin_transaction():
            context.run_migrations()

    def do_run_migrations(connection: Connection) -> None:
        """Run migrations in 'online' mode.

        Args:
            connection: Database connection.
        """
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    def run_migrations_online() -> None:
        """Run migrations using a synchronous engine.

        This function creates a standard SQLAlchemy engine for database connections.
        """
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )

        with connectable.connect() as connection:
            do_run_migrations(connection)

    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()

except SQLAlchemyError as e:
    logging.error(f"Database connection error in migrations: {str(e)}")
    logging.error(
        "Please ensure the database is running and DATABASE_URL is correctly configured."
    )
    sys.exit(1)
except ImportError as e:
    logging.error(f"Import error in migrations: {str(e)}")
    logging.error("Please ensure all required modules are installed.")
    sys.exit(1)
except Exception as e:
    logging.error(f"Error in migrations: {str(e)}")
    sys.exit(1)
