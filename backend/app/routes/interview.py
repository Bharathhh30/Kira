import logging
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from livekit import api
from app.core.config import settings
from app.core.database import get_db_session
from app.models.user import User
from app.repositories.interview import InterviewRepository
from app.routes.auth import get_current_user
from app.schemas.interview import (
    InterviewAnswerRequest,
    InterviewResponse,
    InterviewStartRequest,
    InterviewTokenResponse,
)
from app.services.interview.service import InterviewService

router = APIRouter(prefix="/interview", tags=["interview"])


async def get_interview_service(
    db: AsyncSession = Depends(get_db_session),
) -> InterviewService:
    interview_repo = InterviewRepository(db)
    return InterviewService(interview_repo, db)


@router.post("/start", response_model=InterviewResponse, status_code=201)
async def start_interview(
    request: InterviewStartRequest,
    current_user: User = Depends(get_current_user),
    service: InterviewService = Depends(get_interview_service),
):
    """Initiates a new technical mock interview session."""
    return await service.start_interview(
        user_id=current_user.id, mode=request.interview_mode
    )


@router.post("/next/{interview_id}", response_model=InterviewResponse)
async def process_answer(
    interview_id: uuid.UUID,
    request: InterviewAnswerRequest,
    current_user: User = Depends(get_current_user),
    service: InterviewService = Depends(get_interview_service),
):
    """Processes candidate's response to the active question and updates state."""
    return await service.process_answer(
        interview_id=interview_id, answer=request.answer, user_id=current_user.id
    )


@router.get("/state/{interview_id}", response_model=InterviewResponse)
async def get_interview_state(
    interview_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: InterviewService = Depends(get_interview_service),
):
    """Retrieves current state/details of an interview session."""
    return await service.get_interview_state(
        interview_id=interview_id, user_id=current_user.id
    )


_route_logger = logging.getLogger("kira.routes.interview")


@router.post("/token/{interview_id}", response_model=InterviewTokenResponse)
async def get_token(
    interview_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
):
    """Generates a signed LiveKit connection token and dispatches the voice agent to the room."""
    room_name = str(interview_id)

    # Generate participant access token
    token = api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
    token.with_identity(f"user-{current_user.id}")
    token.with_name(current_user.name)
    token.with_grants(api.VideoGrants(room_join=True, room=room_name))

    # Explicitly dispatch the agent to the room (ensures re-dispatch after crashes)
    lk_api = api.LiveKitAPI(
        url=settings.LIVEKIT_URL,
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET,
    )
    async with lk_api:
        try:
            dispatch = await lk_api.agent_dispatch.create_dispatch(
                api.CreateAgentDispatchRequest(room=room_name, agent_name="")
            )
            _route_logger.info(f"Agent dispatched to room {room_name}: {dispatch}")
        except Exception as e:
            # Non-fatal — agent may already be running in the room
            _route_logger.warning(f"Agent dispatch skipped for room {room_name}: {e}")

    return InterviewTokenResponse(token=token.to_jwt(), server_url=settings.LIVEKIT_URL)
