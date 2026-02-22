"""
Pytest configuration and fixtures for BioLink API tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.database import engine
from app.db_bootstrap import ensure_schema


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Set up test database schema."""
    ensure_schema(engine)
    yield
    # Cleanup after tests if needed


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client for synchronous tests."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers() -> dict:
    """Get authentication headers for testing."""
    # This would normally get a real token
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def sample_patient_data() -> dict:
    """Sample patient data for testing."""
    return {
        "dna_id": "TEST001",
        "age": 45,
        "gender": "M",
        "current_city": "Cairo",
        "enrollment_date": "2024-01-15",
    }
