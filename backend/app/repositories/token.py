import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, session: AsyncSession):
        super().__init__(RefreshToken, session)

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        """Fetch a non-revoked refresh token by its SHA-256 hash."""
        query = select(RefreshToken).where(
            RefreshToken.hashed_token == token_hash,
            RefreshToken.is_revoked.is_(False),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def revoke_by_hash(self, token_hash: str) -> bool:
        """Revoke a specific refresh token by marking it as revoked."""
        token = await self.get_by_token_hash(token_hash)
        if token:
            token.is_revoked = True
            self.session.add(token)
            await self.session.commit()
            return True
        return False

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        """Revoke all active refresh tokens for a given user."""
        query = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked.is_(False),
        )
        result = await self.session.execute(query)
        tokens = result.scalars().all()
        for token in tokens:
            token.is_revoked = True
            self.session.add(token)
        if tokens:
            await self.session.commit()
        return len(tokens)

    async def delete_expired(self) -> int:
        """Clean up physically expired refresh tokens from the database."""
        now = datetime.now(timezone.utc)
        query = select(RefreshToken).where(RefreshToken.expires_at < now)
        result = await self.session.execute(query)
        expired_tokens = result.scalars().all()
        for token in expired_tokens:
            await self.session.delete(token)
        if expired_tokens:
            await self.session.commit()
        return len(expired_tokens)
