"""Test configuration module."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.app.core.db.async_session import get_async_db
from src.app.core.db.base_class import Base
from src.app.core.setup import create_app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for testing.

    Yields:
        Event loop.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create a test database engine.

    Yields:
        Test database engine.
    """
    # Use SQLite for tests with async support
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session.

    Args:
        test_engine: Test database engine.

    Yields:
        Test database session.
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    TestSessionLocal = sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async_session = TestSessionLocal()
    try:
        yield async_session
    finally:
        await async_session.close()
        # Drop tables
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def app(test_db) -> FastAPI:
    """Create a test FastAPI application.

    Args:
        test_db: Test database session.

    Returns:
        Test FastAPI application.
    """
    app = create_app()

    # Override the get_async_db dependency
    async def override_get_async_db():
        yield test_db

    app.dependency_overrides[get_async_db] = override_get_async_db

    return app


@pytest.fixture(scope="function")
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client.

    Args:
        app: Test FastAPI application.

    Yields:
        Test client.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
