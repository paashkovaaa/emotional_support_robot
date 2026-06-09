"""Pydantic-схеми для профілю користувача."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from backend.app.models.profile import CommunicationStyle, Gender


# ── Опитування ──

class SurveyRequest(BaseModel):
    """Запит з результатами опитування."""

    communication_style: CommunicationStyle = Field(
        default=CommunicationStyle.BALANCED,
        description="Стиль спілкування: аналітичний / дружній / збалансований",
    )
    life_area: str | None = Field(
        default=None,
        max_length=1000,
        description="Сфера життя для покращення",
    )
    concern: str | None = Field(
        default=None,
        max_length=1000,
        description="Що найбільше бентежить",
    )
    works_with_psychologist: bool = Field(
        default=False,
        description="Чи працює з психологом",
    )


# ── Профіль ──

class ProfileRead(BaseModel):
    """Читання профілю."""

    id: uuid.UUID
    user_id: uuid.UUID
    nickname: str
    age: int | None
    gender: Gender | None
    communication_style: CommunicationStyle
    life_area: str | None
    concern: str | None
    works_with_psychologist: bool
    survey_completed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    """Оновлення профілю (часткове)."""

    nickname: str | None = Field(default=None, min_length=2, max_length=100)
    age: int | None = Field(default=None, ge=13, le=120)
    gender: Gender | None = None
    communication_style: CommunicationStyle | None = None
    life_area: str | None = Field(default=None, max_length=1000)
    concern: str | None = Field(default=None, max_length=1000)
    works_with_psychologist: bool | None = None
