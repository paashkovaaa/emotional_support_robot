"""Тести модуля безпеки: хешування паролів, JWT-токени."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from backend.app.config import settings
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    hash_password,
    verify_password,
)


# ── Хешування паролів ──


class TestPasswordHashing:
    """Тести хешування паролів (bcrypt)."""

    def test_hash_password_returns_string(self):
        hashed = hash_password("mypassword")
        assert isinstance(hashed, str)
        assert hashed != "mypassword"

    def test_hash_password_different_each_time(self):
        h1 = hash_password("mypassword")
        h2 = hash_password("mypassword")
        assert h1 != h2  # Різні salt

    def test_verify_password_correct(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_empty(self):
        hashed = hash_password("mypassword")
        assert verify_password("", hashed) is False

    def test_hash_password_unicode(self):
        hashed = hash_password("пароль123")
        assert verify_password("пароль123", hashed) is True
        assert verify_password("пароль456", hashed) is False


# ── JWT-токени ──


class TestJWTTokens:
    """Тести JWT-токенів."""

    def test_create_access_token(self):
        token = create_access_token(subject="user-123")
        assert isinstance(token, str)
        assert len(token) > 50

    def test_create_access_token_with_extra_claims(self):
        token = create_access_token(
            subject="user-123",
            extra_claims={"role": "admin", "email": "test@test.com"},
        )
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["role"] == "admin"
        assert payload["email"] == "test@test.com"
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        token = create_refresh_token(subject="user-123")
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"

    def test_decode_token_valid(self):
        token = create_access_token(subject="user-123")
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"
        assert "iat" in payload
        assert "exp" in payload

    def test_decode_token_invalid(self):
        from jose import JWTError

        with pytest.raises(JWTError):
            decode_token("invalid.token.here")

    def test_decode_token_expired(self):
        from jose import JWTError

        # Створюємо токен з минулим терміном дії
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "user-123",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
            "type": "access",
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        with pytest.raises(JWTError):
            decode_token(token)

    def test_create_token_pair(self):
        tokens = create_token_pair(
            user_id="user-123",
            role="user",
            email="test@test.com",
        )
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"

        # Перевіряємо access token
        access_payload = decode_token(tokens["access_token"])
        assert access_payload["sub"] == "user-123"
        assert access_payload["role"] == "user"
        assert access_payload["type"] == "access"

        # Перевіряємо refresh token
        refresh_payload = decode_token(tokens["refresh_token"])
        assert refresh_payload["sub"] == "user-123"
        assert refresh_payload["type"] == "refresh"

    def test_token_pair_without_email(self):
        tokens = create_token_pair(user_id="user-123", role="user")
        access_payload = decode_token(tokens["access_token"])
        assert "email" not in access_payload

    def test_access_token_expiry(self):
        token = create_access_token(subject="user-123")
        payload = decode_token(token)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        # Повинен закінчуватися приблизно через ACCESS_TOKEN_EXPIRE_MINUTES
        diff = (exp - now).total_seconds() / 60
        assert abs(diff - settings.ACCESS_TOKEN_EXPIRE_MINUTES) < 1

