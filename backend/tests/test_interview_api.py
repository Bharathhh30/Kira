from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.resume import Resume
from app.models.user import User
from app.core.security import hash_password
from unittest.mock import patch
from app.services.interview.evaluator import EvaluationResult, GranularScores


async def mock_evaluate(answer, current_question, *args, **kwargs):
    if len(answer) < 20:
        return EvaluationResult(
            score=0.4,
            follow_up=True,
            reason="Answer is too short",
            move_next=False,
            granular_scores=GranularScores(
                communication=0.5, accuracy=0.4, confidence=0.4, completeness=0.3
            ),
        )
    else:
        return EvaluationResult(
            score=0.8,
            follow_up=False,
            reason="Answer is sufficient",
            move_next=True,
            granular_scores=GranularScores(
                communication=0.8, accuracy=0.8, confidence=0.8, completeness=0.8
            ),
        )


async def create_test_user_and_resume(
    db_session: AsyncSession, email: str
) -> tuple[User, Resume]:
    """Helper to seed a user and their parsed resume."""
    hashed_pwd = hash_password("testpassword123")
    user = User(
        email=email,
        hashed_password=hashed_pwd,
        name="API Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    resume = Resume(
        user_id=user.id,
        resume_json={
            "skills": {"technical": ["Python", "FastAPI"]},
            "projects": [{"name": "Chat App"}],
            "experience": [{"company": "EPAM"}],
        },
    )
    db_session.add(resume)
    await db_session.commit()
    await db_session.refresh(resume)

    return user, resume


async def get_auth_headers(client: AsyncClient, email: str) -> dict[str, str]:
    """Helper to log in and return authorization headers."""
    response = await client.post(
        "/api/auth/login",
        json={"email": email, "password": "testpassword123"},
    )
    assert response.status_code == 200
    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}


async def test_start_interview_no_resume(client: AsyncClient, db_session: AsyncSession):
    # Register user but do not upload resume
    hashed_pwd = hash_password("testpassword123")
    user = User(
        email="noresume@example.com",
        hashed_password=hashed_pwd,
        name="No Resume User",
    )
    db_session.add(user)
    await db_session.commit()

    headers = await get_auth_headers(client, "noresume@example.com")

    response = await client.post(
        "/api/interview/start",
        json={"interview_mode": "resume"},
        headers=headers,
    )
    assert response.status_code == 400
    assert "upload your resume" in response.json()["detail"]


async def test_interview_full_flow(client: AsyncClient, db_session: AsyncSession):
    email = "flow@example.com"
    user, _ = await create_test_user_and_resume(db_session, email)
    headers = await get_auth_headers(client, email)

    with patch(
        "app.services.interview.evaluator.InterviewEvaluator.evaluate_response",
        side_effect=mock_evaluate,
    ):
        # 1. Start Interview
        start_res = await client.post(
            "/api/interview/start",
            json={"interview_mode": "resume"},
            headers=headers,
        )
        assert start_res.status_code == 201
        data = start_res.json()
        assert "id" in data
        interview_id = data["id"]
        assert data["current_topic"] == "Topic Selection"
        assert data["follow_up_count"] == 0
        assert not data["is_completed"]

        # Select topic
        with patch(
            "app.services.interview.evaluator.InterviewEvaluator.extract_focus_tech_and_syllabus",
            return_value=("Python", ["Python", "FastAPI"]),
        ):
            sel_res = await client.post(
                f"/api/interview/next/{interview_id}",
                json={"answer": "I would like to focus on Python today."},
                headers=headers,
            )
        assert sel_res.status_code == 200
        sel_data = sel_res.json()
        assert sel_data["current_topic"] == "Python"

        # 2. Get State
        state_res = await client.get(
            f"/api/interview/state/{interview_id}", headers=headers
        )
        assert state_res.status_code == 200
        assert state_res.json()["current_topic"] == "Python"

        # 3. Answer too short (triggers follow up on same topic)
        ans_res = await client.post(
            f"/api/interview/next/{interview_id}",
            json={"answer": "Short"},
            headers=headers,
        )
        assert ans_res.status_code == 200
        ans_data = ans_res.json()
        assert ans_data["current_topic"] == "Python"
        assert ans_data["follow_up_count"] == 1
        assert len(ans_data["history"]) == 2
        assert ans_data["history"][1]["score"] == 0.4

        # 4. Answer sufficient (transitions to FastAPI)
        ans_res2 = await client.post(
            f"/api/interview/next/{interview_id}",
            json={
                "answer": "I have used Python extensively to write clean, asynchronous backend code."
            },
            headers=headers,
        )
        assert ans_res2.status_code == 200
        ans_data2 = ans_res2.json()
        assert ans_data2["current_topic"] == "FastAPI"
        assert ans_data2["follow_up_count"] == 0
        assert len(ans_data2["history"]) == 3
        assert ans_data2["history"][2]["score"] == 0.8


async def test_start_interview_modes(client: AsyncClient, db_session: AsyncSession):
    email = "modes@example.com"
    user, _ = await create_test_user_and_resume(db_session, email)
    headers = await get_auth_headers(client, email)

    # 1. Start Behavioral mode
    res = await client.post(
        "/api/interview/start",
        json={"interview_mode": "behavioral"},
        headers=headers,
    )
    assert res.status_code == 201
    assert res.json()["interview_mode"] == "behavioral"
    assert "Conflict Resolution" in res.json()["current_topic"]

    # 2. Start JD mode (without real Gemini using a mocked method)
    with patch(
        "app.services.interview.service.InterviewService.extract_topics_from_jd",
        return_value=["Custom 1", "Custom 2", "Custom 3", "Custom 4"],
    ):
        res2 = await client.post(
            "/api/interview/start",
            json={
                "interview_mode": "jd",
                "job_description": "We need a Python developer who knows FastAPI and SQL.",
            },
            headers=headers,
        )
    assert res2.status_code == 201
    assert res2.json()["interview_mode"] == "jd"
    assert res2.json()["current_topic"] == "Custom 1"


async def test_end_interview_early(client: AsyncClient, db_session: AsyncSession):
    email = "endearly@example.com"
    user, _ = await create_test_user_and_resume(db_session, email)
    headers = await get_auth_headers(client, email)

    # Start session
    response = await client.post(
        "/api/interview/start",
        json={"interview_mode": "coding"},
        headers=headers,
    )
    assert response.status_code == 201
    interview_id = response.json()["id"]

    # End early
    with patch(
        "app.services.interview.service.InterviewService.generate_final_report",
        return_value={
            "summary": "Completed early.",
            "strengths": ["Quick start"],
            "weaknesses": ["None yet"],
            "granular_averages": {
                "communication": 0.8,
                "accuracy": 0.8,
                "confidence": 0.8,
                "completeness": 0.8,
            },
        },
    ):
        end_res = await client.post(
            f"/api/interview/end/{interview_id}",
            headers=headers,
        )
    assert end_res.status_code == 200
    data = end_res.json()
    assert data["is_completed"] is True
    assert data["report"] is not None
    assert data["report"]["summary"] == "Completed early."
