import os
import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from app.core.database import async_session_maker
from app.models.resume import Resume
from parser.pipeline.runner import run_pipeline

logger = logging.getLogger(__name__)


class ResumeParserService:
    @staticmethod
    async def parse_resume_background(
        user_id: uuid.UUID, file_bytes: bytes, filename: str
    ) -> None:
        """
        Background task to process the uploaded PDF resume,
        run it through the parser pipeline (with Gemini),
        and store it in the database.
        """
        # Create a temp directory inside the backend folder
        temp_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "temp"
        )
        os.makedirs(temp_dir, exist_ok=True)

        # Save file to temp path
        file_ext = os.path.splitext(filename)[1] or ".pdf"
        temp_file_name = f"{uuid.uuid4()}{file_ext}"
        temp_path = os.path.join(temp_dir, temp_file_name)

        try:
            with open(temp_path, "wb") as f:
                f.write(file_bytes)

            logger.info(
                f"Starting resume parser pipeline for user {user_id} on file {filename}"
            )
            pipeline_result = await run_pipeline(temp_path)

            # Check parser pipeline status
            stage5 = pipeline_result.get("stage5", {})
            validated_data = stage5.get("validated")

            # Fallback to Stage 4 initial parsed output if Stage 5 validation/retry failed
            if not validated_data:
                stage4 = pipeline_result.get("stage4", {})
                if stage4.get("parse_status") == "success":
                    validated_data = stage4.get("parsed")
                    logger.warning(
                        f"Validation/retry failed (status: {stage5.get('parse_status')}). "
                        f"Falling back to initial Stage 4 parsed JSON for user {user_id}."
                    )

            if not validated_data:
                logger.error(
                    f"Resume parsing failed for user {user_id}: {stage5.get('error_details') or 'Validation status failed'}"
                )
                return

            # Store in DB
            async with async_session_maker() as session:
                async with session.begin():
                    # Query existing resume
                    stmt = select(Resume).where(Resume.user_id == user_id)
                    result = await session.execute(stmt)
                    db_resume = result.scalar_one_or_none()

                    if db_resume:
                        db_resume.resume_json = validated_data
                        db_resume.parsed_at = datetime.now(timezone.utc)
                        logger.info(f"Updated existing resume for user {user_id}")
                    else:
                        db_resume = Resume(
                            user_id=user_id,
                            resume_json=validated_data,
                        )
                        session.add(db_resume)
                        logger.info(f"Created new resume record for user {user_id}")

        except Exception as e:
            logger.exception(
                f"Unexpected error in parse_resume_background for user {user_id}: {e}"
            )
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as ce:
                    logger.error(f"Failed to delete temp file {temp_path}: {ce}")
