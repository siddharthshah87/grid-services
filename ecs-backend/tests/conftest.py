"""Pytest configuration and shared fixtures for backend tests."""
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Set required environment variables for testing
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "test_user")
os.environ.setdefault("DB_PASSWORD", "test_password")
os.environ.setdefault("DB_NAME", "test_db")
os.environ.setdefault("IOT_ENDPOINT", "test.iot.amazonaws.com")
os.environ.setdefault("AWS_REGION", "us-west-2")


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    yield


@pytest_asyncio.fixture
async def test_engine():
    """Create in-memory test database engine."""
    from app.models import Base
    
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_session):
    """Create test HTTP client with database override."""
    from app.main import app
    from app.dependencies import get_session
    
    async def override_get_session():
        yield test_session
    
    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
