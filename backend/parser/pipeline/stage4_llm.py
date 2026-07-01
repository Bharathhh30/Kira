import re
import json
import logging
import httpx
from parser import config
from parser.schemas.resume_schema import ResumeOutput
from parser.schemas.prompt_template import get_system_prompt

logger = logging.getLogger(__name__)


async def extract_structured(
    merge_output: dict, system_prompt_override: str = None
) -> dict:
    """
    Stage 4: Send merged resume text to Gemini and get structured JSON back.
    Uses plain text generation (no responseSchema) so Gemini fills every field.
    """
    user_payload = {
        "text": merge_output.get("text", ""),
        "embedded_links": merge_output.get("embedded_links", []),
        "metadata": merge_output.get("metadata"),
    }
    user_message = json.dumps(user_payload, indent=2)

    schema_json = json.dumps(ResumeOutput.model_json_schema(), indent=2)
    system_prompt = system_prompt_override or get_system_prompt(schema_json)

    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "your_gemini_api_key_here":
        return {
            "parsed": None,
            "raw_response": None,
            "parse_status": "api_error",
            "reason": "GEMINI_API_KEY is not configured.",
            "provider": "none",
        }

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.GEMINI_MODEL}:generateContent?key={config.GEMINI_API_KEY}"
    )

    payload = {
        "contents": [
            {"parts": [{"text": f"{system_prompt}\n\nResume Details:\n{user_message}"}]}
        ],
        "generationConfig": {
            # Plain JSON text — no responseSchema so Gemini fills every field
            "responseMimeType": "application/json",
        },
    }

    logger.info("Attempting Gemini with model %s", config.GEMINI_MODEL)
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                raise Exception(
                    f"Gemini API returned status {response.status_code}: {response.text}"
                )

            res_json = response.json()
            raw_response = res_json["candidates"][0]["content"]["parts"][0]["text"]
            logger.info("Gemini succeeded")

    except Exception as e:
        logger.exception("Gemini failed")
        return {
            "parsed": None,
            "raw_response": None,
            "parse_status": "api_error",
            "reason": f"Gemini API failed: {e}",
            "provider": "none",
        }

    if not raw_response:
        return {
            "parsed": None,
            "raw_response": raw_response,
            "parse_status": "json_error",
            "reason": "Empty response from Gemini.",
            "provider": "gemini",
        }

    # Strip markdown fences if present
    cleaned = raw_response.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        parsed_dict = json.loads(cleaned)
        return {
            "parsed": parsed_dict,
            "raw_response": raw_response,
            "parse_status": "success",
            "provider": "gemini",
        }
    except Exception as e:
        return {
            "parsed": None,
            "raw_response": raw_response,
            "parse_status": "json_error",
            "reason": str(e),
            "provider": "gemini",
        }
