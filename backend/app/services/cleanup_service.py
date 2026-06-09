"""Сервіс очищення застарілих даних.

Видаляє розмови та повідомлення старші за CONVERSATION_HISTORY_DAYS.
Може запускатися як:
  - Фоновий таск при старті додатку (asyncio.create_task)
  - Окремий скрипт через cron
  - Вручну через admin API
"""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.logging import get_logger
from backend.app.database import async_session_factory
from backend.app.models.conversation import Conversation, ConversationStatus
from backend.app.models.message import Message

logger = get_logger(__name__)


class DataCleanupService:
    """Сервіс для автоматичного видалення застарілих даних."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def cleanup_old_conversations(self) -> dict:
        """Видаляє розмови та їх повідомлення старші за ліміт.

        Returns:
            Статистика видалення.
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(
            days=settings.CONVERSATION_HISTORY_DAYS
        )

        # Знаходимо кількість розмов для видалення
        count_stmt = select(func.count(Conversation.id)).where(
            Conversation.created_at < cutoff_date,
            Conversation.status == ConversationStatus.ENDED,
        )
        result = await self.db.execute(count_stmt)
        conversations_count = result.scalar() or 0

        if conversations_count == 0:
            logger.info("Очищення: немає застарілих розмов для видалення")
            return {"deleted_conversations": 0, "cutoff_date": cutoff_date.isoformat()}

        # Знаходимо ID розмов для видалення
        conv_ids_stmt = select(Conversation.id).where(
            Conversation.created_at < cutoff_date,
            Conversation.status == ConversationStatus.ENDED,
        )
        conv_result = await self.db.execute(conv_ids_stmt)
        conv_ids = [row[0] for row in conv_result.fetchall()]

        # Рахуємо повідомлення для видалення
        msg_count_stmt = select(func.count(Message.id)).where(
            Message.conversation_id.in_(conv_ids)
        )
        msg_result = await self.db.execute(msg_count_stmt)
        messages_count = msg_result.scalar() or 0

        # Видаляємо повідомлення (CASCADE має зробити це автоматично,
        # але для надійності видаляємо явно)
        del_msg_stmt = delete(Message).where(
            Message.conversation_id.in_(conv_ids)
        )
        await self.db.execute(del_msg_stmt)

        # Видаляємо розмови
        del_conv_stmt = delete(Conversation).where(
            Conversation.id.in_(conv_ids)
        )
        await self.db.execute(del_conv_stmt)

        await self.db.commit()

        logger.info(
            f"Очищення завершено: видалено {conversations_count} розмов "
            f"та {messages_count} повідомлень старших за {settings.CONVERSATION_HISTORY_DAYS} днів"
        )

        return {
            "deleted_conversations": conversations_count,
            "deleted_messages": messages_count,
            "cutoff_date": cutoff_date.isoformat(),
        }

    async def cleanup_orphan_emotion_entries(self) -> dict:
        """Видаляє записи щоденника для видалених/заблокованих користувачів.

        Зазвичай CASCADE вирішує це, але для надійності.
        """
        # Placeholder — основна логіка через CASCADE
        return {"cleaned": 0}


async def run_scheduled_cleanup() -> None:
    """Запускає очищення як фоновий таск.

    Виконується щодня о 03:00 UTC.
    """
    logger.info("Запуск фонового таску очищення даних")

    while True:
        # Чекаємо до наступного запуску (кожні 24 години)
        now = datetime.now(timezone.utc)
        next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)

        wait_seconds = (next_run - now).total_seconds()
        logger.info(f"Наступне очищення заплановане на {next_run.isoformat()} "
                     f"(через {wait_seconds / 3600:.1f} годин)")

        await asyncio.sleep(wait_seconds)

        try:
            async with async_session_factory() as db:
                service = DataCleanupService(db)
                result = await service.cleanup_old_conversations()
                logger.info(f"Результат очищення: {result}")
        except Exception as e:
            logger.error(f"Помилка під час очищення: {e}")

