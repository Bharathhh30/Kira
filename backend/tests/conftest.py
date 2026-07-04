from collections.abc import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from app.core.config import settings
from app.core.database import get_db_session
from main import app


@pytest.fixture
async def engine():
    """Create a function-scoped async engine."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest.fixture
def session_maker(engine):
    """Create a function-scoped async session maker."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
async def db_session(
    session_maker,
) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session after truncating tables to ensure test isolation."""
    async with session_maker() as session:
        # Clear database tables before each test
        await session.execute(text("TRUNCATE TABLE resumes CASCADE;"))
        await session.execute(text("TRUNCATE TABLE interviews CASCADE;"))
        await session.execute(text("TRUNCATE TABLE refresh_tokens CASCADE;"))
        await session.execute(text("TRUNCATE TABLE users CASCADE;"))
        await session.commit()

        yield session
        await session.close()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTPX AsyncClient with database session overridden."""

    def override_get_db_session():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client

    app.dependency_overrides.clear()
