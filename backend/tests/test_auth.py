from httpx import AsyncClient


async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "name": "Test User",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert "id" in data
    assert "hashed_password" not in data


async def test_register_existing_user(client: AsyncClient):
    # Register once
    await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "name": "Test User",
            "password": "securepassword123",
        },
    )
    # Register again
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "name": "Test User",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "User with this email already exists"


async def test_login_user(client: AsyncClient):
    # Register user
    await client.post(
        "/api/auth/register",
        json={
            "email": "login@example.com",
            "name": "Login User",
            "password": "securepassword123",
        },
    )
    # Login
    response = await client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "securepassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" not in data  # No longer in response body!
    assert data["token_type"] == "bearer"
    assert "refresh_token" in response.cookies  # Set in HttpOnly cookie!


async def test_login_invalid_credentials(client: AsyncClient):
    response = await client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "somepassword"},
    )
    assert response.status_code == 401


async def test_get_me(client: AsyncClient):
    # Register and login
    await client.post(
        "/api/auth/register",
        json={
            "email": "me@example.com",
            "name": "Me User",
            "password": "securepassword123",
        },
    )
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "me@example.com", "password": "securepassword123"},
    )
    token = login_resp.json()["access_token"]

    # Get me
    response = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["name"] == "Me User"


async def test_refresh_token(client: AsyncClient):
    # Register and login
    await client.post(
        "/api/auth/register",
        json={
            "email": "refresh@example.com",
            "name": "Refresh User",
            "password": "securepassword123",
        },
    )
    login_resp = await client.post(
        "/api/auth/login",
        json={
            "email": "refresh@example.com",
            "password": "securepassword123",
        },
    )
    assert "refresh_token" in login_resp.cookies
    old_refresh = login_resp.cookies.get("refresh_token")

    # Refresh (HTTPX client preserves cookie jar, but we can also check rotation)
    response = await client.post("/api/auth/refresh")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" not in data

    # New cookie set, rotated!
    assert "refresh_token" in response.cookies
    new_refresh = response.cookies.get("refresh_token")
    assert new_refresh != old_refresh


async def test_logout_user(client: AsyncClient):
    # Register and login
    await client.post(
        "/api/auth/register",
        json={
            "email": "logout@example.com",
            "name": "Logout User",
            "password": "securepassword123",
        },
    )
    await client.post(
        "/api/auth/login",
        json={"email": "logout@example.com", "password": "securepassword123"},
    )

    # Logout
    logout_resp = await client.post("/api/auth/logout")
    assert logout_resp.status_code == 204

    # Try to refresh again, should be denied since cookie was revoked/cleared
    refresh_resp = await client.post("/api/auth/refresh")
    assert refresh_resp.status_code == 401
