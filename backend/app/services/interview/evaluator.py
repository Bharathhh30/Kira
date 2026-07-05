import json
import logging
import httpx
from pydantic import BaseModel
from app.core.config import settings
from app.schemas.interview import GranularScores

logger = logging.getLogger(__name__)


class EvaluationResult(BaseModel):
    """Result of evaluating a user response."""

    score: float
    follow_up: bool
    reason: str
    move_next: bool
    granular_scores: GranularScores


class InterviewEvaluator:
    """Evaluates candidate responses using Gemini API with fallback providers."""

    @staticmethod
    async def evaluate_response(answer: str, current_question: str) -> EvaluationResult:
        """
        Calls Gemini model (primary: gemini-3.1-flash-lite, fallback: gemini-2.5-flash)
        to evaluate candidate's response.
        If both fail, falls back to local rule-based heuristics.
        """
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("GEMINI_API_KEY is not configured. Using local fallback.")
            return InterviewEvaluator._fallback_evaluation(answer)

        models = [settings.GEMINI_MODEL, "gemini-2.5-flash"]
        # De-duplicate settings model and fallback model
        if settings.GEMINI_MODEL not in models:
            models.insert(0, settings.GEMINI_MODEL)

        prompt = (
            "You are an expert technical interviewer evaluating a candidate's response to a question.\n\n"
            f"Question: {current_question}\n"
            f"Candidate's Answer: {answer}\n\n"
            "Perform a rigorous evaluation of the candidate's answer.\n"
            "Determine if the answer is complete, technically accurate, clear, and confident.\n"
            "If the answer lacks technical depth, is incorrect, or requires elaboration, set `follow_up` to true and `move_next` to false.\n"
            "Otherwise, if the answer is satisfactory and addresses the question sufficiently, set `follow_up` to false and `move_next` to true.\n\n"
            "Provide scores from 0.0 to 1.0 (float) for each of the following:\n"
            "- `communication`: clarity, structure, and verbal articulation.\n"
            "- `accuracy`: technical correctness and truth of facts.\n"
            "- `confidence`: certainty and tone of the explanation.\n"
            "- `completeness`: addressing all aspects/requirements of the question.\n\n"
            "Also calculate the overall `score` as a float between 0.0 to 1.0 (usually an average of the four granular metrics).\n\n"
            "You must return a valid JSON object matching the following structure:\n"
            "{\n"
            "  \"score\": float,\n"
            "  \"follow_up\": boolean,\n"
            "  \"reason\": \"feedback explaining the strengths/weaknesses and transition decision\",\n"
            "  \"move_next\": boolean,\n"
            "  \"granular_scores\": {\n"
            "    \"communication\": float,\n"
            "    \"accuracy\": float,\n"
            "    \"confidence\": float,\n"
            "    \"completeness\": float\n"
            "  }\n"
            "}"
        )

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
            logger.info(f"Attempting response evaluation with Gemini model: {model}")
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, json=payload)
                    if response.status_code == 200:
                        res_json = response.json()
                        raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                        parsed = json.loads(raw_text.strip())
                        
                        # Validate structure
                        scores = parsed["granular_scores"]
                        return EvaluationResult(
                            score=parsed["score"],
                            follow_up=parsed["follow_up"],
                            reason=parsed["reason"],
                            move_next=parsed["move_next"],
                            granular_scores=GranularScores(
                                communication=scores["communication"],
                                accuracy=scores["accuracy"],
                                confidence=scores["confidence"],
                                completeness=scores["completeness"]
                            )
                        )
                    else:
                        logger.warning(f"Gemini {model} returned code {response.status_code}: {response.text}")
            except Exception as e:
                logger.exception(f"Gemini evaluation failed for model {model}: {e}")

        logger.error("All Gemini evaluation models failed. Using local fallback.")
        return InterviewEvaluator._fallback_evaluation(answer)

    @staticmethod
    def _fallback_evaluation(answer: str) -> EvaluationResult:
        trimmed = answer.strip()
        if len(trimmed) < 20:
            return EvaluationResult(
                score=0.4,
                follow_up=True,
                reason="Answer is too short (< 20 characters). Requesting elaboration. (Local Fallback)",
                move_next=False,
                granular_scores=GranularScores(
                    communication=0.5,
                    accuracy=0.4,
                    confidence=0.4,
                    completeness=0.3
                )
            )
        else:
            return EvaluationResult(
                score=0.8,
                follow_up=False,
                reason="Answer is sufficient in length. Proceeding to next question. (Local Fallback)",
                move_next=True,
                granular_scores=GranularScores(
                    communication=0.8,
                    accuracy=0.8,
                    confidence=0.8,
                    completeness=0.8
                )
            )
