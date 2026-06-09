"""Модуль вимірювання продуктивності для збору даних тестування.

Записує структуровані JSON Lines у файл logs/perf_metrics.jsonl.
Кожен рядок — окрема метрика з типом, часом і параметрами.

Типи метрик:
  - ws_message       : повний цикл обробки WebSocket-повідомлення
  - streaming_first  : час до першого токена від Claude
  - streaming_total  : загальний час стрімінгу та кількість токенів
  - rag_search       : час семантичного пошуку, кількість знайдених чанків
  - rag_context      : час синтезу Gemini-контексту
  - crisis_detection : час перевірки кризового стану та результат
  - auth_login       : час автентифікації
  - document_process : час обробки документа, кількість чанків
"""

from __future__ import annotations

import json
import time
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Директорія для файлів логів (поряд з backend/)
_LOGS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "logs"
_LOGS_DIR.mkdir(parents=True, exist_ok=True)

_PERF_FILE = _LOGS_DIR / "perf_metrics.jsonl"


def _write(record: dict[str, Any]) -> None:
    """Записує один JSON-рядок у файл метрик."""
    record["ts"] = datetime.now(timezone.utc).isoformat()
    try:
        with _PERF_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass  # Логування не повинно валити основну логіку


# ─────────────────────────────────────────────────────
# Допоміжні контекстні менеджери
# ─────────────────────────────────────────────────────

@contextmanager
def measure(event: str, **extra: Any):
    """Синхронний контекстний менеджер для вимірювання часу блоку коду.

    Приклад:
        with measure("crisis_detection", message_len=len(text)) as m:
            result = detector.check(text)
            m["level"] = result.crisis_level
    """
    record: dict[str, Any] = {"event": event, **extra}
    start = time.perf_counter()
    try:
        yield record
    finally:
        record["duration_ms"] = round((time.perf_counter() - start) * 1000, 2)
        _write(record)


@asynccontextmanager
async def ameasure(event: str, **extra: Any):
    """Асинхронний контекстний менеджер для вимірювання часу async-блоку.

    Приклад:
        async with ameasure("rag_search", query_len=len(q)) as m:
            results = await rag.search_chunks(q)
            m["chunks_found"] = len(results)
    """
    record: dict[str, Any] = {"event": event, **extra}
    start = time.perf_counter()
    try:
        yield record
    finally:
        record["duration_ms"] = round((time.perf_counter() - start) * 1000, 2)
        _write(record)


# ─────────────────────────────────────────────────────
# Спеціалізовані функції запису
# ─────────────────────────────────────────────────────

def record_streaming_chunk(
    conversation_id: str,
    chunk_index: int,
    elapsed_ms: float,
    is_first: bool = False,
) -> None:
    """Записує метрику окремого стрімінг-токена."""
    if is_first or chunk_index % 20 == 0:
        # Пишемо не кожен токен, щоб не роздувати файл
        _write({
            "event": "streaming_chunk",
            "conversation_id": conversation_id[:8],
            "chunk_index": chunk_index,
            "elapsed_ms": round(elapsed_ms, 2),
            "is_first": is_first,
        })


def record_streaming_complete(
    conversation_id: str,
    total_ms: float,
    first_token_ms: float,
    total_chunks: int,
    response_len: int,
    had_rag: bool,
) -> None:
    """Записує підсумкову метрику завершеного стрімінгу."""
    _write({
        "event": "streaming_total",
        "conversation_id": conversation_id[:8],
        "total_ms": round(total_ms, 2),
        "first_token_ms": round(first_token_ms, 2),
        "total_chunks": total_chunks,
        "response_len": response_len,
        "had_rag": had_rag,
    })


def record_rag_search(
    query_len: int,
    search_ms: float,
    chunks_found: int,
    top_distance: float | None,
    synthesis_ms: float | None,
    had_gemini: bool,
) -> None:
    """Записує метрику RAG-пошуку."""
    _write({
        "event": "rag_search",
        "query_len": query_len,
        "search_ms": round(search_ms, 2),
        "chunks_found": chunks_found,
        "top_distance": round(top_distance, 4) if top_distance is not None else None,
        "synthesis_ms": round(synthesis_ms, 2) if synthesis_ms is not None else None,
        "had_gemini": had_gemini,
    })


def record_crisis(
    message_len: int,
    detection_ms: float,
    level: str,
    matched_count: int,
) -> None:
    """Записує метрику виявлення кризового стану."""
    _write({
        "event": "crisis_detection",
        "message_len": message_len,
        "detection_ms": round(detection_ms, 2),
        "level": level,
        "matched_count": matched_count,
    })


def record_ws_cycle(
    conversation_id: str,
    total_ms: float,
    was_crisis: bool,
    crisis_level: str,
    message_len: int,
) -> None:
    """Записує метрику повного циклу WebSocket-повідомлення."""
    _write({
        "event": "ws_message",
        "conversation_id": conversation_id[:8],
        "total_ms": round(total_ms, 2),
        "was_crisis": was_crisis,
        "crisis_level": crisis_level,
        "message_len": message_len,
    })

