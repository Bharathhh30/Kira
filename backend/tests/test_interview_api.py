from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.resume import Resume
from app.models.user import User
from app.core.security import hash_password


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

    # 1. Start Interview
    response = await client.post(
        "/api/interview/start",
        json={"interview_mode": "resume"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    interview_id = data["id"]
    assert data["current_topic"] == "Python"
    assert data["follow_up_count"] == 0
    assert not data["is_completed"]
    assert "remaining_topics" in data
    assert len(data["remaining_topics"]) > 0

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
    assert len(ans_data["history"]) == 1
    assert ans_data["history"][0]["score"] == 0.4

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
    assert len(ans_data2["history"]) == 2
    assert ans_data2["history"][1]["score"] == 0.8
