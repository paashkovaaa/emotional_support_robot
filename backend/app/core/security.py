"""Модуль безпеки: хешування паролів, JWT-токени."""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from backend.app.config import settings

# ── Хешування паролів ──


def hash_password(password: str) -> str:
    """Хешує пароль за допомогою bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Перевіряє пароль проти хешу."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ── JWT-токени ──

def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    """Створює access token.

    Args:
        subject: Ідентифікатор користувача (user_id як str).
        extra_claims: Додаткові дані (role, email тощо).

    Returns:
        Закодований JWT access token.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Створює refresh token.

    Args:
        subject: Ідентифікатор користувача (user_id як str).

    Returns:
        Закодований JWT refresh token.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": "refresh",
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Декодує та валідує JWT-токен.

    Args:
        token: JWT-токен.

    Returns:
        Розкодований payload.

    Raises:
        JWTError: Якщо токен невалідний або прострочений.
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def create_token_pair(user_id: str, role: str, email: str | None = None) -> dict[str, str]:
    """Створює пару access + refresh токенів.

    Args:
        user_id: UUID користувача як рядок.
        role: Роль користувача.
        email: Email користувача (опціонально).

    Returns:
        Словник з access_token, refresh_token та token_type.
    """
    extra = {"role": role}
    if email:
        extra["email"] = email

    return {
        "access_token": create_access_token(subject=user_id, extra_claims=extra),
        "refresh_token": create_refresh_token(subject=user_id),
        "token_type": "bearer",
    }
