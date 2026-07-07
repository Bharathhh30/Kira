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
    follow_up_question: str | None = None
    transition_question: str | None = None
    action: str = "FOLLOW_UP"


class InterviewEvaluator:
    """Evaluates candidate responses using Gemini API with fallback providers."""

    @staticmethod
    async def evaluate_response(
        answer: str,
        current_question: str,
        current_topic: str = "",
        next_topic: str | None = None,
    ) -> EvaluationResult:
        """
        Calls Gemini model (primary: gemini-3.1-flash-lite, fallback: gemini-2.5-flash)
        to evaluate candidate's response.
        If both fail, falls back to local rule-based heuristics.
        """
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("GEMINI_API_KEY is not configured. Using local fallback.")
            return InterviewEvaluator._fallback_evaluation(
                answer, current_topic, next_topic
            )

        models = [settings.GEMINI_MODEL, "gemini-2.5-flash"]
        # De-duplicate settings model and fallback model
        if settings.GEMINI_MODEL not in models:
            models.insert(0, settings.GEMINI_MODEL)

        prompt = (
            "You are an expert technical interviewer evaluating a candidate's response to a question.\n"
            "The candidate is a college student looking for entry-level positions or internships, so evaluate them accordingly. "
            "Focus on their core understanding of programming fundamentals, logical reasoning, and academic/personal project experience rather than enterprise industry standards.\n\n"
            f"Question: {current_question}\n"
            f"Candidate's Answer: {answer}\n\n"
            "Perform a rigorous evaluation of the candidate's answer.\n"
            "Determine if the answer is complete, technically accurate, clear, and confident.\n\n"
            "First, determine the conversation `action` to take. Choose exactly one of the following:\n"
            "- `REPEAT`: if the candidate asked to repeat the question, clarify the question, complained they didn't hear it, or their response indicates they didn't understand the question (e.g., 'Sorry I did not get you', 'can you say that again?', 'I didn't understand').\n"
            "- `SKIP`: if the candidate explicitly states they don't know the answer, wants to skip the topic, or requests to move to the next area.\n"
            "- `FOLLOW_UP`: if the candidate answered but their response lacks depth, is partially incorrect, or requires probing on the current topic.\n"
            "- `TRANSITION`: if the candidate answered the question sufficiently and we should move to the next topic.\n\n"
            "Based on the chosen action, set `follow_up` and `move_next` as follows:\n"
            "- For `REPEAT`: set `follow_up` to true and `move_next` to false.\n"
            "- For `SKIP`: set `follow_up` to false and `move_next` to true.\n"
            "- For `FOLLOW_UP`: set `follow_up` to true and `move_next` to false.\n"
            "- For `TRANSITION`: set `follow_up` to false and `move_next` to true.\n\n"
            "Also:\n"
            "1. If `action` is `REPEAT`, generate a rephrased or clarified version of the question (`follow_up_question`) to help them understand it. Do not just repeat it word-for-word.\n"
            "2. If `action` is `FOLLOW_UP`, generate a dynamic, highly contextual technical follow-up question (`follow_up_question`) to probe on the candidate's answer. The question should follow the natural flow of conversation, ask about specific technical concepts they mentioned or missed, and help them expand. "
            "Since the candidate is a student/recent graduate, tailor the question to academic concepts, personal projects, or fundamental design patterns they might have encountered, avoiding industry-heavy enterprise scenarios. "
            "DO NOT use generic phrases like 'Could you please elaborate' or 'tell me more'. Ask a direct technical follow-up question instead.\n"
            f"3. If `action` is `TRANSITION` or `SKIP`, generate a transitional question (`transition_question`) to introduce the next topic. If a next topic is provided (next topic: '{next_topic or ''}'), bridge the conversation to it naturally, focusing on how they might apply Y in projects or their coursework (e.g. 'Great explanation of X. Let's move on to Y. How have you used Y in your coursework or personal projects?'). If no next topic is provided, generate a final concluding sentence.\n"
            "4. For technical follow-up (`follow_up_question`) or transition (`transition_question`) questions, if it makes sense to have the candidate review, debug, optimize, or predict the output of a code snippet, you can append a short code block to the question using a `|||` separator (e.g. 'Looking at the `mystery` function in the snippet, what will it return for x=5, and how would you optimize it? ||| def mystery(x):\n  return x * 2'). Place the question text BEFORE the `|||` and the raw code snippet AFTER the `|||`. Only do this when highly relevant for technical assessment, and keep snippets under 10 lines of clean code. "
            "CRITICAL: If a code snippet is generated, the question text MUST explicitly reference it, using phrases like 'Refer to the code snippet on the screen...', 'Looking at the code block...', or mentioning specific function/variable names from the snippet. The question and code block MUST be tightly interlinked.\n\n"
            "Provide scores from 0.0 to 1.0 (float) for each of the following:\n"
            "- `communication`: clarity, structure, and verbal articulation.\n"
            "- `accuracy`: technical correctness and truth of facts.\n"
            "- `confidence`: certainty and tone of the explanation.\n"
            "- `completeness`: addressing all aspects/requirements of the question.\n\n"
            "Also calculate the overall `score` as a float between 0.0 to 1.0 (usually an average of the four granular metrics). If the action is REPEAT or SKIP, assign a reasonable default score (e.g. 1.0 for REPEAT, or 0.2 for SKIP).\n\n"
            "You must return a valid JSON object matching the following structure:\n"
            "{\n"
            '  "score": float,\n'
            '  "follow_up": boolean,\n'
            '  "reason": "feedback explaining the strengths/weaknesses and transition decision",\n'
            '  "move_next": boolean,\n'
            '  "action": "REPEAT" | "SKIP" | "FOLLOW_UP" | "TRANSITION",\n'
            '  "follow_up_question": "dynamic rephrased or probe question, or null if action is TRANSITION or SKIP",\n'
            '  "transition_question": "dynamic transition question, or null if action is FOLLOW_UP or REPEAT",\n'
            '  "granular_scores": {\n'
            '    "communication": float,\n'
            '    "accuracy": float,\n'
            '    "confidence": float,\n'
            '    "completeness": float\n'
            "  }\n"
            "}"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
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
                        raw_text = res_json["candidates"][0]["content"]["parts"][0][
                            "text"
                        ]
                        parsed = json.loads(raw_text.strip())

                        # Validate structure
                        scores = parsed["granular_scores"]
                        return EvaluationResult(
                            score=parsed["score"],
                            follow_up=parsed["follow_up"],
                            reason=parsed["reason"],
                            move_next=parsed["move_next"],
                            follow_up_question=parsed.get("follow_up_question"),
                            transition_question=parsed.get("transition_question"),
                            action=parsed.get("action", "FOLLOW_UP"),
                            granular_scores=GranularScores(
                                communication=scores["communication"],
                                accuracy=scores["accuracy"],
                                confidence=scores["confidence"],
                                completeness=scores["completeness"],
                            ),
                        )
                    else:
                        logger.warning(
                            f"Gemini {model} returned code {response.status_code}: {response.text}"
                        )
            except Exception as e:
                logger.exception(f"Gemini evaluation failed for model {model}: {e}")

        logger.error("All Gemini evaluation models failed. Using local fallback.")
        return InterviewEvaluator._fallback_evaluation(
            answer, current_topic, next_topic
        )

    @staticmethod
    def _fallback_evaluation(
        answer: str, current_topic: str = "", next_topic: str | None = None
    ) -> EvaluationResult:
        trimmed = answer.strip().lower()
        topic_disp = current_topic or "this area"
        next_disp = next_topic or "the next area"

        # Check if they asked to repeat
        if any(
            phrase in trimmed
            for phrase in [
                "repeat",
                "did not get",
                "not get you",
                "say again",
                "pardon",
            ]
        ):
            return EvaluationResult(
                score=1.0,
                follow_up=True,
                reason="Candidate requested repeating or clarifying the question. (Local Fallback)",
                move_next=False,
                action="REPEAT",
                follow_up_question=f"Sure, let me ask again in a different way. Can you tell me about your experience using {topic_disp}?",
                transition_question=None,
                granular_scores=GranularScores(
                    communication=1.0, accuracy=1.0, confidence=1.0, completeness=1.0
                ),
            )
        # Check if they want to skip or don't know
        elif any(
            phrase in trimmed
            for phrase in ["skip", "don't know", "dont know", "no idea", "pass"]
        ):
            return EvaluationResult(
                score=0.2,
                follow_up=False,
                reason="Candidate requested skipping the topic. (Local Fallback)",
                move_next=True,
                action="SKIP",
                follow_up_question=None,
                transition_question=f"No problem. Let's move on and talk about {next_disp}. Can you share your experience with it?",
                granular_scores=GranularScores(
                    communication=0.5, accuracy=0.2, confidence=0.2, completeness=0.2
                ),
            )
        elif len(trimmed) < 20:
            return EvaluationResult(
                score=0.4,
                follow_up=True,
                reason="Answer is too short (< 20 characters). Requesting elaboration. (Local Fallback)",
                move_next=False,
                action="FOLLOW_UP",
                follow_up_question=f"Could you explain in more detail how you have worked with {topic_disp}?",
                transition_question=None,
                granular_scores=GranularScores(
                    communication=0.5, accuracy=0.4, confidence=0.4, completeness=0.3
                ),
            )
        else:
            return EvaluationResult(
                score=0.8,
                follow_up=False,
                reason="Answer is sufficient in length. Proceeding to next question. (Local Fallback)",
                move_next=True,
                action="TRANSITION",
                follow_up_question=None,
                transition_question=f"Great. Let's move on and talk about {next_disp}. Can you share your experience with it?",
                granular_scores=GranularScores(
                    communication=0.8, accuracy=0.8, confidence=0.8, completeness=0.8
                ),
            )

    @staticmethod
    async def extract_focus_tech_and_syllabus(
        answer: str, resume_json: dict
    ) -> tuple[str, list[str]]:
        """
        Uses Gemini to extract the chosen technology from candidate's text and generate
        3-4 highly relevant subtopics/skills to query during the session.
        """
        api_key = settings.GEMINI_API_KEY
        fallback_tech = "Python"
        fallback_topics = [
            "Language Fundamentals",
            "Data Structures & Collections",
            "Object-Oriented Programming",
            "Concurrency & Multithreading",
            "Memory Management & Garbage Collection",
            "Testing & Debugging Practices",
        ]

        if not api_key:
            return fallback_tech, fallback_topics

        prompt = (
            "You are a technical recruiting coordinator setting up a mock interview for a college student / recent graduate.\n"
            "The candidate was asked which programming language or technology they want to focus on today.\n"
            f'Candidate\'s Answer: "{answer}"\n'
            f"Candidate's Resume JSON: {json.dumps(resume_json.get('skills', {}))}\n\n"
            "Identify the single chosen technology/programming language, and generate 6 core subtopics "
            "suitable for a student/entry-level developer mock interview (e.g., Python: ['Syntax & Basics', 'Data Structures & Collections', 'OOP & Classes', 'Concurrency & Threads', 'Memory & GC', 'Testing & Exceptions']). "
            "Focus on core concepts, algorithms, structures, and practical application in personal or academic projects rather than enterprise-level production architecture.\n"
            "Keep the topic names short and concise.\n\n"
            "Return a valid JSON object matching this structure:\n"
            "{\n"
            '  "technology": "Name of Technology",\n'
            '  "subtopics": ["Topic 1", "Topic 2", "Topic 3", "Topic 4", "Topic 5", "Topic 6"]\n'
            "}"
        )

        models = [settings.GEMINI_MODEL, "gemini-2.5-flash"]
        if settings.GEMINI_MODEL not in models:
            models.insert(0, settings.GEMINI_MODEL)

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }

        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    response = await client.post(url, json=payload)
                    if response.status_code == 200:
                        res_json = response.json()
                        raw_text = res_json["candidates"][0]["content"]["parts"][0][
                            "text"
                        ]
                        parsed = json.loads(raw_text.strip())
                        tech = parsed.get("technology", fallback_tech)
                        topics = parsed.get("subtopics", fallback_topics)
                        if len(topics) >= 2:
                            return tech, topics
            except Exception as e:
                logger.exception(
                    f"Failed to extract focus tech with model {model}: {e}"
                )

        return fallback_tech, fallback_topics

    @staticmethod
    async def generate_graceful_transition(
        current_topic: str,
        next_topic: str,
        last_answer: str,
    ) -> str:
        """
        Calls Gemini to generate a graceful conversational transition from the current topic
        to the next topic, briefly acknowledging the candidate's last response.
        """
        api_key = settings.GEMINI_API_KEY
        fallback_msg = f"Let's move on. Can you tell me about your experience or skills related to {next_topic}?"
        if not api_key:
            return fallback_msg

        models = [settings.GEMINI_MODEL, "gemini-2.5-flash"]
        if settings.GEMINI_MODEL not in models:
            models.insert(0, settings.GEMINI_MODEL)

        prompt = (
            "You are Kira, an expert technical voice interviewer.\n"
            f"You are transitioning the conversation from the topic '{current_topic}' to the next topic '{next_topic}'.\n"
            f"The candidate's last response about '{current_topic}' was: '{last_answer}'\n\n"
            "Generate a graceful, natural voice transition statement and introductory question for the new topic.\n"
            "First, briefly acknowledge the candidate's previous response in a polite, conversational manner (e.g., 'Nice explanation', 'That makes sense', 'That's a good summary of Y').\n"
            "Then, introduce Y ('{next_topic}') and ask them how they have used or learned Y in their projects or coursework.\n"
            "Keep the entire response extremely concise (under 2 sentences), natural for text-to-speech, and warm."
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "text/plain"},
        }

        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    response = await client.post(url, json=payload)
                    if response.status_code == 200:
                        res_json = response.json()
                        raw_text = res_json["candidates"][0]["content"]["parts"][0][
                            "text"
                        ]
                        cleaned = raw_text.strip()
                        if cleaned:
                            return cleaned
            except Exception as e:
                logger.warning(
                    f"Failed to generate graceful transition with {model}: {e}"
                )

        return fallback_msg
