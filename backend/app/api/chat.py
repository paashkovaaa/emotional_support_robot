"""API роутер чату — розмови та повідомлення."""

import time
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from backend.app.api.deps import CurrentUser, DbSession
from backend.app.config import settings
from backend.app.core.logging import get_logger
from backend.app.core.perf_logger import record_ws_cycle
from backend.app.schemas.chat import (
    ConversationCreate,
    ConversationListItem,
    ConversationRead,
    ConversationUpdate,
    MessageCreate,
    MessageRead,
    MessagesListResponse,
    WSIncoming,
    WSOutgoing,
)
from backend.app.services.chat_service import ChatService
from backend.app.models.message import MessageSender

logger = get_logger(__name__)

router = APIRouter()


# ──────────────────────────────────────
# Conversations REST API
# ──────────────────────────────────────


@router.post(
    "/conversations",
    response_model=ConversationRead,
    status_code=201,
    summary="Створити нову розмову",
)
async def create_conversation(
    body: ConversationCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Створює нову розмову для поточного користувача."""
    service = ChatService(db)
    return await service.create_conversation(current_user.id, body)


@router.get(
    "/conversations",
    response_model=list[ConversationListItem],
    summary="Список розмов",
)
async def list_conversations(
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Повертає список розмов поточного користувача (від новіших до старіших)."""
    service = ChatService(db)
    return await service.get_conversations(current_user.id, limit=limit, offset=offset)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationRead,
    summary="Деталі розмови",
)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Повертає деталі розмови за ID."""
    service = ChatService(db)
    return await service.get_conversation(conversation_id, current_user.id)


@router.patch(
    "/conversations/{conversation_id}",
    response_model=ConversationRead,
    summary="Оновити розмову",
)
async def update_conversation(
    conversation_id: uuid.UUID,
    body: ConversationUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Оновлює назву розмови."""
    service = ChatService(db)
    return await service.update_conversation(conversation_id, current_user.id, body)


@router.post(
    "/conversations/{conversation_id}/end",
    response_model=ConversationRead,
    summary="Завершити розмову",
)
async def end_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Завершує активну розмову та автоматично генерує summary для пам'яті."""
    service = ChatService(db)
    result = await service.end_conversation(conversation_id, current_user.id)

    # Автоматично генеруємо summary для довгострокової пам'яті
    if settings.ANTHROPIC_API_KEY:
        try:
            from backend.app.services.ai_service import AiService
            ai = AiService(db)
            summary = await ai.generate_summary(conversation_id)
            if summary:
                await service.save_summary(conversation_id, summary)
                logger.info(f"Summary saved for conversation {conversation_id}")
        except Exception as exc:
            logger.warning(f"Summary generation failed (non-critical): {exc}")

    return result


@router.delete(
    "/conversations/{conversation_id}",
    status_code=204,
    summary="Видалити розмову",
)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Видаляє розмову та всі її повідомлення."""
    service = ChatService(db)
    await service.delete_conversation(conversation_id, current_user.id)


# ──────────────────────────────────────
# Messages REST API
# ──────────────────────────────────────


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=MessagesListResponse,
    summary="Повідомлення розмови",
)
async def get_messages(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """Повертає повідомлення розмови (від старих до нових)."""
    service = ChatService(db)
    messages, total = await service.get_messages(
        conversation_id, current_user.id, limit=limit, offset=offset
    )
    return MessagesListResponse(
        messages=messages,
        total=total,
        conversation_id=conversation_id,
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageRead,
    status_code=201,
    summary="Надіслати повідомлення",
)
async def send_message(
    conversation_id: uuid.UUID,
    body: MessageCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Надсилає повідомлення від користувача.

    Зберігає повідомлення в БД з автоматичною keyword-based детекцією кризи.
    Якщо виявлено кризовий стан (MEDIUM+), автоматично додається відповідь бота
    з кризовими контактами.
    """
    service = ChatService(db)
    user_msg = await service.add_user_message(
        conversation_id, current_user.id, body
    )

    # Якщо виявлено кризу — автоматично додаємо кризову відповідь бота
    crisis_response = getattr(user_msg, "_crisis_response", None)
    if crisis_response and user_msg.is_crisis:
        await service.add_bot_message(
            conversation_id,
            crisis_response,
            crisis_level=user_msg.crisis_level,
            is_crisis=True,
        )
    elif settings.ANTHROPIC_API_KEY:
        # Non-streaming AI response для REST fallback (коли WS недоступний)
        try:
            from backend.app.services.ai_service import AiService
            ai = AiService(db)
            bot_text = await ai.generate_full_response(conversation_id, current_user.id)
            await service.add_bot_message(conversation_id, bot_text)
        except Exception as exc:
            logger.warning(f"REST AI fallback error: {exc}")

    return user_msg


