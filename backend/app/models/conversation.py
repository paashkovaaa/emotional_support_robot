"""Модель розмови."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class ChatType(str, enum.Enum):
    """Тип чату."""

    TEXT = "text"
    VOICE = "voice"


class ConversationStatus(str, enum.Enum):
    """Статус розмови."""

    ACTIVE = "active"
    ENDED = "ended"


class Conversation(Base):
    """Таблиця розмов."""

    __tablename__ = "conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    chat_type: Mapped[ChatType] = mapped_column(
        Enum(ChatType, name="chat_type"),
        default=ChatType.TEXT,
        server_default=ChatType.TEXT.name,
        nullable=False,
    )
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus, name="conversation_status"),
        default=ConversationStatus.ACTIVE,
        server_default=ConversationStatus.ACTIVE.name,
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Короткий висновок розмови для контекстної пам'яті",
    )

    # ── Зв'язки ──
    user: Mapped["User"] = relationship(back_populates="conversations")  # noqa: F821
    messages: Mapped[list["Message"]] = relationship(  # noqa: F821
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.sent_at",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} status={self.status}>"
