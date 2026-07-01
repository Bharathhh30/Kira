import datetime
import logging

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """No-op initialization since we store parsed resumes in Postgres resumes table."""
    pass


async def store(validate_output: dict, candidate_id: str) -> dict:
    """
    Dummy storage function since we store parsed resumes in our Postgres resumes table.
    Returns a success dictionary simulating a completed storage step.
    """
    logger.info(
        f"Stage 6: Skipping SQLite storage for candidate {candidate_id} (storing in Postgres instead)"
    )
    parsed_at = datetime.datetime.now(datetime.timezone.utc)
    return {
        "record_id": candidate_id,
        "parse_status": validate_output.get("parse_status"),
        "stored_at": parsed_at.isoformat(),
    }
