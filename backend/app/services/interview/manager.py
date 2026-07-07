from typing import Any, Dict
from app.schemas.interview import InterviewHistoryEntry, InterviewState
from app.services.interview.evaluator import InterviewEvaluator


class InterviewManager:
    """Manages the lifecycle, state transitions, and evaluation flow of an interview session."""

    def __init__(self, max_follow_ups: int = 2):
        self.max_follow_ups = max_follow_ups

    async def process_answer(
        self, state: InterviewState, answer: str
    ) -> Dict[str, Any]:
        """
        Receives user answer, evaluates it, updates the InterviewState,
        and determines the next action.
        """
        if state.is_completed:
            return {"action": "END", "text": "This interview is already completed."}

        if state.current_topic == "Topic Selection":
            (
                chosen_tech,
                topics,
            ) = await InterviewEvaluator.extract_focus_tech_and_syllabus(
                answer, state.resume_json
            )

            history_entry = InterviewHistoryEntry(
                question=state.current_question,
                answer=answer,
                score=1.0,
                feedback=f"Selected focus technology: {chosen_tech}",
            )
            state.history.append(history_entry)

            state.current_topic = chosen_tech
            state.remaining_topics = topics[1:] if len(topics) > 1 else []
            state.topic_list = list(topics)
            state.follow_up_count = 0
            state.current_question = (
                f"Great! Let's focus on {chosen_tech} today. "
                f"To start off, could you tell me about a project or personal application you built using {chosen_tech}, "
                "and what challenges you faced when developing it?"
            )

            return {
                "action": "ASK",
                "text": state.current_question,
                "evaluation": {
                    "score": 1.0,
                    "reason": f"Focus technology selected: {chosen_tech}",
                },
            }

        # Find next topic if we transition
        next_topic_candidate = (
            state.remaining_topics[0] if state.remaining_topics else None
        )

        # 1. Evaluate the answer
        evaluation = await InterviewEvaluator.evaluate_response(
            answer,
            state.current_question,
            current_topic=state.current_topic or "",
            next_topic=next_topic_candidate,
        )

        # 2. Add exchange to history
        history_entry = InterviewHistoryEntry(
            question=state.current_question,
            answer=answer,
            score=evaluation.score,
            feedback=evaluation.reason,
            granular_scores=evaluation.granular_scores,
        )
        state.history.append(history_entry)

        # 3. Decrement remaining time (assume ~60 seconds per question/answer exchange)
        state.remaining_time = max(0, state.remaining_time - 60)

        # 4. Determine next state transition based on the adaptive action
        should_transition = False
        increment_follow_up = False

        # If Gemini returned no explicit action, determine based on move_next/follow_up booleans
        action_type = getattr(evaluation, "action", None)
        if not action_type or action_type == "FOLLOW_UP":
            # For backward compatibility with older evaluations or mock objects
            if getattr(evaluation, "move_next", False):
                action_type = "TRANSITION"
            elif getattr(evaluation, "follow_up", False):
                action_type = "FOLLOW_UP"
            else:
                action_type = "FOLLOW_UP"

        if action_type == "REPEAT":
            should_transition = False
            increment_follow_up = False
        elif action_type == "SKIP":
            should_transition = True
            increment_follow_up = False
        elif action_type == "TRANSITION":
            should_transition = True
            increment_follow_up = False
        else:  # "FOLLOW_UP"
            if state.follow_up_count >= self.max_follow_ups:
                should_transition = True
                increment_follow_up = False
            else:
                should_transition = False
                increment_follow_up = True

        if should_transition:
            # Move to the next topic if available
            state.follow_up_count = 0
            if state.remaining_topics:
                next_topic = state.remaining_topics.pop(0)

                # Dynamically generate a graceful, personalized topic transition
                transition_question = evaluation.transition_question
                if not transition_question or transition_question.strip().startswith(
                    "Let's move on"
                ):
                    transition_question = (
                        await InterviewEvaluator.generate_graceful_transition(
                            current_topic=state.current_topic or "",
                            next_topic=next_topic,
                            last_answer=answer,
                        )
                    )

                state.current_topic = next_topic
                state.current_question = transition_question
                action = "ASK"
            else:
                # No more topics, end the interview
                state.is_completed = True
                state.current_topic = None
                state.current_question = "Thank you! We have covered all the topics. This concludes your mock interview."
                action = "END"
        else:
            if increment_follow_up:
                state.follow_up_count += 1
            state.current_question = (
                evaluation.follow_up_question
                or f"Could you please elaborate on that? Specifically, tell me more about the technical details of your work with {state.current_topic}."
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
