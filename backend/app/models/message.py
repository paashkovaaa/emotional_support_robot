"""Модель повідомлення."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class MessageSender(str, enum.Enum):
    """Хто відправив повідомлення."""

    USER = "user"
    BOT = "bot"


class CrisisLevel(str, enum.Enum):
    """Рівень кризового ризику."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Message(Base):
    """Таблиця повідомлень."""

    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender: Mapped[MessageSender] = mapped_column(
        Enum(MessageSender, name="message_sender"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Аналіз емоцій ──
    emotion_analysis: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Результат аналізу емоцій повідомлення",
    )

    # ── Кризовий стан ──
    crisis_level: Mapped[CrisisLevel] = mapped_column(
        Enum(CrisisLevel, name="crisis_level"),
        default=CrisisLevel.NONE,
        server_default=CrisisLevel.NONE.name,
        nullable=False,
    )
    is_crisis: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    # ── Зв'язки ──
    conversation: Mapped["Conversation"] = relationship(  # noqa: F821
        back_populates="messages",
    )

    def __repr__(self) -> str:
        preview = self.content[:50] if self.content else ""
        return f"<Message id={self.id} sender={self.sender} preview='{preview}'>"
