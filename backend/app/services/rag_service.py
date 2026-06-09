"""RAG-сервіс — завантаження документів, ембедінги, векторний пошук.

Архітектура:
  1. Завантаження PDF/TXT/DOCX → LangChain loaders
  2. Розбиття на чанки → RecursiveCharacterTextSplitter
  3. Генерація ембедінгів → sentence-transformers (локально)
  4. Збереження → PostgreSQL + pgvector (таблиця document_chunks)
  5. Пошук → cosine similarity через HNSW-індекс
  6. Синтез контексту → Google Gemini 2.5 Flash

Модуль RAG та Бази Знань: Google Gemini 2.5 Flash
  - Завантаження та аналіз великих PDF (книг з психології)
  - Пошук методик та синтез відповіді на основі книг
  - Передає релевантний контекст в основний чат (Claude)
"""

from __future__ import annotations

import asyncio
import functools
import time
import uuid
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.logging import get_logger
from backend.app.core.perf_logger import record_rag_search
from backend.app.models.document_chunk import EMBEDDING_DIM, DocumentChunk
from backend.app.models.knowledge_base import KnowledgeBase, KnowledgeStatus

logger = get_logger(__name__)

# ── Налаштування чанкування ──
CHUNK_SIZE = 800          # символів на чанк
CHUNK_OVERLAP = 100       # перекриття між чанками
MAX_SEARCH_CHUNKS = 5     # к-сть чанків для RAG-контексту
SIMILARITY_THRESHOLD = 0.25  # мінімальна схожість (cosine distance ≤ threshold)

# ── Директорія для завантажених файлів ──
UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


