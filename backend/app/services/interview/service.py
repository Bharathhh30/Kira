import uuid
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.interview import Interview
from app.models.resume import Resume
from app.repositories.interview import InterviewRepository
from app.schemas.interview import InterviewHistoryEntry, InterviewState
from app.services.interview.context_loader import ContextLoader
from app.services.interview.manager import InterviewManager


class InterviewService:
    """Orchestrates starting, retrieving, and stepping through interview sessions."""

    def __init__(self, interview_repo: InterviewRepository, db_session: AsyncSession):
        self.interview_repo = interview_repo
        self.db = db_session

    async def start_interview(
        self, user_id: uuid.UUID, mode: str = "resume"
    ) -> Interview:
        """Starts a new interview session by loading resume data and initializing state."""
        # 1. Fetch user's resume
        stmt = select(Resume).where(Resume.user_id == user_id)
        res = await self.db.execute(stmt)
        db_resume = res.scalar_one_or_none()
        if not db_resume:
            raise HTTPException(
                status_code=400,
                detail="Please upload your resume to start mock interviews.",
            )

        # 2. Call ContextLoader
        initial_state = ContextLoader.load_context(
            user_id=user_id,
            resume_json=db_resume.resume_json,
            interview_mode=mode,
        )

        # 3. Create database object
        db_interview = Interview(
            user_id=user_id,
            current_topic=initial_state.current_topic,
            remaining_topics=initial_state.remaining_topics,
            current_question=initial_state.current_question,
            follow_up_count=initial_state.follow_up_count,
            history=[],
            remaining_time=initial_state.remaining_time,
            interview_mode=initial_state.interview_mode,
            is_completed=initial_state.is_completed,
        )

        return await self.interview_repo.create(db_interview)

    async def process_answer(
        self, interview_id: uuid.UUID, answer: str, user_id: uuid.UUID
    ) -> Interview:
        """Processes candidate answer, evaluates it, and updates DB record."""
        # 1. Fetch active interview
        db_interview = await self.interview_repo.get(interview_id)
        if not db_interview:
            raise HTTPException(status_code=404, detail="Interview session not found.")
        if db_interview.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied.")
        if db_interview.is_completed:
            raise HTTPException(
                status_code=400, detail="This interview has already been completed."
            )

        # 2. Fetch resume JSON
        stmt = select(Resume).where(Resume.user_id == user_id)
        res = await self.db.execute(stmt)
        db_resume = res.scalar_one_or_none()
        resume_json = db_resume.resume_json if db_resume else {}

        # 3. Reconstruct Pydantic state
        history_list = [
            InterviewHistoryEntry(
                question=h["question"],
                answer=h.get("answer"),
                score=h.get("score"),
                feedback=h.get("feedback"),
                # Parse timestamp if exists, otherwise handled by default factory
            )
            for h in db_interview.history
        ]

        state = InterviewState(
            interview_id=db_interview.id,
            user_id=db_interview.user_id,
            resume_json=resume_json,
            current_topic=db_interview.current_topic,
            remaining_topics=db_interview.remaining_topics,
            current_question=db_interview.current_question,
            follow_up_count=db_interview.follow_up_count,
            history=history_list,
            remaining_time=db_interview.remaining_time,
            interview_mode=db_interview.interview_mode,
            is_completed=db_interview.is_completed,
        )

        # 4. Process response using InterviewManager
        manager = InterviewManager()
        manager.process_answer(state, answer)

        # 5. Map updated fields back to DB
        updated_fields = {
            "current_topic": state.current_topic,
            "remaining_topics": state.remaining_topics,
            "current_question": state.current_question,
            "follow_up_count": state.follow_up_count,
            "history": [h.model_dump(mode="json") for h in state.history],
            "remaining_time": state.remaining_time,
            "is_completed": state.is_completed,
        }

        return await self.interview_repo.update(db_interview, updated_fields)

    async def get_interview_state(
        self, interview_id: uuid.UUID, user_id: uuid.UUID
    ) -> Interview:
        """Retrieves an active or completed interview session."""
        db_interview = await self.interview_repo.get(interview_id)
        if not db_interview:
            raise HTTPException(status_code=404, detail="Interview session not found.")
        if db_interview.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied.")
        return db_interview
