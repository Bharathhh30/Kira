from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        """Retrieve user by their email address."""
        query = select(User).where(User.email == email.lower())
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def soft_delete(self, id: Any) -> User | None:
        """Deactivate/soft delete a user."""
        user = await self.get(id)
        if user:
            user.is_active = False
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        return user
