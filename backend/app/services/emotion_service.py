"""Сервіс щоденника емоцій."""

import json
import uuid
from datetime import date

from sqlalchemy import select, extract, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.exceptions import BadRequestError, NotFoundError
from backend.app.core.prompts import EMOTION_SUMMARY_PROMPT
from backend.app.models.conversation import Conversation
from backend.app.models.emotion_entry import EmotionEntry
from backend.app.models.message import Message
from backend.app.schemas.emotion import (
    EmotionEntryCreate,
    EmotionEntryUpdate,
    EmotionGenerateResponse,
)


class EmotionService:
    """Сервіс для роботи зі щоденником емоцій."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── CRUD ──

    async def create_entry(
        self, user_id: uuid.UUID, data: EmotionEntryCreate
    ) -> EmotionEntry:
        """Створює новий запис у щоденнику емоцій.

        Один запис на день на користувача. Якщо запис за цю дату вже існує —
        повертає помилку.

        Args:
            user_id: UUID користувача.
            data: Дані нового запису.

        Returns:
            Створений EmotionEntry.

        Raises:
            BadRequestError: Якщо запис за цю дату вже існує.
        """
        # Перевірка: один запис на день
        existing = await self._get_by_date(user_id, data.entry_date)
        if existing:
            raise BadRequestError(
                f"Запис за дату {data.entry_date} вже існує. "
                f"Використовуйте PATCH для оновлення."
            )

        entry = EmotionEntry(
            user_id=user_id,
            entry_date=data.entry_date,
            emoji=data.emoji,
            user_description=data.user_description,
            bot_description=data.bot_description,
            emotion_tags=data.emotion_tags,
        )
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def get_entries_by_month(
        self, user_id: uuid.UUID, month: int, year: int
    ) -> list[EmotionEntry]:
        """Отримує всі записи за певний місяць.

        Args:
            user_id: UUID користувача.
            month: Місяць (1-12).
            year: Рік.

        Returns:
            Список EmotionEntry за вказаний місяць.
        """
        stmt = (
            select(EmotionEntry)
            .where(
                and_(
                    EmotionEntry.user_id == user_id,
                    extract("month", EmotionEntry.entry_date) == month,
                    extract("year", EmotionEntry.entry_date) == year,
                )
            )
            .order_by(EmotionEntry.entry_date)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_entry_by_date(
        self, user_id: uuid.UUID, entry_date: date
    ) -> EmotionEntry:
        """Отримує запис за конкретну дату.

        Args:
            user_id: UUID користувача.
            entry_date: Дата запису.

        Returns:
            EmotionEntry.

        Raises:
            NotFoundError: Якщо запис не знайдено.
        """
        entry = await self._get_by_date(user_id, entry_date)
        if not entry:
            raise NotFoundError(f"Запис за дату {entry_date} не знайдено")
        return entry

    async def get_entry_by_id(
        self, user_id: uuid.UUID, entry_id: uuid.UUID
    ) -> EmotionEntry:
        """Отримує запис за ID з перевіркою власника.

        Args:
            user_id: UUID користувача.
            entry_id: UUID запису.

        Returns:
            EmotionEntry.

        Raises:
            NotFoundError: Якщо запис не знайдено або не належить користувачу.
        """
        stmt = select(EmotionEntry).where(
            and_(
                EmotionEntry.id == entry_id,
                EmotionEntry.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        entry = result.scalar_one_or_none()

        if not entry:
            raise NotFoundError("Запис не знайдено")
        return entry

    async def update_entry(
        self, user_id: uuid.UUID, entry_id: uuid.UUID, data: EmotionEntryUpdate
    ) -> EmotionEntry:
        """Часткове оновлення запису.

        Args:
            user_id: UUID користувача.
            entry_id: UUID запису.
            data: Поля для оновлення.

        Returns:
            Оновлений EmotionEntry.
        """
        entry = await self.get_entry_by_id(user_id, entry_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entry, field, value)

        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def delete_entry(
        self, user_id: uuid.UUID, entry_id: uuid.UUID
    ) -> None:
        """Видаляє запис з щоденника.

        Args:
            user_id: UUID користувача.
            entry_id: UUID запису.

        Raises:
            NotFoundError: Якщо запис не знайдено.
        """
        entry = await self.get_entry_by_id(user_id, entry_id)
        await self.db.delete(entry)
        await self.db.commit()

    # ── Генерація опису AI ──

    async def generate_emotion_summary(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> EmotionGenerateResponse:
        """Генерує опис емоційного стану на основі розмови з AI.

        Бере повідомлення з вказаної розмови, формує промпт і відправляє
        до LLM для аналізу та генерації короткого опису.

        Args:
            user_id: UUID користувача.
            conversation_id: UUID розмови.

        Returns:
            EmotionGenerateResponse з описом, емодзі та тегами.

        Raises:
            NotFoundError: Якщо розмову не знайдено.
            BadRequestError: Якщо розмова порожня або AI сервіс недоступний.
        """
        # Перевірка розмови
        stmt = select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise NotFoundError("Розмову не знайдено")

        # Отримання повідомлень розмови
        msg_stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sent_at)
        )
        msg_result = await self.db.execute(msg_stmt)
        messages = list(msg_result.scalars().all())

        if not messages:
            raise BadRequestError("Розмова не містить повідомлень")

        # Формування тексту розмови для промпта
        conversation_text = self._format_conversation(messages)

        # Генерація через Claude (Anthropic) — той самий клієнт що й основний чат
        if not settings.ANTHROPIC_API_KEY:
            raise BadRequestError(
                "ANTHROPIC_API_KEY не налаштований — додайте ключ у файл .env"
            )

        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            prompt = EMOTION_SUMMARY_PROMPT.format(conversation=conversation_text)

            response = await client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=512,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.content[0].text.strip()

            # Парсинг JSON-відповіді
            parsed = self._parse_llm_json(content)
            return EmotionGenerateResponse(
                description=parsed.get("description") or "Emi проаналізувала розмову, але не змогла скласти опис. Спробуй описати свій стан самостійно.",
                emoji=parsed.get("emoji") or "🙂",
                tags=parsed.get("tags") or [],
            )

        except Exception as e:
            raise BadRequestError(f"Помилка генерації опису емоцій: {str(e)}")

    # ── Допоміжні методи ──

    async def _get_by_date(
        self, user_id: uuid.UUID, entry_date: date
    ) -> EmotionEntry | None:
        """Знаходить запис за датою та користувачем."""
        stmt = select(EmotionEntry).where(
            and_(
                EmotionEntry.user_id == user_id,
                EmotionEntry.entry_date == entry_date,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _format_conversation(messages: list[Message]) -> str:
        """Форматує повідомлення розмови у текст для промпта."""
        lines = []
        for msg in messages:
            sender = "Користувач" if msg.sender.value == "user" else "Бот"
            lines.append(f"{sender}: {msg.content}")
        return "\n".join(lines)

    @staticmethod
    def _parse_llm_json(content: str) -> dict:
        """Парсить JSON з відповіді LLM.

        LLM може повертати JSON обгорнутий у ```json ... ``` блок.
        """
        # Видалення markdown-обгортки
        cleaned = content.strip()
        if cleaned.startswith("```"):
            # Видаляємо першу лінію (```json) та останню (```)
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                "description": content,
                "emoji": "😐",
                "tags": [],
            }