class RagService:
    """Сервіс RAG: завантаження документів, ембедінги, пошук, синтез Gemini."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._embedding_model: Any = None
        self._gemini_model: Any = None

    # ─────────────────────────────────────────────────
    # Lazy properties
    # ─────────────────────────────────────────────────

    @property
    def embedding_model(self):
        """Лінивий доступ до sentence-transformer моделі."""
        if self._embedding_model is None:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Завантаження embedding моделі: {settings.EMBEDDING_MODEL}")
            self._embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return self._embedding_model

    def _get_gemini_model(self):
        """Лінивий доступ до Gemini моделі."""
        if not settings.GEMINI_API_KEY:
            return None
        if self._gemini_model is None:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
        return self._gemini_model

    # ─────────────────────────────────────────────────
    # Публічний API
    # ─────────────────────────────────────────────────

    async def process_document(
        self,
        file_path: Path,
        knowledge_base_id: uuid.UUID,
    ) -> int:
        """Обробляє завантажений документ: читає → ділить → ембедить → зберігає.

        Args:
            file_path: Шлях до збереженого файлу.
            knowledge_base_id: ID запису в knowledge_base.

        Returns:
            Кількість збережених чанків.

        Raises:
            ValueError: Якщо формат файлу не підтримується.
            RuntimeError: Якщо обробка не вдалась.
        """
        # Оновлюємо статус → PROCESSING
        await self._update_kb_status(knowledge_base_id, KnowledgeStatus.PROCESSING)

        try:
            # 1. Завантаження тексту з файлу
            raw_docs = await asyncio.get_event_loop().run_in_executor(
                None, functools.partial(self._load_document, file_path)
            )

            if not raw_docs:
                raise ValueError(f"Документ порожній або не вдалось зчитати: {file_path}")

            # 2. Розбиття на чанки
            chunks = self._split_into_chunks(raw_docs)
            logger.info(f"Документ розбито на {len(chunks)} чанків")

            # 3. Генерація ембедінгів (в окремому потоці — CPU-інтенсивна операція)
            texts = [c["content"] for c in chunks]
            embeddings = await asyncio.get_event_loop().run_in_executor(
                None,
                functools.partial(self._embed_texts, texts),
            )

            # 4. Очищуємо попередні чанки (для re-processing)
            await self.db.execute(
                delete(DocumentChunk).where(
                    DocumentChunk.knowledge_base_id == knowledge_base_id
                )
            )

            # 5. Зберігаємо чанки в БД порціями (batch insert)
            BATCH_SIZE = 50
            for i in range(0, len(chunks), BATCH_SIZE):
                batch_chunks = chunks[i:i + BATCH_SIZE]
                batch_embeddings = embeddings[i:i + BATCH_SIZE]

                db_chunks = [
                    DocumentChunk(
                        knowledge_base_id=knowledge_base_id,
                        content=chunk["content"],
                        embedding=emb.tolist(),
                        chunk_index=i + j,
                        chunk_metadata=chunk.get("metadata"),
                    )
                    for j, (chunk, emb) in enumerate(
                        zip(batch_chunks, batch_embeddings)
                    )
                ]
                self.db.add_all(db_chunks)
                await self.db.flush()

            await self.db.commit()

            # 6. Оновлюємо статус → ACTIVE
            await self._update_kb_status(
                knowledge_base_id,
                KnowledgeStatus.ACTIVE,
                chunk_count=len(chunks),
            )

            logger.info(
                f"Документ {knowledge_base_id} успішно оброблено: {len(chunks)} чанків"
            )
            return len(chunks)

        except Exception as exc:
            await self.db.rollback()
            await self._update_kb_status(knowledge_base_id, KnowledgeStatus.ERROR)
            logger.error(f"Помилка обробки документа {knowledge_base_id}: {exc}")
            raise

    async def search_chunks(
        self,
        query: str,
        limit: int = MAX_SEARCH_CHUNKS,
    ) -> list[dict]:
        """Векторний пошук релевантних чанків.

        Args:
            query: Текст запиту (повідомлення користувача).
            limit: Максимальна кількість результатів.

        Returns:
            Список dict: {content, knowledge_base_id, chunk_index, distance, metadata}.
        """
        # Спочатку перевіряємо чи є активні чанки (швидкий DB-запит)
        # щоб не завантажувати embedding-модель без потреби
        count_stmt = select(func.count()).select_from(DocumentChunk)
        result = await self.db.execute(count_stmt)
        total_chunks = result.scalar_one()

        if total_chunks == 0:
            return []

        # Ембедуємо запит у потоці (лише якщо є чанки)
        query_embedding = await asyncio.get_event_loop().run_in_executor(
            None,
            functools.partial(self._embed_texts, [query]),
        )
        query_vec = query_embedding[0].tolist()

        # Cosine distance через pgvector оператор <=>
        # Нижче значення = більш схожі
        distance_col = text(
            f"embedding <=> '{query_vec}'::vector({EMBEDDING_DIM})"
        ).label("distance")

        stmt = (
            select(
                DocumentChunk.id,
                DocumentChunk.content,
                DocumentChunk.knowledge_base_id,
                DocumentChunk.chunk_index,
                DocumentChunk.chunk_metadata,
                distance_col,
            )
            .order_by(text(f"embedding <=> '{query_vec}'::vector({EMBEDDING_DIM})"))
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        chunks = []
        for row in rows:
            distance = float(row.distance)
            # Фільтруємо за порогом схожості
            if distance <= SIMILARITY_THRESHOLD:
                chunks.append({
                    "id": str(row.id),
                    "content": row.content,
                    "knowledge_base_id": str(row.knowledge_base_id),
                    "chunk_index": row.chunk_index,
                    "distance": distance,
                    "metadata": row.chunk_metadata,
                })

        return chunks

    async def get_rag_context(self, query: str) -> str | None:
        """Знаходить релевантні чанки та синтезує контекст через Gemini."""
        search_start = time.perf_counter()
        chunks = await self.search_chunks(query)
        search_ms = (time.perf_counter() - search_start) * 1000

        top_distance = chunks[0]["distance"] if chunks else None

        if not chunks:
            record_rag_search(
                query_len=len(query),
                search_ms=search_ms,
                chunks_found=0,
                top_distance=None,
                synthesis_ms=None,
                had_gemini=False,
            )
            return None

        # Формуємо сирий контекст з чанків
        raw_context = "\n\n---\n\n".join(
            f"[Фрагмент {i+1}]:\n{chunk['content']}"
            for i, chunk in enumerate(chunks)
        )

        # Якщо Gemini доступний — синтезуємо стислий контекст
        gemini = self._get_gemini_model()
        synthesis_ms = None
        had_gemini = False
        if gemini:
            try:
                synth_start = time.perf_counter()
                synthesized = await asyncio.get_event_loop().run_in_executor(
                    None,
                    functools.partial(
                        self._synthesize_with_gemini, gemini, query, raw_context
                    ),
                )
                synthesis_ms = (time.perf_counter() - synth_start) * 1000
                had_gemini = True
                record_rag_search(
                    query_len=len(query),
                    search_ms=search_ms,
                    chunks_found=len(chunks),
                    top_distance=top_distance,
                    synthesis_ms=synthesis_ms,
                    had_gemini=had_gemini,
                )
                if synthesized:
                    return synthesized
            except Exception as exc:
                logger.warning(f"Gemini синтез не вдався, використовуємо raw chunks: {exc}")

        record_rag_search(
            query_len=len(query),
            search_ms=search_ms,
            chunks_found=len(chunks),
            top_distance=top_distance,
            synthesis_ms=synthesis_ms,
            had_gemini=had_gemini,
        )

        # Fallback: повертаємо перші 2000 символів сирого контексту
        return raw_context[:2000] if raw_context else None

    async def delete_document(self, knowledge_base_id: uuid.UUID) -> None:
        """Видаляє документ та всі його чанки.

        Чанки видаляються автоматично через CASCADE FK.
        """
        stmt = select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
        result = await self.db.execute(stmt)
        kb = result.scalar_one_or_none()

        if kb is None:
            return

        # Видаляємо файл з диску якщо є
        if kb.file_path:
            file_path = Path(kb.file_path)
            if file_path.exists():
                try:
                    file_path.unlink()
                    logger.info(f"Файл видалено: {file_path}")
                except OSError as exc:
                    logger.warning(f"Не вдалося видалити файл {file_path}: {exc}")

        await self.db.delete(kb)
        await self.db.commit()

    async def list_documents(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """Повертає список документів бази знань."""
        stmt = (
            select(KnowledgeBase)
            .order_by(KnowledgeBase.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        docs = result.scalars().all()

        return [
            {
                "id": str(d.id),
                "title": d.title,
                "category": d.category.value,
                "source": d.source,
                "status": d.status.value,
                "chunk_count": d.chunk_count,
                "created_at": d.created_at.isoformat(),
            }
            for d in docs
        ]

    async def count_documents(self) -> int:
        """Повертає кількість документів у базі знань."""
        stmt = select(func.count()).select_from(KnowledgeBase)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    # ─────────────────────────────────────────────────
    # Приватні методи (синхронні, для run_in_executor)
    # ─────────────────────────────────────────────────

    @staticmethod
    def _load_document(file_path: Path) -> list[dict]:
        """Завантажує документ і повертає список {content, metadata}."""
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(str(file_path))
            docs = loader.load()
        elif suffix == ".txt":
            from langchain_community.document_loaders import TextLoader
            loader = TextLoader(str(file_path), encoding="utf-8")
            docs = loader.load()
        elif suffix in (".docx", ".doc"):
            from langchain_community.document_loaders import Docx2txtLoader
            loader = Docx2txtLoader(str(file_path))
            docs = loader.load()
        else:
            raise ValueError(f"Непідтримуваний формат файлу: {suffix}")

        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
            }
            for doc in docs
            if doc.page_content.strip()
        ]

    @staticmethod
    def _split_into_chunks(raw_docs: list[dict]) -> list[dict]:
        """Розбиває документ на чанки заданого розміру."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
        )

        chunks = []
        for doc in raw_docs:
            texts = splitter.split_text(doc["content"])
            for text_chunk in texts:
                if text_chunk.strip():
                    chunks.append({
                        "content": text_chunk.strip(),
                        "metadata": doc.get("metadata"),
                    })

        return chunks

    def _embed_texts(self, texts: list[str]) -> np.ndarray:
        """Генерує ембедінги для списку текстів."""
        return self.embedding_model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            normalize_embeddings=True,  # Нормалізація для cosine similarity
        )

    @staticmethod
    def _synthesize_with_gemini(gemini_model, query: str, raw_context: str) -> str | None:
        """Синтезує релевантний контекст через Gemini (синхронний виклик)."""
        prompt = f"""Ти — помічник, який аналізує уривки з книг з психології.
На основі наданих уривків, підготуй СТИСЛИЙ (до 300 слів) але інформативний контекст,
який допоможе AI-боту для емоційної підтримки дати більш обґрунтовану відповідь.

Питання/запит користувача: {query}

Уривки з книг:
{raw_context}

Підготуй стислий контекст українською мовою. Тільки факти та методики.
Не включай вступних слів типу "Ось відповідь" або "На основі уривків".
Якщо уривки не релевантні — поверни пусте значення."""

        response = gemini_model.generate_content(prompt)
        text = response.text.strip() if response.text else ""

        # Якщо Gemini повертає "пусте значення" або дуже коротку відповідь
        if len(text) < 20:
            return None

        return text

    async def _update_kb_status(
        self,
        knowledge_base_id: uuid.UUID,
        status: KnowledgeStatus,
        chunk_count: int | None = None,
    ) -> None:
        """Оновлює статус запису в knowledge_base."""
        stmt = select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
        result = await self.db.execute(stmt)
        kb = result.scalar_one_or_none()

        if kb:
            kb.status = status
            if chunk_count is not None:
                kb.chunk_count = chunk_count
            await self.db.commit()

