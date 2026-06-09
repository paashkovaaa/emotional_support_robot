"""Pydantic-схеми для користувачів."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from backend.app.models.user import UserRole


class UserRead(BaseModel):
    """Читання даних користувача."""

    id: uuid.UUID
    email: str | None
    role: UserRole
    is_active: bool
    is_blocked: bool
    last_login: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserAdminRead(UserRead):
    """Розширені дані для адміна."""

    updated_at: datetime
