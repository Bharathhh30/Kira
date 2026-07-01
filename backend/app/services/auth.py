from datetime import datetime, timedelta, timezone
from app.core import exceptions, security
from app.core.config import settings
from app.models.token import RefreshToken
from app.models.user import User
from app.repositories.token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserLogin


class AuthService:
    def __init__(self, user_repo: UserRepository, token_repo: RefreshTokenRepository):
        self.user_repo = user_repo
        self.token_repo = token_repo

    async def register(self, user_in: UserCreate) -> User:
        """Register a new user."""
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise exceptions.UserAlreadyExistsException()

        hashed_password = security.hash_password(user_in.password)
        new_user = User(
            email=user_in.email.lower(),
            name=user_in.name,
            hashed_password=hashed_password,
        )
        return await self.user_repo.create(new_user)

    async def login(self, login_in: UserLogin) -> Token:
        """Log in a user and return access and refresh tokens."""
        user = await self.user_repo.get_by_email(login_in.email)
        if not user or not user.is_active:
            raise exceptions.InvalidCredentialsException()

        if not security.verify_password(login_in.password, user.hashed_password):
            raise exceptions.InvalidCredentialsException()

        # Generate tokens
        access_token = security.create_access_token(subject=str(user.id))
        raw_refresh_token = security.generate_random_token()

        # Save hashed refresh token in database
        hashed_token = security.hash_refresh_token(raw_refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        token_obj = RefreshToken(
            user_id=user.id,
            hashed_token=hashed_token,
            expires_at=expires_at,
        )
        await self.token_repo.create(token_obj)

        return Token(
            access_token=access_token,
            refresh_token=raw_refresh_token,
        )

    async def refresh_tokens(self, refresh_token: str) -> Token:
        """Refresh tokens using a non-revoked, unexpired refresh token.

        Implements token rotation.
        """
        token_hash = security.hash_refresh_token(refresh_token)
        db_token = await self.token_repo.get_by_token_hash(token_hash)

        if not db_token or db_token.expires_at < datetime.now(timezone.utc):
            raise exceptions.TokenInvalidException("Invalid or expired refresh token")

        # Get user
        user = await self.user_repo.get(db_token.user_id)
        if not user or not user.is_active:
            raise exceptions.TokenInvalidException("User is deactivated")

        # Rotate tokens: revoke the old one, generate new ones
        db_token.is_revoked = True
        await self.token_repo.update(db_token, {"is_revoked": True})

        # Create new tokens
        access_token = security.create_access_token(subject=str(user.id))
        new_raw_refresh_token = security.generate_random_token()
        new_hashed_token = security.hash_refresh_token(new_raw_refresh_token)
        new_expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        new_token_obj = RefreshToken(
            user_id=user.id,
            hashed_token=new_hashed_token,
            expires_at=new_expires_at,
        )
        await self.token_repo.create(new_token_obj)

        return Token(
            access_token=access_token,
            refresh_token=new_raw_refresh_token,
        )

    async def logout(self, refresh_token: str) -> None:
        """Log out a user by revoking the refresh token."""
        token_hash = security.hash_refresh_token(refresh_token)
        await self.token_repo.revoke_by_hash(token_hash)
