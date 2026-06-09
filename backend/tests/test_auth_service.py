"""Тести сервісу автентифікації."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import BadRequestError, ConflictError, UnauthorizedError
from backend.app.core.security import create_token_pair, verify_password
from backend.app.models.user import User
from backend.app.services.auth_service import AuthService


class TestAuthServiceRegister:
    """Тести реєстрації."""

    async def test_register_success(self, db_session: AsyncSession):
        service = AuthService(db_session)
        user = await service.register(
            email="newuser@example.com",
            password="password123",
            nickname="NewUser",
        )
        assert user.email == "newuser@example.com"
        assert user.hashed_password != "password123"
        assert verify_password("password123", user.hashed_password)

    async def test_register_creates_profile(self, db_session: AsyncSession):
        service = AuthService(db_session)
        user = await service.register(
            email="withprofile@example.com",
            password="password123",
            nickname="WithProfile",
        )
        # Профіль створюється через flush
        assert user.id is not None

    async def test_register_duplicate_email(self, db_session: AsyncSession, test_user: User):
        service = AuthService(db_session)
        with pytest.raises(ConflictError):
            await service.register(
                email="test@example.com",  # Вже існує
                password="password123",
                nickname="Duplicate",
            )


class TestAuthServiceLogin:
    """Тести логіну."""

    async def test_login_success(self, db_session: AsyncSession, test_user: User):
        service = AuthService(db_session)
        tokens = await service.login(
            email="test@example.com",
            password="testpassword123",
        )
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"

    async def test_login_wrong_password(self, db_session: AsyncSession, test_user: User):
        service = AuthService(db_session)
        with pytest.raises(UnauthorizedError):
            await service.login(
                email="test@example.com",
                password="wrongpassword",
            )

    async def test_login_nonexistent_email(self, db_session: AsyncSession):
        service = AuthService(db_session)
        with pytest.raises(UnauthorizedError):
            await service.login(
                email="nouser@example.com",
                password="password123",
            )

    async def test_login_blocked_user(self, db_session: AsyncSession, blocked_user: User):
        service = AuthService(db_session)
        with pytest.raises(UnauthorizedError, match="заблоковано"):
            await service.login(
                email="blocked@example.com",
                password="blockedpassword123",
            )

    async def test_login_updates_last_login(self, db_session: AsyncSession, test_user: User):
        service = AuthService(db_session)
        assert test_user.last_login is None
        await service.login(email="test@example.com", password="testpassword123")
        assert test_user.last_login is not None


class TestAuthServiceRefresh:
    """Тести оновлення токенів."""

    async def test_refresh_success(self, db_session: AsyncSession, test_user: User):
        service = AuthService(db_session)
        # Отримуємо початкові токени
        tokens = create_token_pair(
            user_id=str(test_user.id),
            role=test_user.role.value,
            email=test_user.email,
        )
        # Оновлюємо
        new_tokens = await service.refresh_tokens(tokens["refresh_token"])
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens

    async def test_refresh_with_access_token_fails(self, db_session: AsyncSession, test_user: User):
        service = AuthService(db_session)
        tokens = create_token_pair(
            user_id=str(test_user.id),
            role=test_user.role.value,
        )
        with pytest.raises(UnauthorizedError):
            await service.refresh_tokens(tokens["access_token"])  # Не refresh!

    async def test_refresh_invalid_token(self, db_session: AsyncSession):
        service = AuthService(db_session)
        with pytest.raises(UnauthorizedError):
            await service.refresh_tokens("invalid.token.here")


class TestAuthServiceChangePassword:
    """Тести зміни пароля."""

    async def test_change_password_success(self, db_session: AsyncSession, test_user: User):
        service = AuthService(db_session)
        await service.change_password(
            user=test_user,
            old_password="testpassword123",
            new_password="newpassword456",
        )
        assert verify_password("newpassword456", test_user.hashed_password)
        assert not verify_password("testpassword123", test_user.hashed_password)

    async def test_change_password_wrong_old(self, db_session: AsyncSession, test_user: User):
        service = AuthService(db_session)
        with pytest.raises(BadRequestError):
            await service.change_password(
                user=test_user,
                old_password="wrongoldpassword",
                new_password="newpassword456",
            )

