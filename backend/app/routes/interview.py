import asyncio
import logging
import uuid
import time
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

# In-memory cache to prevent duplicate dispatches in quick succession
# Room name -> timestamp
RECENT_DISPATCHES: dict[str, float] = {}
dispatch_lock = asyncio.Lock()


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
        user_id=current_user.id,
        mode=request.interview_mode,
        job_description=request.job_description,
        company_name=request.company_name,
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


@router.post("/end/{interview_id}", response_model=InterviewResponse)
async def end_interview_early(
    interview_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: InterviewService = Depends(get_interview_service),
):
    """Forces the active mock interview session to complete early and generates the report."""
    return await service.end_interview_early(
        interview_id=interview_id, user_id=current_user.id
    )


@router.get("/list", response_model=list[InterviewResponse])
async def list_interviews(
    current_user: User = Depends(get_current_user),
    service: InterviewService = Depends(get_interview_service),
):
    """Retrieves all mock interview sessions for the current user."""
    return await service.list_interviews(user_id=current_user.id)


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
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Generates a signed LiveKit connection token and dispatches the voice agent to the room."""
    room_name = str(interview_id)

    # Generate participant access token
    token = api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
    token.with_identity(f"user-{current_user.id}")
    token.with_name(current_user.name)
    token.with_grants(api.VideoGrants(room_join=True, room=room_name))

    # Fetch interview row with row-level write lock to prevent race conditions
    from sqlalchemy import select
    from app.models.interview import Interview

    should_dispatch = False
    current_time = time.time()
    try:
        # with_for_update blocks concurrent transactions from reading this row
        stmt = select(Interview).where(Interview.id == interview_id).with_for_update()
        res = await db.execute(stmt)
        db_interview = res.scalar_one_or_none()

        if db_interview:
            report_dict = db_interview.report or {}
            last_dispatched = report_dict.get("agent_dispatched_at", 0.0)

            if current_time - last_dispatched < 15.0:
                should_dispatch = False
                _route_logger.info(
                    f"Agent already recently dispatched in DB for room {room_name}. Skipping dispatch."
                )
            else:
                should_dispatch = True
                # Record dispatch timestamp in database immediately
                report_dict["agent_dispatched_at"] = current_time
                db_interview.report = report_dict
                await db.commit()
        else:
            _route_logger.warning(f"Interview {interview_id} not found in DB.")
    except Exception as dbe:
        _route_logger.warning(f"Failed database dispatch synchronization: {dbe}")
        # Fallback to local memory cache if database lock fails
        should_dispatch = True

    if should_dispatch:
        # Check active participants list on LiveKit as a final safeguard
        lk_api = api.LiveKitAPI(
            url=settings.LIVEKIT_URL,
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
        )
        async with lk_api:
            try:
                # Clean up expired dispatches in local cache
                for r_name in list(RECENT_DISPATCHES.keys()):
                    if current_time - RECENT_DISPATCHES[r_name] > 15.0:
                        RECENT_DISPATCHES.pop(r_name, None)

                has_agent = False
                try:
                    participants_res = await lk_api.room.list_participants(
                        api.ListParticipantsRequest(room=room_name)
                    )
                    for p in participants_res.participants:
                        if p.identity.startswith("agent-"):
                            has_agent = True
                            break
                except Exception as le:
                    _route_logger.warning(
                        f"Could not check participants list for room {room_name}: {le}"
                    )

                if not has_agent and room_name not in RECENT_DISPATCHES:
                    RECENT_DISPATCHES[room_name] = current_time
                    dispatch = await lk_api.agent_dispatch.create_dispatch(
                        api.CreateAgentDispatchRequest(room=room_name, agent_name="")
                    )
                    _route_logger.info(
                        f"Agent dispatched to room {room_name}: {dispatch}"
                    )
                else:
                    _route_logger.info(
                        f"Agent already present or recently dispatched to room {room_name}. Skipping dispatch."
                    )
            except Exception as e:
                _route_logger.warning(
                    f"Agent dispatch skipped for room {room_name}: {e}"
                )

    return InterviewTokenResponse(token=token.to_jwt(), server_url=settings.LIVEKIT_URL)
