from pydantic import BaseModel


class EvaluationResult(BaseModel):
    """Result of evaluating a user response."""

    score: float
    follow_up: bool
    reason: str
    move_next: bool


class InterviewEvaluator:
    """Evaluates candidate responses using simple rule-based heuristics."""

    @staticmethod
    def evaluate_response(answer: str, current_question: str) -> EvaluationResult:
        """
        Rule-based dummy evaluation.
        - If the answer is too short (< 20 chars), ask a follow-up.
        - Otherwise, transition to the next topic/question.
        """
        trimmed_answer = answer.strip()

        if len(trimmed_answer) < 20:
            return EvaluationResult(
                score=0.4,
                follow_up=True,
                reason="Answer is too short (< 20 characters). Requesting elaboration.",
                move_next=False,
            )
        else:
            return EvaluationResult(
                score=0.8,
                follow_up=False,
                reason="Answer is sufficient in length. Proceeding to next question.",
                move_next=True,
            )
