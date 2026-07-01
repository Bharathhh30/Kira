import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ResumeResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    resume_json: dict
    parsed_at: datetime

    model_config = ConfigDict(from_attributes=True)
