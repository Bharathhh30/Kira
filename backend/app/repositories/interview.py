from sqlalchemy.ext.asyncio import AsyncSession
from app.models.interview import Interview
from app.repositories.base import BaseRepository


class InterviewRepository(BaseRepository[Interview]):
    """Repository handling CRUD operations on Interview records."""

    def __init__(self, session: AsyncSession):
        super().__init__(Interview, session)
