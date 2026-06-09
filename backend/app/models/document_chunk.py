"""Модель чанків документів для RAG (векторна база знань)."""

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base

# Розмірність ембедінгів paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DIM = 384


class DocumentChunk(Base):
    """Таблиця чанків документів із векторними ембедінгами для RAG-пошуку."""

    __tablename__ = "document_chunks"

    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_base.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Текст чанку",
    )
    embedding: Mapped[list[float]] = mapped_column(
        Vector(EMBEDDING_DIM),
        nullable=False,
        comment="Векторне представлення чанку (384 виміри)",
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Порядковий номер чанку у документі",
    )
    chunk_metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Метадані: номер сторінки, позиція тощо",
    )

    def __repr__(self) -> str:
        return (
            f"<DocumentChunk id={self.id} "
            f"kb_id={self.knowledge_base_id} idx={self.chunk_index}>"
        )

