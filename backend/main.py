from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine
from app.routes.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify database connection before starting the server
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("Database connection check: SUCCESS")
    except Exception as e:
        print(f"Database connection check: FAILED. Error: {e}")
        raise RuntimeError(f"Database is not accessible: {e}") from e
    yield
    # Clean up connection pool on shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def read_root() -> dict[str, str]:
    """Base check endpoint."""
    return {"status": "ok", "message": "Welcome to Kira API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
