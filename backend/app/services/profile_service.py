"""Сервіс профілю користувача."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import NotFoundError
from backend.app.models.profile import Profile
from backend.app.models.user import User
from backend.app.schemas.profile import ProfileUpdate, SurveyRequest


class ProfileService:
    """Сервіс для роботи з профілями."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_profile(self, user_id: uuid.UUID) -> Profile:
        """Отримує профіль за user_id.

        Raises:
            NotFoundError: Якщо профіль не знайдено.
        """
        stmt = select(Profile).where(Profile.user_id == user_id)
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            raise NotFoundError("Профіль не знайдено")

        return profile

    async def complete_survey(
        self, user_id: uuid.UUID, survey: SurveyRequest
    ) -> Profile:
        """Зберігає результати опитування.

        Args:
            user_id: UUID користувача.
            survey: Дані опитування.

        Returns:
            Оновлений профіль.
        """
        profile = await self.get_profile(user_id)

        profile.communication_style = survey.communication_style
        profile.life_area = survey.life_area
        profile.concern = survey.concern
        profile.works_with_psychologist = survey.works_with_psychologist
        profile.survey_completed = True

        await self.db.flush()
        return profile

    async def update_profile(
        self, user_id: uuid.UUID, data: ProfileUpdate
    ) -> Profile:
        """Часткове оновлення профілю.

        Args:
            user_id: UUID користувача.
            data: Поля для оновлення (тільки не-None).

        Returns:
            Оновлений профіль.
        """
        profile = await self.get_profile(user_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)

        await self.db.flush()
        return profile

    async def delete_account(self, user_id: uuid.UUID) -> None:
        """Видаляє акаунт користувача та всі пов'язані дані.

        Каскадне видалення очистить: профіль, розмови, повідомлення, записи емоцій.

        Args:
            user_id: UUID користувача.

        Raises:
            NotFoundError: Якщо користувача не знайдено.
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("Користувача не знайдено")

        await self.db.delete(user)
        await self.db.flush()