# ──────────────────────────────────────
# WebSocket
# ──────────────────────────────────────


@router.websocket("/ws/chat/{conversation_id}")
async def websocket_chat(
    websocket: WebSocket,
    conversation_id: uuid.UUID,
):
    """WebSocket ендпоінт для real-time чату.

    Протокол:
    → Client sends: {"type": "message", "content": "..."}
    ← Server sends: {"type": "message", "content": "...", "sender": "bot", "message_id": "..."}
    ← Server sends: {"type": "chunk", "content": "..."}  (streaming)
    ← Server sends: {"type": "typing"}
    ← Server sends: {"type": "error", "content": "..."}

    Автентифікація через query-параметр ?token=<jwt>.
    """
    # Перевіряємо токен з query params
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    # Валідація токена
    try:
        from backend.app.core.security import decode_token
        payload = decode_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=4001, reason="Invalid token type")
            return
        user_id = uuid.UUID(payload["sub"])
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()

    # Отримуємо сесію БД
    from backend.app.database import async_session_factory
    async with async_session_factory() as db:
        service = ChatService(db)

        # Перевіряємо що розмова належить користувачу
        try:
            conv = await service.get_conversation(conversation_id, user_id)
        except Exception:
            await websocket.send_json(
                WSOutgoing(type="error", content="Розмову не знайдено").model_dump()
            )
            await websocket.close()
            return

        try:
            while True:
                data = await websocket.receive_text()

                try:
                    incoming = WSIncoming.model_validate_json(data)
                except Exception:
                    await websocket.send_json(
                        WSOutgoing(type="error", content="Невалідний формат повідомлення").model_dump()
                    )
                    continue

                if incoming.type == "end_conversation":
                    await service.end_conversation(conversation_id, user_id)

                    # Генеруємо summary асинхронно перед відповіддю
                    if settings.ANTHROPIC_API_KEY:
                        try:
                            from backend.app.services.ai_service import AiService
                            ai_ws = AiService(db)
                            summary = await ai_ws.generate_summary(conversation_id)
                            if summary:
                                await service.save_summary(conversation_id, summary)
                        except Exception as _exc:
                            logger.warning(f"WS summary generation failed: {_exc}")

                    await websocket.send_json(
                        WSOutgoing(type="conversation_ended").model_dump()
                    )
                    break

                if incoming.type == "message" and incoming.content:
                    _ws_start = time.perf_counter()

                    # Зберігаємо повідомлення користувача (з авто-детекцією кризи)
                    user_msg = await service.add_user_message(
                        conversation_id,
                        user_id,
                        MessageCreate(content=incoming.content),
                    )

                    # Відправляємо підтвердження
                    await websocket.send_json(
                        WSOutgoing(
                            type="message",
                            content=user_msg.content,
                            sender=MessageSender.USER,
                            message_id=str(user_msg.id),
                            is_crisis=user_msg.is_crisis,
                            crisis_level=user_msg.crisis_level,
                        ).model_dump()
                    )

                    # Typing indicator
                    await websocket.send_json(
                        WSOutgoing(type="typing").model_dump()
                    )

                    # ── Кризова відповідь (якщо виявлено MEDIUM+) ──
                    crisis_response = getattr(user_msg, "_crisis_response", None)
                    if crisis_response and user_msg.is_crisis:
                        crisis_bot_msg = await service.add_bot_message(
                            conversation_id,
                            crisis_response,
                            crisis_level=user_msg.crisis_level,
                            is_crisis=True,
                        )
                        await websocket.send_json(
                            WSOutgoing(
                                type="message",
                                content=crisis_bot_msg.content,
                                sender=MessageSender.BOT,
                                message_id=str(crisis_bot_msg.id),
                                is_crisis=True,
                                crisis_level=crisis_bot_msg.crisis_level,
                            ).model_dump()
                        )
                        record_ws_cycle(
                            str(conversation_id),
                            (time.perf_counter() - _ws_start) * 1000,
                            was_crisis=True,
                            crisis_level=str(user_msg.crisis_level),
                            message_len=len(incoming.content),
                        )
                        # Після кризової відповіді AI-відповідь не генеруємо
                        continue

                    # ── AI-відповідь через Anthropic Claude ──
                    if not settings.ANTHROPIC_API_KEY:
                        # Fallback якщо ключ не налаштований
                        stub = (
                            "Вибачте, AI-сервіс зараз недоступний. "
                            "Зверніться до адміністратора."
                        )
                        bot_msg = await service.add_bot_message(conversation_id, stub)
                        await websocket.send_json(
                            WSOutgoing(
                                type="message",
                                content=bot_msg.content,
                                sender=MessageSender.BOT,
                                message_id=str(bot_msg.id),
                            ).model_dump()
                        )
                        continue

                    try:
                        from backend.app.services.ai_service import AiService
                        ai_service = AiService(db)

                        # Streaming: збираємо чанки та відправляємо клієнту
                        full_response_parts: list[str] = []
                        async for chunk in ai_service.stream_response(
                            conversation_id, user_id
                        ):
                            full_response_parts.append(chunk)
                            await websocket.send_json(
                                WSOutgoing(
                                    type="chunk",
                                    content=chunk,
                                    sender=MessageSender.BOT,
                                ).model_dump()
                            )

                        full_response = "".join(full_response_parts)

                        # Зберігаємо фінальне повідомлення у БД
                        bot_msg = await service.add_bot_message(
                            conversation_id, full_response
                        )

                        # Відправляємо підтвердження з message_id
                        await websocket.send_json(
                            WSOutgoing(
                                type="message",
                                content=bot_msg.content,
                                sender=MessageSender.BOT,
                                message_id=str(bot_msg.id),
                                is_crisis=bot_msg.is_crisis,
                                crisis_level=bot_msg.crisis_level,
                            ).model_dump()
                        )
                        record_ws_cycle(
                            str(conversation_id),
                            (time.perf_counter() - _ws_start) * 1000,
                            was_crisis=False,
                            crisis_level=str(user_msg.crisis_level),
                            message_len=len(incoming.content),
                        )

                    except Exception as ai_exc:
                        logger.error(f"AI streaming error in WebSocket: {ai_exc}", exc_info=True)
                        error_msg = (
                            "Вибачте, зараз я не можу відповісти. 🙏 "
                            "Спробуйте ще раз або зверніться на гарячу лінію 7333."
                        )
                        bot_msg = await service.add_bot_message(
                            conversation_id, error_msg
                        )
                        await websocket.send_json(
                            WSOutgoing(
                                type="message",
                                content=error_msg,
                                sender=MessageSender.BOT,
                                message_id=str(bot_msg.id),
                            ).model_dump()
                        )

        except WebSocketDisconnect:
            pass  # Клієнт відключився
        except Exception as e:
            try:
                await websocket.send_json(
                    WSOutgoing(type="error", content=str(e)).model_dump()
                )
            except Exception:
                pass

