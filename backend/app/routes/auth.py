from fastapi import (
    APIRouter,
    Depends,
    Response,
    Cookie,
    BackgroundTasks,
    UploadFile,
    HTTPException,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.core import exceptions, security
from app.core.config import settings
from app.core.database import get_db_session
from app.models.user import User
from app.models.resume import Resume
from app.repositories.token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.token import AccessTokenResponse
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.resume import ResumeResponse
from app.services.auth import AuthService
from app.services.parser import ResumeParserService

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


@router.post("/login", response_model=AccessTokenResponse)
async def login(
    response: Response,
    login_in: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Log in with email and password, returning access token and setting HttpOnly cookie."""
    token_data = await auth_service.login(login_in)
    response.set_cookie(
        key="refresh_token",
        value=token_data.refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/auth",
    )
    return AccessTokenResponse(
        access_token=token_data.access_token,
        token_type=token_data.token_type,
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh the access and refresh tokens using token rotation."""
    if not refresh_token:
        raise exceptions.CredentialsException("Missing refresh token")

    token_data = await auth_service.refresh_tokens(refresh_token)
    response.set_cookie(
        key="refresh_token",
        value=token_data.refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/auth",
    )
    return AccessTokenResponse(
        access_token=token_data.access_token,
        token_type=token_data.token_type,
    )


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Revoke a refresh token upon user logout."""
    if refresh_token:
        await auth_service.logout(refresh_token)
    response.delete_cookie(
        key="refresh_token",
        path="/api/auth",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Retrieve the current logged-in user profile."""
    return current_user


@router.post("/resume", status_code=202)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
):
    """Upload a resume PDF, processing it asynchronously in the background."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()
    background_tasks.add_task(
        ResumeParserService.parse_resume_background,
        current_user.id,
        file_bytes,
        file.filename,
    )
    return {"message": "Resume upload accepted. Processing in background."}


@router.get("/resume", response_model=ResumeResponse)
async def get_resume(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Retrieve the current user's parsed resume."""
    stmt = select(Resume).where(Resume.user_id == current_user.id)
    result = await db.execute(stmt)
    db_resume = result.scalar_one_or_none()
    if not db_resume:
        raise HTTPException(status_code=404, detail="No resume has been uploaded yet.")
    return db_resume
