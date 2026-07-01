from pydantic import ValidationError
from parser.schemas.resume_schema import ResumeOutput


async def validate(llm_output: dict, raw_text: str, merge_output: dict) -> dict:
    """
    Validates LLM output against the Pydantic schema.
    No confidence scoring, no retries, no second API call.
    Returns the validated dict on success, or an error dict on failure.
    """
    if llm_output.get("parse_status") != "success":
        return {
            "validated": None,
            "parse_status": llm_output.get("parse_status", "api_error"),
            "error_details": llm_output.get("reason", "Extraction failed."),
        }

    try:
        model = ResumeOutput(**llm_output["parsed"])
        return {
            "validated": model.model_dump(),
            "parse_status": "success",
        }

    except ValidationError as ve:
        return {
            "validated": None,
            "parse_status": "schema_error",
            "error_details": str(ve),
        }
