"""Pydantic-схеми для автентифікації."""

import uuid

from pydantic import BaseModel, EmailStr, Field


# ── Реєстрація ──

class RegisterRequest(BaseModel):
    """Запит на реєстрацію."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128, description="Пароль (мін. 8 символів)")
    nickname: str = Field(min_length=2, max_length=100, description="Нікнейм для профілю")


class RegisterResponse(BaseModel):
    """Відповідь після реєстрації."""

    id: uuid.UUID
    email: str
    message: str = "Реєстрація успішна"


# ── Логін ──

class LoginRequest(BaseModel):
    """Запит на вхід."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Відповідь з JWT-токенами."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ── Refresh ──

class RefreshRequest(BaseModel):
    """Запит на оновлення токена."""

    refresh_token: str


# ── Зміна пароля ──

class ChangePasswordRequest(BaseModel):
    """Запит на зміну пароля."""

    old_password: str
    new_password: str = Field(min_length=8, max_length=128)
