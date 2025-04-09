"""Database session module."""

import logging
import time
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from src.app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Connection retry settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


class DatabaseSessionManager:
    """Manager for database sessions.

    This class manages the database engine and session factory.
    It provides methods for getting database sessions and handles
    connection retries.
    """

    def __init__(self) -> None:
        """Initialize DatabaseSessionManager."""
        self.engine = None
        self.session_factory = None
        self._initialized = False

    def initialize(self, retry: bool = True) -> bool:
        """Initialize the database engine and session factory.

        Args:
            retry: Whether to retry the connection on failure.

        Returns:
            True if initialization succeeded, False otherwise.
        """
        if self._initialized:
            return True

        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                logger.info(
                    f"Connecting to database: {settings.DATABASE_URL.split('@')[1] if '@' in str(settings.DATABASE_URL) else 'unknown'}"
                )

                # Create engine
                self.engine = create_engine(
                    str(settings.DATABASE_URL),
                    echo=settings.DEBUG,
                    future=True,
                    pool_pre_ping=True,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                )

                # Create session factory
                self.session_factory = sessionmaker(
                    self.engine,
                    expire_on_commit=False,
                    autocommit=False,
                    autoflush=False,
                )

                # Test the connection
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))

                logger.info("Database connection established successfully")
                self._initialized = True
                return True

            except SQLAlchemyError as e:
                retry_count += 1
                logger.warning(
                    f"Database connection attempt {retry_count} failed: {str(e)}"
                )

                if not retry or retry_count >= MAX_RETRIES:
                    logger.error(
                        f"Failed to connect to database after {retry_count} attempts"
                    )
                    break

                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)

        return False

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Get a database session.

        Yields:
            Session: Database session.
        """
        if not self._initialized:
            success = self.initialize()
            if not success:
                raise RuntimeError("Database connection is not initialized")

        session = self.session_factory()
        try:
            yield session
        except SQLAlchemyError as e:
            logger.exception(f"Database session error: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()

    def get_dummy_session(self) -> Generator[Session, None, None]:
        """Get a dummy session when database is not available.

        Yields:
            A mock session that raises exceptions when used.
        """

        class DummySession:
            def execute(self, *args, **kwargs):
                raise RuntimeError("No database connection available")

            def commit(self):
                raise RuntimeError("No database connection available")

            def rollback(self):
                pass

            def close(self):
                pass

        def _get_session():
            session = DummySession()
            try:
                yield session
            finally:
                session.close()

        return _get_session()


# Create a singleton instance
db_manager = DatabaseSessionManager()


def get_db() -> Generator[Session, None, None]:
    """Get database session.

    This is the dependency to be used in FastAPI endpoints.

    Yields:
        Session: Database session.
    """
    try:
        with db_manager.session() as session:
            yield session
    except RuntimeError as e:
        logger.warning(f"Using dummy database session: {str(e)}")
        for session in db_manager.get_dummy_session():
            yield session
