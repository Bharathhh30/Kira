import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class InterviewHistoryEntry(BaseModel):
    """Represents a single question and answer exchange within an interview."""

    question: str
    answer: Optional[str] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InterviewState(BaseModel):
    """Holds the current active state of an interview session."""

    interview_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    resume_json: Dict[str, Any]
    current_topic: Optional[str] = None
    remaining_topics: List[str] = Field(default_factory=list)
    current_question: Optional[str] = None
    follow_up_count: int = 0
    history: List[InterviewHistoryEntry] = Field(default_factory=list)
    remaining_time: int = 1800  # Default 30 minutes in seconds
    interview_mode: str = "resume"
    is_completed: bool = False


class InterviewStartRequest(BaseModel):
    """Request payload to initiate a new interview session."""

    interview_mode: str = "resume"


class InterviewAnswerRequest(BaseModel):
    """Request payload submitting candidate's response to the active question."""

    answer: str


class InterviewResponse(BaseModel):
    """Response payload detailing the active state of an interview."""

    id: uuid.UUID
    user_id: uuid.UUID
    current_topic: Optional[str] = None
    remaining_topics: List[str] = []
    current_question: Optional[str] = None
    follow_up_count: int
    history: List[InterviewHistoryEntry] = []
    remaining_time: int
    interview_mode: str
    is_completed: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewTokenResponse(BaseModel):
    """Response payload containing LiveKit access token."""

    token: str
    server_url: str
