import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://kira:kira_password@localhost:5432/kira"


async def reset():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        # Drop all tables in the public schema
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO kira;"))
    print("Database reset successfully.")


if __name__ == "__main__":
    asyncio.run(reset())
