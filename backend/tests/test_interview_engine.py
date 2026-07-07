import uuid
from unittest.mock import patch
from app.schemas.interview import InterviewState
from app.services.interview.context_loader import ContextLoader
from app.services.interview.evaluator import EvaluationResult, GranularScores
from app.services.interview.manager import InterviewManager

MOCK_RESUME = {
    "personal": {"name": "Test User", "email": "test@example.com"},
    "skills": {"technical": ["Python", "FastAPI"]},
    "projects": [{"name": "Test Project"}],
}


async def mock_evaluate(answer, current_question, *args, **kwargs):
    if "Python" in answer or "detailed" in answer or len(answer) > 20:
        return EvaluationResult(
            score=0.8,
            follow_up=False,
            reason="Answer is sufficient",
            move_next=True,
            granular_scores=GranularScores(
                communication=0.8,
                accuracy=0.8,
                confidence=0.8,
                completeness=0.8,
            ),
        )
    else:
        return EvaluationResult(
            score=0.4,
            follow_up=True,
            reason="Answer is too short",
            move_next=False,
            granular_scores=GranularScores(
                communication=0.5,
                accuracy=0.4,
                confidence=0.4,
                completeness=0.3,
            ),
        )


def test_context_loader():
    user_id = uuid.uuid4()
    state = ContextLoader.load_context(
        user_id=user_id, resume_json=MOCK_RESUME, interview_mode="resume"
    )

    assert isinstance(state, InterviewState)
    assert state.user_id == user_id
    assert state.current_topic == "Topic Selection"
    assert not state.is_completed
    assert state.follow_up_count == 0


async def test_evaluator():
    # Test short response
    res1 = await mock_evaluate("Short answer", "What is Python?")
    assert res1.follow_up
    assert not res1.move_next
    assert res1.score == 0.4

    # Test long response
    res2 = await mock_evaluate(
        "This is a sufficiently long response that should pass the 20 character limit check.",
        "What is Python?",
    )
    assert not res2.follow_up
    assert res2.move_next
    assert res2.score == 0.8


async def test_manager_short_answer():
    user_id = uuid.uuid4()
    state = ContextLoader.load_context(
        user_id=user_id, resume_json=MOCK_RESUME, interview_mode="resume"
    )
    state.current_topic = "Python"
    state.remaining_topics = ["FastAPI"]

    manager = InterviewManager()
    with patch(
        "app.services.interview.evaluator.InterviewEvaluator.evaluate_response",
        side_effect=mock_evaluate,
    ):
        result = await manager.process_answer(state, "Too short")

    assert result["action"] == "ASK"
    assert "elaborate" in result["text"]
    assert state.follow_up_count == 1
    assert len(state.history) == 1
    assert state.history[0].answer == "Too short"
    assert state.history[0].score == 0.4
    assert state.history[0].granular_scores is not None


async def test_manager_long_answer_transition():
    user_id = uuid.uuid4()
    state = ContextLoader.load_context(
        user_id=user_id, resume_json=MOCK_RESUME, interview_mode="resume"
    )
    state.current_topic = "Python"
    state.remaining_topics = ["FastAPI"]

    manager = InterviewManager()
    with patch(
        "app.services.interview.evaluator.InterviewEvaluator.evaluate_response",
        side_effect=mock_evaluate,
    ):
        result = await manager.process_answer(
            state, "This is a very long response detailing Python development."
        )

    assert result["action"] == "ASK"
    assert state.current_topic == "FastAPI"
    assert state.follow_up_count == 0
    assert len(state.history) == 1
    assert state.history[0].score == 0.8


async def test_manager_max_follow_up_transition():
    user_id = uuid.uuid4()
    state = ContextLoader.load_context(
        user_id=user_id, resume_json=MOCK_RESUME, interview_mode="resume"
    )
    state.current_topic = "Python"
    state.remaining_topics = ["FastAPI"]

    manager = InterviewManager(max_follow_ups=1)

    with patch(
        "app.services.interview.evaluator.InterviewEvaluator.evaluate_response",
        side_effect=mock_evaluate,
    ):
        # First short response: increments follow_up_count to 1
        await manager.process_answer(state, "Too short")
        assert state.follow_up_count == 1
        assert state.current_topic == "Python"

        # Second short response: since follow_up_count >= max_follow_ups, it transitions to FastAPI
        result2 = await manager.process_answer(state, "Still short")
        assert state.follow_up_count == 0
        assert state.current_topic == "FastAPI"
        assert result2["action"] == "ASK"


async def test_manager_completion():
    # Only 1 topic to make completion easy
    simple_resume = {"skills": {"technical": ["Python"]}}
    user_id = uuid.uuid4()
    state = ContextLoader.load_context(
        user_id=user_id, resume_json=simple_resume, interview_mode="resume"
    )
    state.current_topic = "Python"
    state.remaining_topics = []

    manager = InterviewManager()
    with patch(
        "app.services.interview.evaluator.InterviewEvaluator.evaluate_response",
        side_effect=mock_evaluate,
    ):
        result = await manager.process_answer(
            state,
            "This is a detailed answer that should successfully complete Python.",
        )

    assert state.is_completed
    assert result["action"] == "END"
    assert "concludes" in result["text"]
