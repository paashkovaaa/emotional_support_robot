"""Тести сервісу щоденника емоцій."""

import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import BadRequestError, NotFoundError
from backend.app.models.emotion_entry import EmotionEntry
from backend.app.models.user import User
from backend.app.schemas.emotion import EmotionEntryCreate, EmotionEntryUpdate
from backend.app.services.emotion_service import EmotionService


class TestEmotionServiceCreate:
    """Тести створення записів."""

    async def test_create_entry(self, db_session: AsyncSession, test_user: User):
        service = EmotionService(db_session)
        entry = await service.create_entry(
            user_id=test_user.id,
            data=EmotionEntryCreate(
                entry_date=date.today(),
                emoji="😊",
                user_description="Сьогодні гарний день",
                # emotion_tags пропускаємо — SQLite не підтримує ARRAY
            ),
        )
        assert entry.user_id == test_user.id
        assert entry.emoji == "😊"
        assert entry.user_description == "Сьогодні гарний день"

    async def test_create_entry_minimal(self, db_session: AsyncSession, test_user: User):
        service = EmotionService(db_session)
        entry = await service.create_entry(
            user_id=test_user.id,
            data=EmotionEntryCreate(entry_date=date.today()),
        )
        assert entry.user_id == test_user.id
        assert entry.emoji is None

    async def test_create_duplicate_date(self, db_session: AsyncSession, test_user: User):
        service = EmotionService(db_session)
        today = date.today()
        await service.create_entry(
            user_id=test_user.id,
            data=EmotionEntryCreate(entry_date=today, emoji="😊"),
        )
        with pytest.raises(BadRequestError, match="вже існує"):
            await service.create_entry(
                user_id=test_user.id,
                data=EmotionEntryCreate(entry_date=today, emoji="😢"),
            )


class TestEmotionServiceRead:
    """Тести читання записів."""

    async def test_get_by_month(self, db_session: AsyncSession, test_user: User):
        service = EmotionService(db_session)
        today = date.today()
        # Створюємо записи за 3 дні
        for i in range(3):
            d = today - timedelta(days=i)
            await service.create_entry(
                user_id=test_user.id,
                data=EmotionEntryCreate(entry_date=d, emoji="😊"),
            )
        entries = await service.get_entries_by_month(
            user_id=test_user.id,
            month=today.month,
            year=today.year,
        )
        assert len(entries) >= 1  # Мінімум один запис за поточний місяць

    async def test_get_by_date(self, db_session: AsyncSession, test_user: User):
        service = EmotionService(db_session)
        today = date.today()
        await service.create_entry(
            user_id=test_user.id,
            data=EmotionEntryCreate(entry_date=today, emoji="😊"),
        )
        entry = await service.get_entry_by_date(test_user.id, today)
        assert entry.emoji == "😊"

    async def test_get_by_date_not_found(self, db_session: AsyncSession, test_user: User):
        service = EmotionService(db_session)
        with pytest.raises(NotFoundError):
            await service.get_entry_by_date(test_user.id, date(2020, 1, 1))

    async def test_get_by_id(self, db_session: AsyncSession, test_user: User):
        service = EmotionService(db_session)
        entry = await service.create_entry(
            user_id=test_user.id,
            data=EmotionEntryCreate(entry_date=date.today(), emoji="😊"),
        )
        found = await service.get_entry_by_id(test_user.id, entry.id)
        assert found.id == entry.id

    async def test_get_by_id_wrong_user(self, db_session: AsyncSession, test_user: User):
        service = EmotionService(db_session)
        entry = await service.create_entry(
            user_id=test_user.id,
            data=EmotionEntryCreate(entry_date=date.today(), emoji="😊"),
        )
        with pytest.raises(NotFoundError):
            await service.get_entry_by_id(uuid.uuid4(), entry.id)


class TestEmotionServiceUpdate:
    """Тести оновлення записів."""

    async def test_update_emoji(self, db_session: AsyncSession, test_user: User):
        service = EmotionService(db_session)
        entry = await service.create_entry(
            user_id=test_user.id,
            data=EmotionEntryCreate(entry_date=date.today(), emoji="😊"),
        )
        updated = await service.update_entry(
            user_id=test_user.id,
            entry_id=entry.id,
            data=EmotionEntryUpdate(emoji="😢"),
        )
        assert updated.emoji == "😢"

    async def test_update_description(self, db_session: AsyncSession, test_user: User):
        service = EmotionService(db_session)
        entry = await service.create_entry(
            user_id=test_user.id,
            data=EmotionEntryCreate(entry_date=date.today()),
        )
        updated = await service.update_entry(
            user_id=test_user.id,
            entry_id=entry.id,
            data=EmotionEntryUpdate(user_description="Оновлений опис"),
        )
        assert updated.user_description == "Оновлений опис"


class TestEmotionServiceDelete:
    """Тести видалення записів."""

    async def test_delete_entry(self, db_session: AsyncSession, test_user: User):
        service = EmotionService(db_session)
        entry = await service.create_entry(
            user_id=test_user.id,
            data=EmotionEntryCreate(entry_date=date.today(), emoji="😊"),
        )
        await service.delete_entry(test_user.id, entry.id)
        with pytest.raises(NotFoundError):
            await service.get_entry_by_id(test_user.id, entry.id)

    async def test_delete_nonexistent(self, db_session: AsyncSession, test_user: User):
        service = EmotionService(db_session)
        with pytest.raises(NotFoundError):
            await service.delete_entry(test_user.id, uuid.uuid4())


class TestEmotionServiceHelpers:
    """Тести допоміжних методів."""

    def test_parse_llm_json_valid(self):
        content = '{"description": "Тест", "emoji": "😊", "tags": ["щастя"]}'
        result = EmotionService._parse_llm_json(content)
        assert result["description"] == "Тест"
        assert result["emoji"] == "😊"
        assert result["tags"] == ["щастя"]

    def test_parse_llm_json_with_markdown(self):
        content = '```json\n{"description": "Тест", "emoji": "😊", "tags": []}\n```'
        result = EmotionService._parse_llm_json(content)
        assert result["description"] == "Тест"

    def test_parse_llm_json_invalid(self):
        content = "це не JSON взагалі"
        result = EmotionService._parse_llm_json(content)
        assert result["emoji"] == "😐"
        assert result["description"] == content

