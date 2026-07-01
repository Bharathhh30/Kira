import uuid
from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import exceptions, security
from app.core.database import get_db_session
from app.models.user import User
from app.repositories.token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.token import Token, TokenRefreshRequest
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
security_scheme = HTTPBearer()


async def get_auth_service(
    db: AsyncSession = Depends(get_db_session),
) -> AuthService:
    user_repo = UserRepository(db)
    token_repo = RefreshTokenRepository(db)
    return AuthService(user_repo, token_repo)


async def get_current_user(
    db: AsyncSession = Depends(get_db_session),
    token_credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> User:
    token = token_credentials.credentials
    payload = security.decode_access_token(token)
    if not payload:
        raise exceptions.CredentialsException()

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise exceptions.CredentialsException()

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise exceptions.CredentialsException()

    user_repo = UserRepository(db)
    user = await user_repo.get(user_id)
    if not user or not user.is_active:
        raise exceptions.CredentialsException("User not found or deactivated")
    return user


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user account."""
    return await auth_service.register(user_in)


@router.post("/login", response_model=Token)
async def login(
    login_in: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Log in with email and password, returning tokens."""
    return await auth_service.login(login_in)


@router.post("/refresh", response_model=Token)
async def refresh(
    refresh_in: TokenRefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh the access and refresh tokens using token rotation."""
    return await auth_service.refresh_tokens(refresh_in.refresh_token)


@router.post("/logout", status_code=204)
async def logout(
    refresh_in: TokenRefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Revoke a refresh token upon user logout."""
    await auth_service.logout(refresh_in.refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Retrieve the current logged-in user profile."""
    return current_user
