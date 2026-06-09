"""API роутер щоденника емоцій."""

import uuid
from datetime import date

from fastapi import APIRouter, Query

from backend.app.api.deps import CurrentUser, DbSession
from backend.app.schemas.emotion import (
    EmotionEntryCreate,
    EmotionEntryRead,
    EmotionEntryUpdate,
    EmotionGenerateRequest,
    EmotionGenerateResponse,
)
from backend.app.services.emotion_service import EmotionService

router = APIRouter()


@router.post(
    "/",
    response_model=EmotionEntryRead,
    status_code=201,
    summary="Створити запис у щоденнику",
)
async def create_emotion_entry(
    body: EmotionEntryCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Створює новий запис у щоденнику емоцій.

    ⚠️ Один запис на день. Якщо запис за цю дату вже існує — поверне помилку 400.
    """
    service = EmotionService(db)
    return await service.create_entry(current_user.id, body)


@router.get(
    "/",
    response_model=list[EmotionEntryRead],
    summary="Отримати записи за місяць",
)
async def get_entries_by_month(
    current_user: CurrentUser,
    db: DbSession,
    month: int = Query(ge=1, le=12, description="Місяць (1-12)"),
    year: int = Query(ge=2020, le=2100, description="Рік"),
):
    """Повертає всі записи щоденника за вказаний місяць та рік.

    Записи відсортовані за датою.
    """
    service = EmotionService(db)
    return await service.get_entries_by_month(current_user.id, month, year)


@router.get(
    "/date/{entry_date}",
    response_model=EmotionEntryRead,
    summary="Отримати запис за дату",
)
async def get_entry_by_date(
    entry_date: date,
    current_user: CurrentUser,
    db: DbSession,
):
    """Повертає запис щоденника за конкретну дату (формат: YYYY-MM-DD)."""
    service = EmotionService(db)
    return await service.get_entry_by_date(current_user.id, entry_date)


@router.patch(
    "/{entry_id}",
    response_model=EmotionEntryRead,
    summary="Оновити запис",
)
async def update_emotion_entry(
    entry_id: uuid.UUID,
    body: EmotionEntryUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Часткове оновлення запису. Надсилайте лише поля, які потрібно змінити."""
    service = EmotionService(db)
    return await service.update_entry(current_user.id, entry_id, body)


@router.delete(
    "/{entry_id}",
    status_code=204,
    summary="Видалити запис",
)
async def delete_emotion_entry(
    entry_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Видаляє запис з щоденника емоцій. Ця дія незворотна."""
    service = EmotionService(db)
    await service.delete_entry(current_user.id, entry_id)


@router.post(
    "/generate",
    response_model=EmotionGenerateResponse,
    summary="Згенерувати опис стану",
)
async def generate_emotion_summary(
    body: EmotionGenerateRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """Генерує опис емоційного стану на основі розмови з ботом.

    Аналізує вказану розмову через AI та повертає:
    - **description**: Короткий опис емоційного стану (2-3 речення).
    - **emoji**: Запропонований емодзі.
    - **tags**: Теги емоцій (до 3 штук).

    Користувач може зберегти, відредагувати або відхилити пропозицію.
    """
    service = EmotionService(db)
    return await service.generate_emotion_summary(
        current_user.id, body.conversation_id
    )

