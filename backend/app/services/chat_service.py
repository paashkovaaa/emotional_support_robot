"""Сервіс чату — CRUD розмов та повідомлень.

AI-відповіді будуть підключені пізніше через ai_service.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from backend.app.models.conversation import Conversation, ConversationStatus
from backend.app.models.message import Message, MessageSender, CrisisLevel
from backend.app.core.logging import get_logger
from backend.app.schemas.chat import (
    ConversationCreate,
    ConversationListItem,
    ConversationRead,
    ConversationUpdate,
    MessageCreate,
    MessageRead,
)
from backend.app.services.crisis_detector import crisis_detector

logger = get_logger(__name__)


class ChatService:
    """Сервіс для роботи з розмовами та повідомленнями."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ──────────────────────────────────────
    # Conversations CRUD
    # ──────────────────────────────────────

    async def create_conversation(
        self,
        user_id: uuid.UUID,
        data: ConversationCreate,
    ) -> ConversationRead:
        """Створює нову розмову.

        Перевіряє ліміт MAX_CONVERSATIONS_PER_USER.
        """
        # Перевірка ліміту
        count_stmt = (
            select(func.count())
            .select_from(Conversation)
            .where(Conversation.user_id == user_id)
        )
        result = await self.db.execute(count_stmt)
        count = result.scalar_one()

        if count >= settings.MAX_CONVERSATIONS_PER_USER:
            raise BadRequestError(
                f"Досягнуто ліміт розмов ({settings.MAX_CONVERSATIONS_PER_USER}). "
                "Видаліть старі розмови."
            )

        conversation = Conversation(
            user_id=user_id,
            title=data.title,
            chat_type=data.chat_type,
            status=ConversationStatus.ACTIVE,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)

        return ConversationRead(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            chat_type=conversation.chat_type,
            status=conversation.status,
            started_at=conversation.started_at,
            ended_at=conversation.ended_at,
            summary=conversation.summary,
            message_count=0,
        )

    async def get_conversations(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConversationListItem]:
        """Повертає список розмов користувача з прев'ю останнього повідомлення."""
        # Підзапит: кількість повідомлень та останнє повідомлення
        msg_count_subq = (
            select(
                Message.conversation_id,
                func.count().label("msg_count"),
                func.max(Message.sent_at).label("last_msg_time"),
            )
            .group_by(Message.conversation_id)
            .subquery()
        )

        stmt = (
            select(Conversation, msg_count_subq.c.msg_count)
            .outerjoin(
                msg_count_subq,
                Conversation.id == msg_count_subq.c.conversation_id,
            )
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        items = []
        for conv, msg_count in rows:
            # Отримуємо прев'ю останнього повідомлення
            last_msg_preview = await self._get_last_message_preview(conv.id)

            items.append(
                ConversationListItem(
                    id=conv.id,
                    title=conv.title,
                    chat_type=conv.chat_type,
                    status=conv.status,
                    started_at=conv.started_at,
                    ended_at=conv.ended_at,
                    message_count=msg_count or 0,
                    last_message_preview=last_msg_preview,
                )
            )

        return items

    async def get_conversation(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> ConversationRead:
        """Отримує розмову за ID. Перевіряє належність користувачу."""
        conv = await self._get_conversation_or_404(conversation_id, user_id)

        msg_count = await self._count_messages(conversation_id)

        return ConversationRead(
            id=conv.id,
            user_id=conv.user_id,
            title=conv.title,
            chat_type=conv.chat_type,
            status=conv.status,
            started_at=conv.started_at,
            ended_at=conv.ended_at,
            summary=conv.summary,
            message_count=msg_count,
        )

    async def update_conversation(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ConversationUpdate,
    ) -> ConversationRead:
        """Оновлює назву розмови."""
        conv = await self._get_conversation_or_404(conversation_id, user_id)

        if data.title is not None:
            conv.title = data.title

        await self.db.commit()
        await self.db.refresh(conv)

        msg_count = await self._count_messages(conversation_id)

        return ConversationRead(
            id=conv.id,
            user_id=conv.user_id,
            title=conv.title,
            chat_type=conv.chat_type,
            status=conv.status,
            started_at=conv.started_at,
            ended_at=conv.ended_at,
            summary=conv.summary,
            message_count=msg_count,
        )

    async def end_conversation(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> ConversationRead:
        """Завершує розмову."""
        conv = await self._get_conversation_or_404(conversation_id, user_id)

        if conv.status == ConversationStatus.ENDED:
            raise BadRequestError("Розмова вже завершена")

        conv.status = ConversationStatus.ENDED
        conv.ended_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(conv)

        msg_count = await self._count_messages(conversation_id)

        return ConversationRead(
            id=conv.id,
            user_id=conv.user_id,
            title=conv.title,
            chat_type=conv.chat_type,
            status=conv.status,
            started_at=conv.started_at,
            ended_at=conv.ended_at,
            summary=conv.summary,
            message_count=msg_count,
        )

    async def delete_conversation(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Видаляє розмову та всі повідомлення (CASCADE)."""
        conv = await self._get_conversation_or_404(conversation_id, user_id)
        await self.db.delete(conv)
        await self.db.commit()

    # ──────────────────────────────────────
    # Messages CRUD
    # ──────────────────────────────────────

    async def get_messages(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[MessageRead], int]:
        """Повертає повідомлення розмови (від старих до нових)."""
        # Перевірка належності
        await self._get_conversation_or_404(conversation_id, user_id)

        total = await self._count_messages(conversation_id)

        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sent_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        messages = result.scalars().all()

        return [
            MessageRead(
                id=m.id,
                conversation_id=m.conversation_id,
                sender=m.sender,
                content=m.content,
                sent_at=m.sent_at,
                crisis_level=m.crisis_level,
                is_crisis=m.is_crisis,
            )
            for m in messages
        ], total

    async def add_user_message(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        data: MessageCreate,
    ) -> MessageRead:
        """Додає повідомлення від користувача.

        Автоматично виконує keyword-based детекцію кризових станів.
        Повертає збережене повідомлення. AI-відповідь генерується окремо.
        """
        conv = await self._get_conversation_or_404(conversation_id, user_id)

        if conv.status == ConversationStatus.ENDED:
            raise BadRequestError("Не можна писати у завершену розмову")

        # ── Keyword-based crisis detection ──
        crisis_result = crisis_detector.check_message(data.content)

        message = Message(
            conversation_id=conversation_id,
            sender=MessageSender.USER,
            content=data.content,
            sent_at=datetime.now(timezone.utc),
            crisis_level=crisis_result.crisis_level,
            is_crisis=crisis_result.is_crisis,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        # Автоматично генеруємо назву розмови з першого повідомлення
        if not conv.title:
            conv.title = data.content[:80] + ("..." if len(data.content) > 80 else "")
            await self.db.commit()

        msg_read = MessageRead(
            id=message.id,
            conversation_id=message.conversation_id,
            sender=message.sender,
            content=message.content,
            sent_at=message.sent_at,
            crisis_level=message.crisis_level,
            is_crisis=message.is_crisis,
        )

        # Зберігаємо crisis_response для використання у WebSocket/API
        msg_read._crisis_response = crisis_result.crisis_response  # type: ignore[attr-defined]

        return msg_read

    async def add_bot_message(
        self,
        conversation_id: uuid.UUID,
        content: str,
        crisis_level: CrisisLevel = CrisisLevel.NONE,
        is_crisis: bool = False,
    ) -> MessageRead:
        """Додає повідомлення від бота (використовується AI-сервісом)."""
        message = Message(
            conversation_id=conversation_id,
            sender=MessageSender.BOT,
            content=content,
            sent_at=datetime.now(timezone.utc),
            crisis_level=crisis_level,
            is_crisis=is_crisis,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        return MessageRead(
            id=message.id,
            conversation_id=message.conversation_id,
            sender=message.sender,
            content=message.content,
            sent_at=message.sent_at,
            crisis_level=message.crisis_level,
            is_crisis=message.is_crisis,
        )

    async def save_summary(
        self, conversation_id: uuid.UUID, summary: str
    ) -> None:
        """Зберігає підсумок розмови для довгострокової пам'яті."""
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(stmt)
        conv = result.scalar_one_or_none()
        if conv:
            conv.summary = summary
            await self.db.commit()

    # ──────────────────────────────────────
    # Приватні хелпери
    # ──────────────────────────────────────

    async def _get_conversation_or_404(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> Conversation:
        """Отримує розмову або 404 + перевірка належності."""
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(stmt)
        conv = result.scalar_one_or_none()

        if not conv:
            raise NotFoundError("Розмову не знайдено")

        if conv.user_id != user_id:
            raise ForbiddenError("Ця розмова належить іншому користувачу")

        return conv

    async def _count_messages(self, conversation_id: uuid.UUID) -> int:
        """Підраховує кількість повідомлень у розмові."""
        stmt = (
            select(func.count())
            .select_from(Message)
            .where(Message.conversation_id == conversation_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def _get_last_message_preview(
        self, conversation_id: uuid.UUID
    ) -> str | None:
        """Отримує прев'ю останнього повідомлення."""
        stmt = (
            select(Message.content)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sent_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        content = result.scalar_one_or_none()

        if content:
            return content[:100] + ("..." if len(content) > 100 else "")
        return None

