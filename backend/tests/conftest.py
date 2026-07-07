from collections.abc import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from app.core.config import settings
from app.core.database import get_db_session
from main import app


from app.models.base import Base
from app.models.user import User  # noqa: F401
from app.models.token import RefreshToken  # noqa: F401
from app.models.resume import Resume  # noqa: F401
from app.models.interview import Interview  # noqa: F401


@pytest.fixture(scope="session")
def setup_test_db() -> str:
    """Ensure the test database exists and has all tables initialized."""
    import asyncio

    async def _setup():
        db_url = settings.DATABASE_URL
        if db_url.endswith("/kira"):
            default_db_url = db_url[:-5] + "/postgres"
            test_db_url = db_url[:-5] + "/kira_test"
        else:
            base_url, db_name = db_url.rsplit("/", 1)
            default_db_url = base_url + "/postgres"
            test_db_url = base_url + "/kira_test"

        # Create database if not exists
        init_engine = create_async_engine(default_db_url, isolation_level="AUTOCOMMIT")
        async with init_engine.connect() as conn:
            try:
                await conn.execute(text("CREATE DATABASE kira_test"))
            except Exception:
                pass
        await init_engine.dispose()

        # Create tables
        test_engine = create_async_engine(test_db_url, poolclass=NullPool)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await test_engine.dispose()

        return test_db_url

    return asyncio.run(_setup())


@pytest.fixture(scope="session")
def engine(setup_test_db: str):
    """Create a session-scoped async engine using the test database."""
    engine = create_async_engine(
        setup_test_db,
        echo=False,
        poolclass=NullPool,
    )
    yield engine
    import asyncio

    try:
        asyncio.run(engine.dispose())
    except Exception:
        pass


@pytest.fixture(scope="session")
def session_maker(engine):
    """Create a session-scoped async session maker."""
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
