import uuid
import logging
import httpx
import json
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
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
                granular_scores=h.get("granular_scores"),
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
            report=db_interview.report,
        )

        # 4. Process response using InterviewManager
        manager = InterviewManager()
        await manager.process_answer(state, answer)

        # 5. Generate final report if completed
        report_data = db_interview.report
        if state.is_completed and not report_data:
            report_data = await self.generate_final_report(state)

        # 6. Map updated fields back to DB
        updated_fields = {
            "current_topic": state.current_topic,
            "remaining_topics": state.remaining_topics,
            "current_question": state.current_question,
            "follow_up_count": state.follow_up_count,
            "history": [h.model_dump(mode="json") for h in state.history],
            "remaining_time": state.remaining_time,
            "is_completed": state.is_completed,
            "report": report_data,
        }

        return await self.interview_repo.update(db_interview, updated_fields)

    async def generate_final_report(self, state: InterviewState) -> dict:
        """
        Generates a summary final performance report by calling the Gemini API.
        """
        logger = logging.getLogger("kira-interview-report")
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("GEMINI_API_KEY not configured. Generating static fallback report.")
            return self._generate_fallback_report(state)

        # Build prompt listing the entire history of questions, answers, and scores
        history_text = ""
        for idx, entry in enumerate(state.history):
            history_text += (
                f"Exchange #{idx+1}:\n"
                f"Question: {entry.question}\n"
                f"Answer: {entry.answer or 'N/A'}\n"
                f"Score: {entry.score or 0.0}\n"
                f"Feedback: {entry.feedback or ''}\n\n"
            )

        prompt = (
            "You are an expert technical interviewer compiling a final performance report for a mock interview.\n\n"
            "Here is the dialogue history and feedback for each question-answer exchange:\n"
            f"{history_text}\n"
            "Based on the dialogue history, compile a comprehensive evaluation report.\n"
            "You must return a valid JSON object matching the following structure:\n"
            "{\n"
            "  \"summary\": \"Overall performance summary (2-3 sentences summarizing key metrics, domain knowledge, and highlights).\",\n"
            "  \"strengths\": [\n"
            "    \"Strength 1 (specific detail from answers)\",\n"
            "    \"Strength 2\"\n"
            "  ],\n"
            "  \"weaknesses\": [\n"
            "    \"Area for improvement 1 (specific gap or detail that was missed)\",\n"
            "    \"Area for improvement 2\"\n"
            "  ],\n"
            "  \"granular_averages\": {\n"
            "    \"communication\": float, // Average communication score from 0.0 to 1.0\n"
            "    \"accuracy\": float, // Average accuracy score from 0.0 to 1.0\n"
            "    \"confidence\": float, // Average confidence score from 0.0 to 1.0\n"
            "    \"completeness\": float // Average completeness score from 0.0 to 1.0\n"
            "  }\n"
            "}"
        )

        models = [settings.GEMINI_MODEL, "gemini-2.5-flash"]
        if settings.GEMINI_MODEL not in models:
            models.insert(0, settings.GEMINI_MODEL)

        payload = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
            },
        }

        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    response = await client.post(url, json=payload)
                    if response.status_code == 200:
                        res_json = response.json()
                        raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                        parsed = json.loads(raw_text.strip())
                        return parsed
            except Exception as e:
                logger.exception(f"Failed to generate report with model {model}: {e}")

        logger.warning("All Gemini report models failed. Generating static fallback report.")
        return self._generate_fallback_report(state)

    def _generate_fallback_report(self, state: InterviewState) -> dict:
        # Calculate averages locally
        comm_scores = []
        acc_scores = []
        conf_scores = []
        comp_scores = []
        
        for entry in state.history:
            if entry.granular_scores:
                comm_scores.append(entry.granular_scores.communication)
                acc_scores.append(entry.granular_scores.accuracy)
                conf_scores.append(entry.granular_scores.confidence)
                comp_scores.append(entry.granular_scores.completeness)
                
        avg_comm = sum(comm_scores) / len(comm_scores) if comm_scores else 0.8
        avg_acc = sum(acc_scores) / len(acc_scores) if acc_scores else 0.8
        avg_conf = sum(conf_scores) / len(conf_scores) if conf_scores else 0.8
        avg_comp = sum(comp_scores) / len(comp_scores) if comp_scores else 0.8

        return {
            "summary": "The candidate has completed the mock interview. Good performance overall across all syllabus topics.",
            "strengths": ["Demonstrates basic knowledge of the selected topics", "Completed the interview within the time limit"],
            "weaknesses": ["Could provide more detailed examples in technical responses"],
            "granular_averages": {
                "communication": avg_comm,
                "accuracy": avg_acc,
                "confidence": avg_conf,
                "completeness": avg_comp
            }
        }

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
