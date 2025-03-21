"""Test configuration module."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.app.core.config import settings
from src.app.core.db.base_class import Base
from src.app.core.db.session import get_db
from src.app.core.setup import create_app

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


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
def test_engine():
    """Create a test database engine.

    Yields:
        Test database engine.
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine) -> Generator[Session, None, None]:
    """Create a test database session.

    Args:
        test_engine: Test database engine.

    Yields:
        Test database session.
    """
    # Create tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    TestSessionLocal = sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop tables
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def app(test_db) -> FastAPI:
    """Create a test FastAPI application.

    Args:
        test_db: Test database session.

    Returns:
        Test FastAPI application.
    """
    app = create_app()

    # Override the get_db dependency
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    return app


@pytest.fixture(scope="function")
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client.

    Args:
        app: Test FastAPI application.

    Yields:
        Test client.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
