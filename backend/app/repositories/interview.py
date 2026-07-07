import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.interview import Interview
from app.repositories.base import BaseRepository


class InterviewRepository(BaseRepository[Interview]):
    """Repository handling CRUD operations on Interview records."""

    def __init__(self, session: AsyncSession):
        super().__init__(Interview, session)

    async def get_by_user_id(self, user_id: uuid.UUID) -> list[Interview]:
        """Fetch all interviews for a specific user, ordered by creation time descending."""
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
