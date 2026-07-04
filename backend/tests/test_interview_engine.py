import uuid
from app.schemas.interview import InterviewState
from app.services.interview.context_loader import ContextLoader
from app.services.interview.evaluator import InterviewEvaluator
from app.services.interview.manager import InterviewManager

MOCK_RESUME = {
    "personal": {"name": "Test User", "email": "test@example.com"},
    "skills": {"technical": ["Python", "FastAPI"]},
    "projects": [{"name": "Test Project"}],
}


def test_context_loader():
    user_id = uuid.uuid4()
    state = ContextLoader.load_context(
        user_id=user_id, resume_json=MOCK_RESUME, interview_mode="resume"
    )

    assert isinstance(state, InterviewState)
    assert state.user_id == user_id
    assert state.current_topic == "Python"
    assert state.remaining_topics == ["FastAPI", "Project: Test Project"]
    assert not state.is_completed
    assert state.follow_up_count == 0


def test_evaluator():
    # Test short response
    res1 = InterviewEvaluator.evaluate_response("Short answer", "What is Python?")
    assert res1.follow_up
    assert not res1.move_next
    assert res1.score == 0.4

    # Test long response
    res2 = InterviewEvaluator.evaluate_response(
        "This is a sufficiently long response that should pass the 20 character limit check.",
        "What is Python?",
    )
    assert not res2.follow_up
    assert res2.move_next
    assert res2.score == 0.8


def test_manager_short_answer():
    user_id = uuid.uuid4()
    state = ContextLoader.load_context(
        user_id=user_id, resume_json=MOCK_RESUME, interview_mode="resume"
    )

    manager = InterviewManager()
    result = manager.process_answer(state, "Too short")

    assert result["action"] == "ASK"
    assert "elaborate" in result["text"]
    assert state.follow_up_count == 1
    assert len(state.history) == 1
    assert state.history[0].answer == "Too short"
    assert state.history[0].score == 0.4


def test_manager_long_answer_transition():
    user_id = uuid.uuid4()
    state = ContextLoader.load_context(
        user_id=user_id, resume_json=MOCK_RESUME, interview_mode="resume"
    )

    manager = InterviewManager()
    result = manager.process_answer(
        state, "This is a very long response detailing Python development."
    )

    assert result["action"] == "ASK"
    assert state.current_topic == "FastAPI"
    assert state.follow_up_count == 0
    assert len(state.history) == 1
    assert state.history[0].score == 0.8


def test_manager_max_follow_up_transition():
    user_id = uuid.uuid4()
    state = ContextLoader.load_context(
        user_id=user_id, resume_json=MOCK_RESUME, interview_mode="resume"
    )

    manager = InterviewManager(max_follow_ups=1)

    # First short response: increments follow_up_count to 1
    manager.process_answer(state, "Too short")
    assert state.follow_up_count == 1
    assert state.current_topic == "Python"

    # Second short response: since follow_up_count >= max_follow_ups, it transitions to FastAPI
    result2 = manager.process_answer(state, "Still short")
    assert state.follow_up_count == 0
    assert state.current_topic == "FastAPI"
    assert result2["action"] == "ASK"


def test_manager_completion():
    # Only 1 topic to make completion easy
    simple_resume = {"skills": {"technical": ["Python"]}}
    user_id = uuid.uuid4()
    state = ContextLoader.load_context(
        user_id=user_id, resume_json=simple_resume, interview_mode="resume"
    )

    manager = InterviewManager()
    result = manager.process_answer(
        state, "This is a detailed answer that should successfully complete Python."
    )

    assert state.is_completed
    assert result["action"] == "END"
    assert "concludes" in result["text"]
