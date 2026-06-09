"""API роутер адмін-панелі."""

import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, Query, Request, UploadFile

from backend.app.api.deps import CurrentAdmin, DbSession
from backend.app.models.knowledge_base import KnowledgeCategory, KnowledgeStatus
from backend.app.models.user import UserRole
from backend.app.schemas.admin import (
    AdminUserListResponse,
    BlockUserRequest,
    BlockUserResponse,
    KnowledgeDocumentListResponse,
    KnowledgeDocumentRead,
    KnowledgeUploadResponse,
    SystemHealth,
    SystemStats,
)
from backend.app.services.admin_service import AdminService
from backend.app.services.cleanup_service import DataCleanupService
from backend.app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ──────────────────────────────────────────────
# Користувачі
# ──────────────────────────────────────────────


@router.get(
    "/users",
    response_model=AdminUserListResponse,
    summary="Список користувачів",
)
async def list_users(
    admin: CurrentAdmin,
    db: DbSession,
    page: int = Query(default=1, ge=1, description="Номер сторінки"),
    per_page: int = Query(default=20, ge=1, le=100, description="Кількість на сторінці"),
    search: str | None = Query(default=None, description="Пошук за email"),
    role: UserRole | None = Query(default=None, description="Фільтр за роллю"),
    is_blocked: bool | None = Query(default=None, description="Фільтр за статусом блокування"),
    sort_by: str = Query(
        default="created_at",
        description="Поле сортування: created_at, email, last_login, role",
    ),
    sort_order: str = Query(
        default="desc",
        description="Напрямок: asc або desc",
    ),
):
    """Повертає список усіх користувачів з пагінацією.

    Доступно лише адміністраторам.

    Підтримує:
    - **Пошук** за email (частковий збіг)
    - **Фільтрацію** за роллю та статусом блокування
    - **Сортування** за різними полями
    - **Пагінацію**
    """
    service = AdminService(db)
    return await service.get_users(
        page=page,
        per_page=per_page,
        search=search,
        role=role,
        is_blocked=is_blocked,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.patch(
    "/users/{user_id}/block",
    response_model=BlockUserResponse,
    summary="Заблокувати / розблокувати користувача",
)
async def block_user(
    user_id: uuid.UUID,
    body: BlockUserRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """Блокує або розблоковує акаунт користувача.

    - Заблокований користувач не зможе увійти в систему.
    - Неможливо заблокувати адміністратора або себе.

    **is_blocked**: `true` — заблокувати, `false` — розблокувати.
    """
    service = AdminService(db)
    return await service.block_user(
        user_id=user_id,
        is_blocked=body.is_blocked,
        admin_id=admin.id,
        reason=body.reason,
    )


# ──────────────────────────────────────────────
# Статистика
# ──────────────────────────────────────────────


@router.get(
    "/stats",
    response_model=SystemStats,
    summary="Статистика системи",
)
async def get_system_stats(
    admin: CurrentAdmin,
    db: DbSession,
):
    """Повертає загальну статистику системи.

    Включає:
    - Кількість користувачів (загальна, активні, заблоковані)
    - Кількість розмов та повідомлень
    - Кількість записів щоденника емоцій
    - Кризову статистику (за рівнями ризику)
    - Динаміку реєстрацій (7 та 30 днів)
    """
    service = AdminService(db)
    return await service.get_stats()


# ──────────────────────────────────────────────
# Здоров'я системи
# ──────────────────────────────────────────────


@router.get(
    "/health",
    response_model=SystemHealth,
    summary="Моніторинг здоров'я системи",
)
async def get_system_health(
    admin: CurrentAdmin,
    db: DbSession,
    request: Request,
):
    """Перевіряє стан всіх компонентів системи.

    Повертає:
    - **database**: стан PostgreSQL (статус, затримка)
    - **redis**: стан Redis (статус, затримка)
    - **uptime_seconds**: час роботи сервера
    - **status**: загальний стан (healthy / degraded / unhealthy)
    """
    redis_client = getattr(request.app.state, "redis", None)
    service = AdminService(db)
    return await service.get_health(redis_client)


# ──────────────────────────────────────────────
# Очищення даних
# ──────────────────────────────────────────────


@router.post(
    "/cleanup",
    summary="Ручне очищення застарілих даних",
)
async def run_data_cleanup(
    admin: CurrentAdmin,
    db: DbSession,
):
    """Запускає ручне очищення застарілих даних.

    Видаляє завершені розмови та їх повідомлення,
    які старші за CONVERSATION_HISTORY_DAYS (за замовчуванням 30 днів).

    Доступно лише адміністраторам.
    """
    service = DataCleanupService(db)
    return await service.cleanup_old_conversations()


# ──────────────────────────────────────────────
# База знань (RAG)
# ──────────────────────────────────────────────

_ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".doc"}
_MAX_FILE_SIZE_MB = 50


async def _process_document_bg(file_path: Path, knowledge_base_id: uuid.UUID) -> None:
    """Фонова задача: обробка документа (chunking + embedding + storing)."""
    from backend.app.database import async_session_factory
    from backend.app.services.rag_service import RagService

    async with async_session_factory() as db:
        rag = RagService(db)
        try:
            chunk_count = await rag.process_document(file_path, knowledge_base_id)
            logger.info(f"Документ {knowledge_base_id} оброблено: {chunk_count} чанків")
        except Exception as exc:
            logger.error(f"Помилка фонової обробки документа {knowledge_base_id}: {exc}")


@router.post(
    "/knowledge",
    response_model=KnowledgeUploadResponse,
    status_code=201,
    summary="Завантажити документ у базу знань",
)
async def upload_knowledge_document(
    admin: CurrentAdmin,
    db: DbSession,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF, TXT або DOCX файл"),
    title: str = Form(..., max_length=500, description="Назва документа"),
    category: KnowledgeCategory = Form(
        default=KnowledgeCategory.OTHER,
        description="Категорія: cbt, act, dbt, crisis, self_help, article, book, other",
    ),
    source: str | None = Form(default=None, max_length=500, description="Джерело/автор"),
):
    """Завантажує документ у базу знань та запускає фонову обробку.

    **Підтримувані формати:** PDF, TXT, DOCX

    Обробка (chunking + ембедінги) відбувається у фоновому режимі.
    Статус документа: `processing` → `active` (після успішної обробки) або `error`.

    Доступно лише адміністраторам.
    """
    from backend.app.models.knowledge_base import KnowledgeBase
    from backend.app.services.rag_service import UPLOADS_DIR

    # Перевірка розширення
    if not file.filename:
        from backend.app.core.exceptions import BadRequestError
        raise BadRequestError("Ім'я файлу не може бути порожнім")

    file_suffix = Path(file.filename).suffix.lower()
    if file_suffix not in _ALLOWED_EXTENSIONS:
        from backend.app.core.exceptions import BadRequestError
        raise BadRequestError(
            f"Непідтримуваний формат: {file_suffix}. "
            f"Дозволено: {', '.join(_ALLOWED_EXTENSIONS)}"
        )

    # Читаємо вміст
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > _MAX_FILE_SIZE_MB:
        from backend.app.core.exceptions import BadRequestError
        raise BadRequestError(
            f"Файл занадто великий: {size_mb:.1f} МБ. "
            f"Максимум: {_MAX_FILE_SIZE_MB} МБ"
        )

    # Зберігаємо файл
    safe_name = f"{uuid.uuid4()}{file_suffix}"
    file_path = UPLOADS_DIR / safe_name
    file_path.write_bytes(content)

    # Створюємо запис у БД
    kb = KnowledgeBase(
        title=title,
        category=category,
        source=source,
        file_path=str(file_path),
        uploaded_by=admin.id,
        status=KnowledgeStatus.PROCESSING,
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)

    # Запускаємо фонову обробку
    background_tasks.add_task(_process_document_bg, file_path, kb.id)

    return KnowledgeUploadResponse(
        id=kb.id,
        title=kb.title,
        status=kb.status,
        message=(
            f"Документ «{title}» ({size_mb:.1f} МБ) завантажено. "
            "Обробка розпочата у фоновому режимі."
        ),
    )


@router.get(
    "/knowledge",
    response_model=KnowledgeDocumentListResponse,
    summary="Список документів бази знань",
)
async def list_knowledge_documents(
    admin: CurrentAdmin,
    db: DbSession,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Повертає список усіх документів у базі знань.

    Доступно лише адміністраторам.
    """
    from backend.app.services.rag_service import RagService

    rag = RagService(db)
    docs_raw = await rag.list_documents(limit=limit, offset=offset)
    total = await rag.count_documents()

    from datetime import datetime
    docs = [
        KnowledgeDocumentRead(
            id=uuid.UUID(d["id"]),
            title=d["title"],
            category=KnowledgeCategory(d["category"]),
            source=d["source"],
            status=KnowledgeStatus(d["status"]),
            chunk_count=d["chunk_count"],
            created_at=datetime.fromisoformat(d["created_at"]),
        )
        for d in docs_raw
    ]

    return KnowledgeDocumentListResponse(documents=docs, total=total)


@router.get(
    "/knowledge/{doc_id}",
    response_model=KnowledgeDocumentRead,
    summary="Деталі документа бази знань",
)
async def get_knowledge_document(
    doc_id: uuid.UUID,
    admin: CurrentAdmin,
    db: DbSession,
):
    """Повертає деталі конкретного документа.

    Доступно лише адміністраторам.
    """
    from sqlalchemy import select
    from backend.app.models.knowledge_base import KnowledgeBase
    from backend.app.core.exceptions import NotFoundError

    stmt = select(KnowledgeBase).where(KnowledgeBase.id == doc_id)
    result = await db.execute(stmt)
    kb = result.scalar_one_or_none()

    if not kb:
        raise NotFoundError("Документ не знайдено")

    return KnowledgeDocumentRead(
        id=kb.id,
        title=kb.title,
        category=kb.category,
        source=kb.source,
        status=kb.status,
        chunk_count=kb.chunk_count,
        created_at=kb.created_at,
    )


@router.delete(
    "/knowledge/{doc_id}",
    status_code=204,
    summary="Видалити документ з бази знань",
)
async def delete_knowledge_document(
    doc_id: uuid.UUID,
    admin: CurrentAdmin,
    db: DbSession,
):
    """Видаляє документ, усі його чанки та файл з диску.

    Доступно лише адміністраторам.
    """
    from backend.app.services.rag_service import RagService

    rag = RagService(db)
    await rag.delete_document(doc_id)


@router.post(
    "/knowledge/{doc_id}/reprocess",
    response_model=KnowledgeUploadResponse,
    summary="Переобробити документ (re-embed)",
)
async def reprocess_knowledge_document(
    doc_id: uuid.UUID,
    admin: CurrentAdmin,
    db: DbSession,
    background_tasks: BackgroundTasks,
):
    """Запускає повторну обробку документа (перегенерація ембедінгів).

    Корисно після зміни моделі ембедінгів.
    Доступно лише адміністраторам.
    """
    from sqlalchemy import select
    from backend.app.models.knowledge_base import KnowledgeBase
    from backend.app.core.exceptions import NotFoundError

    stmt = select(KnowledgeBase).where(KnowledgeBase.id == doc_id)
    result = await db.execute(stmt)
    kb = result.scalar_one_or_none()

    if not kb:
        raise NotFoundError("Документ не знайдено")

    if not kb.file_path or not Path(kb.file_path).exists():
        from backend.app.core.exceptions import BadRequestError
        raise BadRequestError("Файл документа не знайдено на диску")

    background_tasks.add_task(_process_document_bg, Path(kb.file_path), kb.id)

    return KnowledgeUploadResponse(
        id=kb.id,
        title=kb.title,
        status=KnowledgeStatus.PROCESSING,
        message=f"Переобробка документа «{kb.title}» розпочата у фоновому режимі.",
    )
