"""API роутер детекції залежності від бота."""

from fastapi import APIRouter, Query

from backend.app.api.deps import CurrentUser, DbSession
from backend.app.schemas.dependency import DependencyCheckResult, ReminderResponse
from backend.app.services.dependency_detector import DependencyDetector

router = APIRouter()


@router.get(
    "/check",
    response_model=DependencyCheckResult,
    summary="Перевірка на ознаки залежності",
)
async def check_dependency(
    user: CurrentUser,
    db: DbSession,
):
    """Аналізує патерни використання бота поточним користувачем.

    Повертає:
    - **usage**: метрики використання (сесії, повідомлення, тривалість)
    - **warnings**: список попереджень (якщо є)
    - **risk_level**: рівень ризику (none / low / medium / high)
    - **bot_message**: м'яке повідомлення від бота (при наявності попереджень)
    - **show_reminder**: чи потрібно показати періодичне нагадування
    """
    detector = DependencyDetector(db)
    return await detector.check_dependency(user.id)


@router.get(
    "/reminder",
    response_model=ReminderResponse,
    summary="Отримати нагадування",
)
async def get_reminder(
    user: CurrentUser,
    db: DbSession,
    message_count: int = Query(
        default=0,
        ge=0,
        description="Кількість повідомлень у поточній сесії",
    ),
):
    """Визначає, чи потрібно показати нагадування користувачу.

    Використовується під час чату для періодичного нагадування,
    що бот — не заміна терапії.

    **message_count** — кількість повідомлень у поточній сесії.
    Нагадування показується кожні N повідомлень (налаштовується).
    """
    detector = DependencyDetector(db)
    return await detector.get_periodic_reminder(user.id, message_count)

