"""Модель запису щоденника емоцій."""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class EmotionEntry(Base):
    """Таблиця записів щоденника емоцій."""

    __tablename__ = "emotion_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "entry_date", name="uq_user_entry_date"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entry_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Дата запису",
    )
    emoji: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Емодзі емоції за день",
    )
    user_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Опис стану від користувача",
    )
    bot_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Опис стану згенерований ботом",
    )
    emotion_tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(50)),
        nullable=True,
        comment="Теги емоцій: стрес, щастя, злість, тривога тощо",
    )

    # ── Зв'язки ──
    user: Mapped["User"] = relationship(back_populates="emotion_entries")  # noqa: F821

    def __repr__(self) -> str:
        return f"<EmotionEntry id={self.id} date={self.entry_date} emoji={self.emoji}>"
