from typing import Any, Dict
from app.schemas.interview import InterviewHistoryEntry, InterviewState
from app.services.interview.evaluator import InterviewEvaluator


class InterviewManager:
    """Manages the lifecycle, state transitions, and evaluation flow of an interview session."""

    def __init__(self, max_follow_ups: int = 2):
        self.max_follow_ups = max_follow_ups

    def process_answer(self, state: InterviewState, answer: str) -> Dict[str, Any]:
        """
        Receives user answer, evaluates it, updates the InterviewState,
        and determines the next action.
        """
        if state.is_completed:
            return {"action": "END", "text": "This interview is already completed."}

        # 1. Evaluate the answer
        evaluation = InterviewEvaluator.evaluate_response(
            answer, state.current_question
        )

        # 2. Add exchange to history
        history_entry = InterviewHistoryEntry(
            question=state.current_question,
            answer=answer,
            score=evaluation.score,
            feedback=evaluation.reason,
        )
        state.history.append(history_entry)

        # 3. Decrement remaining time (assume ~60 seconds per question/answer exchange)
        state.remaining_time = max(0, state.remaining_time - 60)

        # 4. Determine next state transition
        # We transition if the answer is good, or if we have hit the maximum follow-up limit
        should_transition = evaluation.move_next or (
            state.follow_up_count >= self.max_follow_ups
        )

        if should_transition:
            # Move to the next topic if available
            state.follow_up_count = 0
            if state.remaining_topics:
                next_topic = state.remaining_topics.pop(0)
                state.current_topic = next_topic
                state.current_question = f"Let's move on. Can you tell me about your experience or skills related to {next_topic}?"
                action = "ASK"
            else:
                # No more topics, end the interview
                state.is_completed = True
                state.current_topic = None
                state.current_question = "Thank you! We have covered all the topics. This concludes your mock interview."
                action = "END"
        else:
            # Request follow-up
            state.follow_up_count += 1
            state.current_question = (
                f"Could you please elaborate on that? Specifically, "
                f"tell me more about the technical details of your work with {state.current_topic}."
            )
            action = "ASK"

        return {
            "action": action,
            "text": state.current_question,
            "evaluation": {
                "score": evaluation.score,
                "reason": evaluation.reason,
            },
        }
