"""Async database session module."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


# Create async engine and session factory
if settings.ENVIRONMENT == "test":
    async_engine = create_async_engine(
        str(settings.DATABASE_URL),
        echo=settings.DEBUG,
        future=True,
        pool_pre_ping=True,
    )
else:
    async_engine = create_async_engine(
        str(settings.DATABASE_URL),
        echo=settings.DEBUG,
        future=True,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

async_session_factory = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session.

    Yields:
        AsyncSession: Asynchronous database session.
    """
    session = async_session_factory()
    try:
        yield session
    except Exception as e:
        logger.exception(f"Async database session error: {str(e)}")
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session as a dependency.

    This function is designed to be used as a FastAPI dependency.

    Yields:
        AsyncSession: Asynchronous database session.
    """
    async with get_async_session() as session:
        yield session
