"""Модель профілю користувача."""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class CommunicationStyle(str, enum.Enum):
    """Стиль спілкування."""

    ANALYTICAL = "analytical"
    FRIENDLY = "friendly"
    BALANCED = "balanced"


class Gender(str, enum.Enum):
    """Стать."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class Profile(Base):
    """Таблиця профілів (результати опитування та персональні дані)."""

    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    nickname: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[Gender | None] = mapped_column(
        Enum(Gender, name="gender"),
        nullable=True,
    )

    # ── Результати опитування ──
    communication_style: Mapped[CommunicationStyle] = mapped_column(
        Enum(CommunicationStyle, name="communication_style"),
        default=CommunicationStyle.BALANCED,
        server_default=CommunicationStyle.BALANCED.name,
        nullable=False,
    )
    life_area: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Сфера життя для покращення",
    )
    concern: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Що найбільше бентежить",
    )
    works_with_psychologist: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )
    survey_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    # ── Зв'язки ──
    user: Mapped["User"] = relationship(back_populates="profile")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Profile id={self.id} nickname={self.nickname}>"
