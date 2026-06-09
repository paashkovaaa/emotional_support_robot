"""Pydantic-схеми для адмін-панелі."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from backend.app.models.knowledge_base import KnowledgeCategory, KnowledgeStatus
from backend.app.models.user import UserRole


# ── Користувачі ──

class AdminUserRead(BaseModel):
    """Розширена інформація про користувача для адміна."""

    id: uuid.UUID
    email: str | None
    role: UserRole
    is_active: bool
    is_blocked: bool
    last_login: datetime | None
    created_at: datetime
    updated_at: datetime

    # Додаткова інформація
    conversations_count: int = Field(default=0, description="Кількість розмов")
    emotion_entries_count: int = Field(default=0, description="Кількість записів емоцій")

    model_config = {"from_attributes": True}


class AdminUserListResponse(BaseModel):
    """Відповідь зі списком користувачів (з пагінацією)."""

    users: list[AdminUserRead]
    total: int = Field(description="Загальна кількість користувачів")
    page: int = Field(description="Поточна сторінка")
    per_page: int = Field(description="Кількість на сторінці")
    pages: int = Field(description="Загальна кількість сторінок")


class BlockUserRequest(BaseModel):
    """Запит на блокування/розблокування."""

    is_blocked: bool = Field(description="True — заблокувати, False — розблокувати")
    reason: str | None = Field(
        default=None,
        max_length=500,
        description="Причина блокування (опціонально)",
    )


class BlockUserResponse(BaseModel):
    """Відповідь після блокування/розблокування."""

    id: uuid.UUID
    email: str | None
    is_blocked: bool
    message: str


# ── Статистика ──

class CrisisStats(BaseModel):
    """Статистика кризових подій."""

    total_crisis_messages: int = Field(description="Загальна кількість кризових повідомлень")
    by_level: dict[str, int] = Field(
        description="Кількість за рівнями: low, medium, high, critical",
    )


class SystemStats(BaseModel):
    """Статистика системи."""

    total_users: int = Field(description="Загальна кількість користувачів")
    active_users: int = Field(description="Активні користувачі")
    blocked_users: int = Field(description="Заблоковані користувачі")
    total_conversations: int = Field(description="Загальна кількість розмов")
    active_conversations: int = Field(description="Активні розмови")
    total_messages: int = Field(description="Загальна кількість повідомлень")
    total_emotion_entries: int = Field(description="Загальна кількість записів емоцій")
    crisis: CrisisStats = Field(description="Кризова статистика")
    users_registered_last_7_days: int = Field(description="Нових користувачів за 7 днів")
    users_registered_last_30_days: int = Field(description="Нових користувачів за 30 днів")


# ── Здоров'я системи ──

class ServiceHealth(BaseModel):
    """Стан окремого сервісу."""

    status: str = Field(description="ok | error | unavailable")
    latency_ms: float | None = Field(default=None, description="Затримка в мілісекундах")
    detail: str | None = Field(default=None, description="Додаткова інформація")


class SystemHealth(BaseModel):
    """Здоров'я системи."""

    status: str = Field(description="healthy | degraded | unhealthy")
    uptime_seconds: float = Field(description="Час роботи сервера в секундах")
    database: ServiceHealth
    redis: ServiceHealth
    version: str
    environment: str


# ── База знань (RAG) ──

class KnowledgeDocumentRead(BaseModel):
    """Інформація про документ бази знань."""

    id: uuid.UUID
    title: str
    category: KnowledgeCategory
    source: str | None
    status: KnowledgeStatus
    chunk_count: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeDocumentListResponse(BaseModel):
    """Список документів бази знань."""

    documents: list[KnowledgeDocumentRead]
    total: int


class KnowledgeUploadResponse(BaseModel):
    """Відповідь після завантаження документа."""

    id: uuid.UUID
    title: str
    status: KnowledgeStatus
    message: str



