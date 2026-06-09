from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "e2e1c4519c86"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 384


def upgrade() -> None:
    # ── pgvector extension ──
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── document_chunks table ──
    op.create_table(
        "document_chunks",
        sa.Column("knowledge_base_id", sa.UUID(), nullable=False),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
            comment="Текст чанку",
        ),
        sa.Column(
            "embedding",
            Vector(EMBEDDING_DIM),
            nullable=False,
            comment="Векторне представлення чанку (384 виміри)",
        ),
        sa.Column(
            "chunk_index",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Порядковий номер чанку у документі",
        ),
        sa.Column(
            "chunk_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Метадані: номер сторінки, позиція тощо",
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["knowledge_base_id"],
            ["knowledge_base.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_document_chunks_id"),
        "document_chunks",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_chunks_knowledge_base_id"),
        "document_chunks",
        ["knowledge_base_id"],
        unique=False,
    )

    # ── HNSW-індекс для векторного пошуку (cosine distance) ──
    # HNSW швидший за IVFFlat для невеликих датасетів, не вимагає тренування
    op.execute(
        """
        CREATE INDEX ix_document_chunks_embedding_hnsw
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")
    op.drop_index(
        op.f("ix_document_chunks_knowledge_base_id"),
        table_name="document_chunks",
    )
    op.drop_index(
        op.f("ix_document_chunks_id"),
        table_name="document_chunks",
    )
    op.drop_table("document_chunks")
    # Не видаляємо vector extension — може використовуватися іншими таблицями

