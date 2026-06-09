"""AI-сервіс — інтеграція з Anthropic Claude Haiku 4.5.

Відповідальість:
  - Генерація streaming / повних відповідей бота
  - Будування системного промпта (з урахуванням профілю користувача)
  - Управління контекстним вікном (останні N повідомлень + summary)
  - Інтеграція RAG-контексту з бази знань (через Gemini + pgvector)
  - Генерація summary розмови при завершенні
  - Генерація пропозиції для щоденника емоцій
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator

import time

import anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.exceptions import BadRequestError
from backend.app.core.logging import get_logger
from backend.app.core.perf_logger import record_streaming_complete, record_streaming_chunk
from backend.app.core.prompts import (
    CONVERSATION_SUMMARY_PROMPT,
    EMOTION_SUMMARY_PROMPT,
    STYLE_ANALYTICAL,
    STYLE_BALANCED,
    STYLE_FRIENDLY,
    SYSTEM_PROMPT_BASE,
)
from backend.app.models.conversation import Conversation, ConversationStatus
from backend.app.models.message import Message, MessageSender
from backend.app.models.profile import CommunicationStyle, Profile

logger = get_logger(__name__)


# ── Fallback-відповідь коли AI недоступний ──
_AI_UNAVAILABLE_MSG = (
    "Вибачте, зараз я не можу відповісти через технічну проблему. 🙏 "
    "Спробуйте ще раз через хвилину. Якщо вам потрібна термінова допомога — "
    "телефонуйте на Лайфлайн Україна: 7333."
)


class AiService:
    """Сервіс AI-відповідей на базі Anthropic Claude Haiku 4."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._client: anthropic.AsyncAnthropic | None = None

    # ─────────────────────────────────────────────────
    # Публічний API
    # ─────────────────────────────────────────────────

    @property
    def client(self) -> anthropic.AsyncAnthropic:
        """Лінивий доступ до Anthropic клієнта."""
        if self._client is None:
            if not settings.ANTHROPIC_API_KEY:
                raise BadRequestError(
                    "ANTHROPIC_API_KEY не налаштований. "
                    "Додайте ключ у файл .env та перезапустіть сервер."
                )
            self._client = anthropic.AsyncAnthropic(
                api_key=settings.ANTHROPIC_API_KEY,
            )
        return self._client

    async def stream_response(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> AsyncGenerator[str, None]:
        """Генерує streaming-відповідь від Claude з RAG-контекстом.

        1. Отримує контекст розмови та профіль
        2. Виконує векторний пошук у базі знань (RAG)
        3. Якщо є релевантні знання — Gemini синтезує їх у стислий контекст
        4. Claude генерує емпатичну відповідь з урахуванням знань

        Yields:
            Текстові чанки відповіді Клода.
        """
        # Отримуємо останнє повідомлення користувача для RAG-запиту
        last_user_msg = await self._get_last_user_message(conversation_id)

        # Будуємо системний промпт та виконуємо RAG-пошук ПОСЛІДОВНО
        # (обидві операції використовують один і той самий DB-сесію,
        #  паралельні asyncio.create_task на одній сесії призводять до
        #  asyncpg.InterfaceError: another operation is in progress)
        system_prompt = await self._build_system_prompt(user_id, conversation_id)

        rag_context: str | None = None
        if last_user_msg:
            try:
                rag_context = await asyncio.wait_for(
                    self._get_rag_context(last_user_msg),
                    timeout=20.0,  # не блокуємо відповідь довше 20 сек
                )
            except asyncio.TimeoutError:
                logger.warning("RAG context timed out (>20s), continuing without it")
                rag_context = None

        had_rag = rag_context is not None

        # Вбудовуємо RAG-контекст у системний промпт (якщо є)
        if rag_context:
            system_prompt += (
                "\n\n---\n"
                "📚 Релевантні знання з бази психологічних матеріалів:\n"
                f"{rag_context}\n\n"
                "Використовуй ці знання як підґрунтя для своєї відповіді, "
                "але залишайся емпатичним і природним у спілкуванні."
            )

        messages = await self._build_context(conversation_id)

        if not messages:
            yield _AI_UNAVAILABLE_MSG
            return

        # ── Вимірювання часу стрімінгу ──
        stream_start = time.perf_counter()
        first_token_ms: float | None = None
        chunk_index = 0

        try:
            async with self.client.messages.stream(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE,
                system=system_prompt,
                messages=messages,
            ) as stream:
                async for text in stream.text_stream:
                    elapsed = (time.perf_counter() - stream_start) * 1000
                    if first_token_ms is None:
                        first_token_ms = elapsed
                    record_streaming_chunk(
                        str(conversation_id), chunk_index, elapsed,
                        is_first=(chunk_index == 0)
                    )
                    chunk_index += 1
                    yield text

        except anthropic.AuthenticationError:
            logger.error("Anthropic: невірний API-ключ")
            yield (
                "Вибачте, виникла проблема з налаштуваннями сервісу. "
                "Зверніться до адміністратора. 🔧"
            )
        except anthropic.APIConnectionError as exc:
            logger.error(f"Anthropic connection error: {exc}")
            yield _AI_UNAVAILABLE_MSG
        except anthropic.RateLimitError:
            logger.warning("Anthropic: rate limit перевищено")
            yield (
                "Зачекайте хвильку — зараз надто багато запитів. "
                "Спробуйте ще раз через кілька секунд. ⏳"
            )
        except anthropic.APIStatusError as exc:
            logger.error(f"Anthropic API error {exc.status_code}: {exc.message}")
            yield _AI_UNAVAILABLE_MSG
        finally:
            total_ms = (time.perf_counter() - stream_start) * 1000
            record_streaming_complete(
                conversation_id=str(conversation_id),
                total_ms=total_ms,
                first_token_ms=first_token_ms if first_token_ms is not None else 0.0,
                total_chunks=chunk_index,
                response_len=0,  # довжина буде відома зовні
                had_rag=had_rag,
            )

    async def generate_full_response(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> str:
        """Генерує повну (non-streaming) відповідь від Claude.

        Використовується в REST-ендпоінті як fallback.

        Returns:
            Повний текст відповіді.
        """
        chunks: list[str] = []
        async for chunk in self.stream_response(conversation_id, user_id):
            chunks.append(chunk)
        return "".join(chunks)

    async def generate_summary(
        self,
        conversation_id: uuid.UUID,
    ) -> str:
        """Генерує короткий підсумок розмови для довгострокової пам'яті.

        Викликається при завершенні розмови (end_conversation).

        Returns:
            Текст підсумку або порожній рядок при помилці.
        """
        # Вибираємо всі повідомлення розмови
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sent_at.asc())
        )
        result = await self.db.execute(stmt)
        messages = result.scalars().all()

        if not messages:
            return ""

        conversation_text = "\n".join(
            f"{'Користувач' if m.sender == MessageSender.USER else 'Emi'}: {m.content}"
            for m in messages
        )
        prompt = CONVERSATION_SUMMARY_PROMPT.format(conversation=conversation_text)

        try:
            response = await self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=256,
                temperature=0.3,  # Нижча температура для точнішого підсумку
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as exc:
            logger.error(f"Помилка генерації summary: {exc}")
            return ""

    async def generate_emotion_entry(
        self,
        conversation_id: uuid.UUID,
    ) -> dict:
        """Генерує пропозицію запису у щоденник емоцій на основі розмови.

        Returns:
            dict з ключами: description, emoji, tags (або {} при помилці).
        """
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sent_at.asc())
            .limit(30)
        )
        result = await self.db.execute(stmt)
        messages = result.scalars().all()

        if not messages:
            return {}

        conversation_text = "\n".join(
            f"{'Користувач' if m.sender == MessageSender.USER else 'Emi'}: {m.content}"
            for m in messages
        )
        prompt = EMOTION_SUMMARY_PROMPT.format(conversation=conversation_text)

        try:
            response = await self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=256,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            # Видаляємо markdown-обгортку якщо є
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text)
        except json.JSONDecodeError as exc:
            logger.error(f"Помилка парсингу emotion entry JSON: {exc}")
            return {}
        except Exception as exc:
            logger.error(f"Помилка генерації emotion entry: {exc}")
            return {}

    # ─────────────────────────────────────────────────
    # Приватні методи
    # ─────────────────────────────────────────────────

    async def _build_system_prompt(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> str:
        """Будує системний промпт з урахуванням профілю користувача та попередніх розмов."""
        # Отримуємо профіль
        stmt = select(Profile).where(Profile.user_id == user_id)
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()

        prompt_parts: list[str] = [SYSTEM_PROMPT_BASE]

        # ── Стиль спілкування ──
        if profile:
            style_map = {
                CommunicationStyle.ANALYTICAL: STYLE_ANALYTICAL,
                CommunicationStyle.FRIENDLY: STYLE_FRIENDLY,
                CommunicationStyle.BALANCED: STYLE_BALANCED,
            }
            prompt_parts.append(
                style_map.get(profile.communication_style, STYLE_BALANCED)
            )

            # ── Персоналізація ──
            personal_lines: list[str] = []

            if profile.nickname:
                personal_lines.append(
                    f"Ім'я користувача: {profile.nickname}. "
                    f"ОБОВ'ЯЗКОВО завжди звертайся до користувача на ім'я '{profile.nickname}' — "
                    "особливо на початку першого повідомлення в розмові та в ключових емоційних моментах. "
                    "Ніколи не використовуй безособові звертання якщо відомо ім'я."
                )
            if profile.concern:
                personal_lines.append(
                    f"Головна тема, яка хвилює: {profile.concern}."
                )
            if profile.life_area:
                personal_lines.append(
                    f"Сфера, яку хоче покращити: {profile.life_area}."
                )
            if profile.works_with_psychologist:
                personal_lines.append(
                    "Користувач вже працює з психологом — підтримуй цей процес, "
                    "не дублюй та не суперечи роботі фахівця."
                )

            if personal_lines:
                prompt_parts.append("\nПерсональний контекст:\n" + "\n".join(personal_lines))
        else:
            prompt_parts.append(STYLE_BALANCED)

        # ── Пам'ять попередніх розмов ──
        summaries = await self._get_previous_summaries(user_id, conversation_id)
        if summaries:
            prompt_parts.append(
                "\nКонтекст попередніх розмов з цим користувачем:\n" + summaries
            )

        return "\n".join(prompt_parts).strip()

    async def _build_context(
        self,
        conversation_id: uuid.UUID,
    ) -> list[dict]:
        """Будує список повідомлень для Anthropic API.

        Формат Anthropic: масив {"role": "user"|"assistant", "content": str}.
        Повідомлення мають ЧЕРГУВАТИСЯ: user → assistant → user → ...
        Перше повідомлення завжди має бути від "user".

        Returns:
            Список повідомлень або порожній список.
        """
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sent_at.desc())  # Від нових до старих
            .limit(settings.AI_CONTEXT_MESSAGES)
        )
        result = await self.db.execute(stmt)
        # Перевертаємо: від старих до нових
        messages = list(reversed(result.scalars().all()))

        if not messages:
            return []

        # Перетворюємо на формат Anthropic
        anthropic_messages: list[dict] = []
        for msg in messages:
            role = "user" if msg.sender == MessageSender.USER else "assistant"
            anthropic_messages.append({"role": role, "content": msg.content})

        # Anthropic вимагає: перше повідомлення = "user"
        # Відкидаємо початкові assistant-повідомлення
        while anthropic_messages and anthropic_messages[0]["role"] == "assistant":
            anthropic_messages.pop(0)

        if not anthropic_messages:
            return []

        # Anthropic також не дозволяє два поспіль однакові ролі
        # Якщо таке трапляється — об'єднуємо сусідні повідомлення з тією ж роллю
        merged: list[dict] = [anthropic_messages[0]]
        for msg in anthropic_messages[1:]:
            if msg["role"] == merged[-1]["role"]:
                merged[-1]["content"] += "\n\n" + msg["content"]
            else:
                merged.append(msg)

        return merged

    async def _get_previous_summaries(
        self,
        user_id: uuid.UUID,
        current_conversation_id: uuid.UUID,
    ) -> str:
        """Повертає підсумки попередніх розмов для контекстної пам'яті.

        Спочатку шукає готові summaries завершених розмов.
        Якщо їх немає — формує короткий контекст з останніх повідомлень
        попередніх розмов (fallback для нових користувачів).
        """
        # 1. Перевіряємо готові summaries завершених розмов
        stmt = (
            select(Conversation.summary)
            .where(
                Conversation.user_id == user_id,
                Conversation.id != current_conversation_id,
                Conversation.status == ConversationStatus.ENDED,
                Conversation.summary.isnot(None),
                Conversation.summary != "",
            )
            .order_by(Conversation.ended_at.desc())
            .limit(settings.AI_PREV_SUMMARIES_COUNT)
        )
        result = await self.db.execute(stmt)
        summaries = result.scalars().all()

        if summaries:
            return "\n".join(f"• {s}" for s in summaries)

        # 2. Fallback: якщо summaries відсутні — беремо останні повідомлення
        # з попередніх розмов як короткий контекст
        recent_conv_stmt = (
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.id != current_conversation_id,
            )
            .order_by(Conversation.started_at.desc())
            .limit(3)
        )
        result = await self.db.execute(recent_conv_stmt)
        recent_convs = result.scalars().all()

        if not recent_convs:
            return ""

        context_parts: list[str] = []
        for conv in recent_convs:
            msg_stmt = (
                select(Message)
                .where(Message.conversation_id == conv.id)
                .order_by(Message.sent_at.asc())
                .limit(8)
            )
            result = await self.db.execute(msg_stmt)
            msgs = result.scalars().all()

            if not msgs:
                continue

            date_str = conv.started_at.strftime("%d.%m.%Y")
            user_msgs = [
                m.content[:120]
                for m in msgs
                if m.sender == MessageSender.USER
            ]
            if user_msgs:
                preview = "; ".join(user_msgs[:3])
                context_parts.append(f"• Розмова від {date_str}: {preview}")

        return "\n".join(context_parts)

    async def _get_last_user_message(
        self, conversation_id: uuid.UUID
    ) -> str | None:
        """Повертає текст останнього повідомлення від користувача."""
        stmt = (
            select(Message.content)
            .where(
                Message.conversation_id == conversation_id,
                Message.sender == MessageSender.USER,
            )
            .order_by(Message.sent_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_rag_context(self, query: str | None) -> str | None:
        """Отримує релевантний контекст з бази знань через RAG.

        Повертає None якщо база знань порожня або запит не релевантний.
        Помилки ігноруються — RAG є опціональним покращенням.
        """
        if not query:
            return None

        try:
            from backend.app.services.rag_service import RagService
            rag = RagService(self.db)
            return await rag.get_rag_context(query)
        except Exception as exc:
            logger.warning(f"RAG context fetch failed (non-critical): {exc}")
            return None


