"""API роутер профілю користувача."""

from fastapi import APIRouter

from backend.app.api.deps import CurrentUser, DbSession
from backend.app.schemas.profile import ProfileRead, ProfileUpdate, SurveyRequest
from backend.app.schemas.user import UserRead
from backend.app.services.profile_service import ProfileService

router = APIRouter()


@router.get(
    "/",
    response_model=ProfileRead,
    summary="Отримати профіль",
)
async def get_profile(current_user: CurrentUser, db: DbSession):
    """Повертає профіль поточного автентифікованого користувача."""
    service = ProfileService(db)
    return await service.get_profile(current_user.id)


@router.post(
    "/survey",
    response_model=ProfileRead,
    summary="Зберегти результати опитування",
)
async def complete_survey(
    body: SurveyRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """Зберігає результати початкового опитування.

    - **communication_style**: Стиль спілкування (аналітичний / дружній / збалансований).
    - **life_area**: Сфера життя для покращення.
    - **concern**: Що найбільше бентежить.
    - **works_with_psychologist**: Чи працює з психологом.
    """
    service = ProfileService(db)
    return await service.complete_survey(current_user.id, body)


@router.patch(
    "/",
    response_model=ProfileRead,
    summary="Оновити профіль",
)
async def update_profile(
    body: ProfileUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Часткове оновлення профілю. Надсилайте лише поля, які потрібно змінити."""
    service = ProfileService(db)
    return await service.update_profile(current_user.id, body)


@router.delete(
    "/",
    summary="Видалити акаунт",
)
async def delete_account(current_user: CurrentUser, db: DbSession):
    """Видаляє акаунт та всі пов'язані дані (розмови, повідомлення, записи емоцій).

    ⚠️ **Ця дія незворотна!**
    """
    service = ProfileService(db)
    await service.delete_account(current_user.id)
    return {"message": "Акаунт та всі дані видалено"}


@router.get(
    "/me",
    response_model=UserRead,
    summary="Дані поточного користувача",
)
async def get_current_user_info(current_user: CurrentUser):
    """Повертає основну інформацію про автентифікованого користувача."""
    return UserRead.model_validate(current_user)
