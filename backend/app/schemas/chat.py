"""Pydantic-схеми для чату (розмови та повідомлення)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from backend.app.models.conversation import ChatType, ConversationStatus
from backend.app.models.message import CrisisLevel, MessageSender


# ── Conversations ──


class ConversationCreate(BaseModel):
    """Створення нової розмови."""

    title: str | None = Field(default=None, max_length=255)
    chat_type: ChatType = ChatType.TEXT


class ConversationRead(BaseModel):
    """Читання розмови."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str | None
    chat_type: ChatType
    status: ConversationStatus
    started_at: datetime
    ended_at: datetime | None
    summary: str | None
    message_count: int = 0

    model_config = {"from_attributes": True}


class ConversationListItem(BaseModel):
    """Елемент списку розмов (без summary для швидкості)."""

    id: uuid.UUID
    title: str | None
    chat_type: ChatType
    status: ConversationStatus
    started_at: datetime
    ended_at: datetime | None
    message_count: int = 0
    last_message_preview: str | None = None

    model_config = {"from_attributes": True}


class ConversationUpdate(BaseModel):
    """Оновлення розмови."""

    title: str | None = Field(default=None, max_length=255)


# ── Messages ──


class MessageCreate(BaseModel):
    """Створення повідомлення від користувача."""

    content: str = Field(min_length=1, max_length=5000)


class MessageRead(BaseModel):
    """Читання повідомлення."""

    id: uuid.UUID
    conversation_id: uuid.UUID
    sender: MessageSender
    content: str
    sent_at: datetime
    crisis_level: CrisisLevel
    is_crisis: bool

    model_config = {"from_attributes": True}


class MessagesListResponse(BaseModel):
    """Список повідомлень розмови."""

    messages: list[MessageRead]
    total: int
    conversation_id: uuid.UUID


# ── WebSocket ──


class WSIncoming(BaseModel):
    """Вхідне WebSocket-повідомлення від клієнта."""

    type: str = "message"  # "message" | "typing" | "end_conversation"
    content: str | None = None


class WSOutgoing(BaseModel):
    """Вихідне WebSocket-повідомлення до клієнта."""

    type: str  # "message" | "chunk" | "typing" | "error" | "conversation_ended"
    content: str | None = None
    sender: MessageSender | None = None
    message_id: str | None = None
    is_crisis: bool = False
    crisis_level: CrisisLevel | None = None

