"""Тести сервісу чату."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from backend.app.models.conversation import Conversation, ConversationStatus
from backend.app.models.message import CrisisLevel, Message, MessageSender
from backend.app.models.user import User
from backend.app.schemas.chat import ConversationCreate, ConversationUpdate, MessageCreate
from backend.app.services.chat_service import ChatService


class TestChatServiceConversations:
    """Тести CRUD розмов."""

    async def test_create_conversation(self, db_session: AsyncSession, test_user: User):
        service = ChatService(db_session)
        conv = await service.create_conversation(
            user_id=test_user.id,
            data=ConversationCreate(title="Test Chat"),
        )
        assert conv.title == "Test Chat"
        assert conv.user_id == test_user.id
        assert conv.status == ConversationStatus.ACTIVE
        assert conv.message_count == 0

    async def test_create_conversation_without_title(self, db_session: AsyncSession, test_user: User):
        service = ChatService(db_session)
        conv = await service.create_conversation(
            user_id=test_user.id,
            data=ConversationCreate(),
        )
        assert conv.title is None

    async def test_get_conversation(
        self, db_session: AsyncSession, test_user: User, test_conversation: Conversation
    ):
        service = ChatService(db_session)
        conv = await service.get_conversation(test_conversation.id, test_user.id)
        assert conv.id == test_conversation.id
        assert conv.title == "Test Conversation"

    async def test_get_conversation_wrong_user(
        self, db_session: AsyncSession, test_conversation: Conversation
    ):
        service = ChatService(db_session)
        with pytest.raises(ForbiddenError):
            await service.get_conversation(test_conversation.id, uuid.uuid4())

    async def test_get_conversation_not_found(self, db_session: AsyncSession, test_user: User):
        service = ChatService(db_session)
        with pytest.raises(NotFoundError):
            await service.get_conversation(uuid.uuid4(), test_user.id)

    async def test_get_conversations_list(self, db_session: AsyncSession, test_user: User):
        service = ChatService(db_session)
        # Створюємо кілька розмов
        for i in range(3):
            await service.create_conversation(
                user_id=test_user.id,
                data=ConversationCreate(title=f"Chat {i}"),
            )
        convs = await service.get_conversations(test_user.id)
        assert len(convs) == 3

    async def test_update_conversation_title(
        self, db_session: AsyncSession, test_user: User, test_conversation: Conversation
    ):
        service = ChatService(db_session)
        updated = await service.update_conversation(
            conversation_id=test_conversation.id,
            user_id=test_user.id,
            data=ConversationUpdate(title="New Title"),
        )
        assert updated.title == "New Title"

    async def test_end_conversation(
        self, db_session: AsyncSession, test_user: User, test_conversation: Conversation
    ):
        service = ChatService(db_session)
        ended = await service.end_conversation(test_conversation.id, test_user.id)
        assert ended.status == ConversationStatus.ENDED
        assert ended.ended_at is not None

    async def test_end_already_ended_conversation(
        self, db_session: AsyncSession, test_user: User, test_conversation: Conversation
    ):
        service = ChatService(db_session)
        await service.end_conversation(test_conversation.id, test_user.id)
        with pytest.raises(BadRequestError, match="вже завершена"):
            await service.end_conversation(test_conversation.id, test_user.id)

    async def test_delete_conversation(
        self, db_session: AsyncSession, test_user: User, test_conversation: Conversation
    ):
        service = ChatService(db_session)
        await service.delete_conversation(test_conversation.id, test_user.id)
        with pytest.raises(NotFoundError):
            await service.get_conversation(test_conversation.id, test_user.id)


class TestChatServiceMessages:
    """Тести повідомлень."""

    async def test_add_user_message(
        self, db_session: AsyncSession, test_user: User, test_conversation: Conversation
    ):
        service = ChatService(db_session)
        msg = await service.add_user_message(
            conversation_id=test_conversation.id,
            user_id=test_user.id,
            data=MessageCreate(content="Привіт!"),
        )
        assert msg.content == "Привіт!"
        assert msg.sender == MessageSender.USER

    async def test_add_user_message_sets_title(
        self, db_session: AsyncSession, test_user: User
    ):
        """Перше повідомлення автоматично стає назвою розмови."""
        service = ChatService(db_session)
        conv = await service.create_conversation(
            user_id=test_user.id,
            data=ConversationCreate(),  # Без назви
        )
        await service.add_user_message(
            conversation_id=conv.id,
            user_id=test_user.id,
            data=MessageCreate(content="Як правильно медитувати?"),
        )
        updated_conv = await service.get_conversation(conv.id, test_user.id)
        assert updated_conv.title is not None
        assert "медитувати" in updated_conv.title

    async def test_add_user_message_crisis_detection(
        self, db_session: AsyncSession, test_user: User, test_conversation: Conversation
    ):
        service = ChatService(db_session)
        msg = await service.add_user_message(
            conversation_id=test_conversation.id,
            user_id=test_user.id,
            data=MessageCreate(content="Мені дуже сумно"),
        )
        assert msg.crisis_level == CrisisLevel.LOW

    async def test_add_user_message_to_ended_conversation(
        self, db_session: AsyncSession, test_user: User, test_conversation: Conversation
    ):
        service = ChatService(db_session)
        await service.end_conversation(test_conversation.id, test_user.id)
        with pytest.raises(BadRequestError, match="завершену"):
            await service.add_user_message(
                conversation_id=test_conversation.id,
                user_id=test_user.id,
                data=MessageCreate(content="Ще одне повідомлення"),
            )

    async def test_add_bot_message(
        self, db_session: AsyncSession, test_conversation: Conversation
    ):
        service = ChatService(db_session)
        msg = await service.add_bot_message(
            conversation_id=test_conversation.id,
            content="Відповідь бота",
        )
        assert msg.sender == MessageSender.BOT
        assert msg.content == "Відповідь бота"

    async def test_get_messages(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_conversation: Conversation,
        test_messages: list[Message],
    ):
        service = ChatService(db_session)
        messages, total = await service.get_messages(
            conversation_id=test_conversation.id,
            user_id=test_user.id,
        )
        assert total == 4
        assert len(messages) == 4

    async def test_get_messages_pagination(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_conversation: Conversation,
        test_messages: list[Message],
    ):
        service = ChatService(db_session)
        messages, total = await service.get_messages(
            conversation_id=test_conversation.id,
            user_id=test_user.id,
            limit=2,
            offset=0,
        )
        assert total == 4
        assert len(messages) == 2

