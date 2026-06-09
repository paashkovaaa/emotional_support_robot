"""Інтеграційні тести API автентифікації."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User
from backend.tests.conftest import get_auth_headers


class TestRegisterAPI:
    """Тести POST /api/auth/register."""

    async def test_register_success(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "nickname": "NewUser",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data

    async def test_register_duplicate_email(self, client: AsyncClient):
        # Перша реєстрація
        await client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "password123",
                "nickname": "User1",
            },
        )
        # Друга з тим самим email
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "password456",
                "nickname": "User2",
            },
        )
        assert response.status_code == 409

    async def test_register_invalid_email(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
                "nickname": "User",
            },
        )
        assert response.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "user@example.com",
                "password": "short",
                "nickname": "User",
            },
        )
        assert response.status_code == 422

    async def test_register_missing_nickname(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "user@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 422


class TestLoginAPI:
    """Тести POST /api/auth/login."""

    async def test_login_success(self, client: AsyncClient):
        # Спочатку реєструємо
        await client.post(
            "/api/auth/register",
            json={
                "email": "logintest@example.com",
                "password": "password123",
                "nickname": "LoginUser",
            },
        )
        # Логін
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "logintest@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post(
            "/api/auth/register",
            json={
                "email": "wrongpw@example.com",
                "password": "password123",
                "nickname": "User",
            },
        )
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "wrongpw@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "nouser@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 401


class TestRefreshAPI:
    """Тести POST /api/auth/refresh."""

    async def test_refresh_success(self, client: AsyncClient):
        # Реєстрація + логін
        await client.post(
            "/api/auth/register",
            json={
                "email": "refresh@example.com",
                "password": "password123",
                "nickname": "RefreshUser",
            },
        )
        login_resp = await client.post(
            "/api/auth/login",
            json={
                "email": "refresh@example.com",
                "password": "password123",
            },
        )
        refresh_token = login_resp.json()["refresh_token"]

        # Refresh
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_invalid_token(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert response.status_code == 401


class TestLogoutAPI:
    """Тести POST /api/auth/logout."""

    async def test_logout_success(self, client: AsyncClient):
        # Реєстрація + логін
        await client.post(
            "/api/auth/register",
            json={
                "email": "logout@example.com",
                "password": "password123",
                "nickname": "LogoutUser",
            },
        )
        login_resp = await client.post(
            "/api/auth/login",
            json={
                "email": "logout@example.com",
                "password": "password123",
            },
        )
        token = login_resp.json()["access_token"]

        response = await client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_logout_without_token(self, client: AsyncClient):
        response = await client.post("/api/auth/logout")
        assert response.status_code == 401


class TestChangePasswordAPI:
    """Тести POST /api/auth/change-password."""

    async def test_change_password_success(self, client: AsyncClient):
        # Реєстрація + логін
        await client.post(
            "/api/auth/register",
            json={
                "email": "changepw@example.com",
                "password": "password123",
                "nickname": "ChangePW",
            },
        )
        login_resp = await client.post(
            "/api/auth/login",
            json={
                "email": "changepw@example.com",
                "password": "password123",
            },
        )
        token = login_resp.json()["access_token"]

        response = await client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "old_password": "password123",
                "new_password": "newpassword456",
            },
        )
        assert response.status_code == 200

        # Перевіряємо що новий пароль працює
        login2 = await client.post(
            "/api/auth/login",
            json={
                "email": "changepw@example.com",
                "password": "newpassword456",
            },
        )
        assert login2.status_code == 200

    async def test_change_password_wrong_old(self, client: AsyncClient):
        await client.post(
            "/api/auth/register",
            json={
                "email": "wrongold@example.com",
                "password": "password123",
                "nickname": "WrongOld",
            },
        )
        login_resp = await client.post(
            "/api/auth/login",
            json={
                "email": "wrongold@example.com",
                "password": "password123",
            },
        )
        token = login_resp.json()["access_token"]

        response = await client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "old_password": "wrongoldpassword",
                "new_password": "newpassword456",
            },
        )
        assert response.status_code == 400

