import uuid
from typing import Any, Dict, Optional
from app.schemas.interview import InterviewState


class ContextLoader:
    """Service to load interview contexts from user resumes and settings."""

    @staticmethod
    def load_context(
        user_id: uuid.UUID,
        resume_json: Dict[str, Any],
        interview_mode: str = "resume",
        interview_id: Optional[uuid.UUID] = None,
        custom_topics: Optional[list[str]] = None,
    ) -> InterviewState:
        """Initializes the InterviewState based on user resume data and settings."""
        if custom_topics:
            all_topics = list(custom_topics)
        else:
            # Find starting topic and populate remaining topics
            skills = resume_json.get("skills", {})
            tech_skills = list(skills.get("technical", []))

            projects = [
                p.get("name") for p in resume_json.get("projects", []) if p.get("name")
            ]
            experience = [
                e.get("company")
                for e in resume_json.get("experience", [])
                if e.get("company")
            ]

            all_topics = []
            if tech_skills:
                all_topics.extend(tech_skills)
            if projects:
                all_topics.extend([f"Project: {p}" for p in projects])
            if experience:
                all_topics.extend([f"Experience at {e}" for e in experience])

        if not all_topics:
            all_topics = ["General Software Engineering"]

        if interview_mode == "resume" and not custom_topics:
            initial_topic = "Topic Selection"
            remaining = []
            skills = resume_json.get("skills", {})
            tech_skills = list(skills.get("technical", []))
            skills_display = (
                ", ".join(tech_skills[:4]) if tech_skills else "programming"
            )
            initial_question = (
                f"Hello! I see you have experience with several technologies, such as {skills_display} "
                "on your profile. Which programming language or technology would you like to focus on for this mock interview today?"
            )
        else:
            initial_topic = all_topics[0]
            remaining = all_topics[1:]

            # Set a starter question
            if interview_mode == "behavioral":
                initial_question = (
                    f"Hello! Let's start with a scenario on {initial_topic}. "
                    "Could you describe a situation from your past experience where you had to handle this?"
                )
            else:
                initial_question = (
                    f"Hello! I see we are discussing {initial_topic} in this mock session. "
                    "Could you explain a project or experience where you used it and what challenges you faced?"
                )

        return InterviewState(
            interview_id=interview_id or uuid.uuid4(),
            user_id=user_id,
            resume_json=resume_json,
            current_topic=initial_topic,
            remaining_topics=remaining,
            current_question=initial_question,
            follow_up_count=0,
            interview_mode=interview_mode,
            remaining_time=1800,  # 30 minutes in seconds
            is_completed=False,
        )
