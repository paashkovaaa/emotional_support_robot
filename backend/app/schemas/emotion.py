"""Pydantic-схеми для щоденника емоцій."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# ── Створення запису ──

class EmotionEntryCreate(BaseModel):
    """Створення нового запису емоцій."""

    entry_date: date = Field(
        description="Дата запису (YYYY-MM-DD)",
    )
    emoji: str | None = Field(
        default=None,
        max_length=10,
        description="Емодзі емоції за день",
    )
    user_description: str | None = Field(
        default=None,
        max_length=5000,
        description="Опис стану від користувача",
    )
    bot_description: str | None = Field(
        default=None,
        max_length=5000,
        description="Опис стану, згенерований ботом",
    )
    emotion_tags: list[str] | None = Field(
        default=None,
        max_length=10,
        description="Теги емоцій: стрес, щастя, злість, тривога тощо",
    )


# ── Оновлення запису ──

class EmotionEntryUpdate(BaseModel):
    """Часткове оновлення запису емоцій."""

    emoji: str | None = Field(default=None, max_length=10)
    user_description: str | None = Field(default=None, max_length=5000)
    bot_description: str | None = Field(default=None, max_length=5000)
    emotion_tags: list[str] | None = Field(default=None, max_length=10)


# ── Читання запису ──

class EmotionEntryRead(BaseModel):
    """Відповідь із записом емоцій."""

    id: uuid.UUID
    user_id: uuid.UUID
    entry_date: date
    emoji: str | None
    user_description: str | None
    bot_description: str | None
    emotion_tags: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Список записів за місяць ──

class EmotionMonthQuery(BaseModel):
    """Параметри запиту за місяць."""

    month: int = Field(ge=1, le=12, description="Місяць (1-12)")
    year: int = Field(ge=2020, le=2100, description="Рік")


# ── Запит на генерацію від AI ──

class EmotionGenerateRequest(BaseModel):
    """Запит на генерацію опису стану ботом."""

    conversation_id: uuid.UUID = Field(
        description="ID розмови, на основі якої генерувати опис",
    )
    entry_date: date | None = Field(
        default=None,
        description="Дата запису (за замовчуванням — сьогодні)",
    )


class EmotionGenerateResponse(BaseModel):
    """Відповідь із згенерованим описом стану."""

    description: str = Field(description="Опис емоційного стану")
    emoji: str = Field(description="Запропонований емодзі")
    tags: list[str] = Field(description="Запропоновані теги емоцій")

