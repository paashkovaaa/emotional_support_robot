"""Модель бази знань (для RAG)."""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class KnowledgeCategory(str, enum.Enum):
    """Категорія матеріалу."""

    CBT = "cbt"  # Когнітивно-поведінкова терапія
    ACT = "act"  # Терапія прийняття та відповідальності
    DBT = "dbt"  # Діалектична поведінкова терапія
    CRISIS = "crisis"  # Кризова інтервенція
    SELF_HELP = "self_help"  # Самодопомога
    ARTICLE = "article"  # Стаття
    BOOK = "book"  # Книга
    OTHER = "other"


class KnowledgeStatus(str, enum.Enum):
    """Статус матеріалу."""

    ACTIVE = "active"
    PROCESSING = "processing"
    ARCHIVED = "archived"
    ERROR = "error"


class KnowledgeBase(Base):
    """Таблиця бази знань — матеріали для RAG."""

    __tablename__ = "knowledge_base"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[KnowledgeCategory] = mapped_column(
        Enum(KnowledgeCategory, name="knowledge_category"),
        default=KnowledgeCategory.OTHER,
        nullable=False,
    )
    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Повний текст матеріалу",
    )
    source: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Джерело матеріалу (URL, назва книги)",
    )
    file_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Шлях до завантаженого файлу",
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[KnowledgeStatus] = mapped_column(
        Enum(KnowledgeStatus, name="knowledge_status"),
        default=KnowledgeStatus.PROCESSING,
        server_default=KnowledgeStatus.PROCESSING.name,
        nullable=False,
    )
    chunk_count: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="Кількість чанків після розбиття",
    )

    def __repr__(self) -> str:
        return f"<KnowledgeBase id={self.id} title='{self.title[:30]}'>"
