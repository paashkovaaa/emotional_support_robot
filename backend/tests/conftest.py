"""Фікстури для тестів.

Використовує SQLite in-memory для швидкості (без потреби у PostgreSQL).
Для інтеграційних тестів — async TestClient з override залежностей.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool, String, Text, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.security import create_token_pair, hash_password
from backend.app.database import get_db
from backend.app.models.base import Base
from backend.app.models.conversation import Conversation, ConversationStatus
from backend.app.models.message import Message, MessageSender
from backend.app.models.profile import CommunicationStyle, Profile
from backend.app.models.user import User, UserRole

# ── Патч PostgreSQL-специфічних типів для SQLite ──
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID as PG_UUID
from sqlalchemy import JSON

# Реєструємо SQLite-сумісні замінники для PG типів
# Це потрібно, бо моделі використовують JSONB, ARRAY, UUID
from sqlalchemy.dialects import sqlite

sqlite.base.SQLiteTypeCompiler.visit_JSONB = lambda self, type_, **kw: "TEXT"  # type: ignore[attr-defined]
sqlite.base.SQLiteTypeCompiler.visit_ARRAY = lambda self, type_, **kw: "TEXT"  # type: ignore[attr-defined]


# ── Тестовий двигун SQLite (async, in-memory) ──

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

test_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Фікстури для БД ──


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Створює таблиці перед кожним тестом та видаляє після."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Тестова сесія БД з відкатом після кожного тесту."""
    async with test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Override залежностей FastAPI ──


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Заміна get_db для тестів."""
    async with test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Фікстура HTTP-клієнта ──


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP-клієнт для тестування API ендпоінтів."""
    from backend.app.main import app

    app.dependency_overrides[get_db] = override_get_db
    app.state.redis = None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Фікстури для створення тестових даних ──


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Створює тестового користувача."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        role=UserRole.USER,
        is_active=True,
        is_blocked=False,
    )
    db_session.add(user)
    await db_session.flush()

    profile = Profile(
        id=uuid.uuid4(),
        user_id=user.id,
        nickname="TestUser",
        communication_style=CommunicationStyle.BALANCED,
        survey_completed=True,
    )
    db_session.add(profile)
    await db_session.flush()

    return user


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """Створює тестового адміністратора."""
    admin = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        hashed_password=hash_password("adminpassword123"),
        role=UserRole.ADMIN,
        is_active=True,
        is_blocked=False,
    )
    db_session.add(admin)
    await db_session.flush()

    profile = Profile(
        id=uuid.uuid4(),
        user_id=admin.id,
        nickname="Admin",
        communication_style=CommunicationStyle.BALANCED,
        survey_completed=True,
    )
    db_session.add(profile)
    await db_session.flush()

    return admin


@pytest_asyncio.fixture
async def blocked_user(db_session: AsyncSession) -> User:
    """Створює заблокованого користувача."""
    user = User(
        id=uuid.uuid4(),
        email="blocked@example.com",
        hashed_password=hash_password("blockedpassword123"),
        role=UserRole.USER,
        is_active=True,
        is_blocked=True,
    )
    db_session.add(user)
    await db_session.flush()

    profile = Profile(
        id=uuid.uuid4(),
        user_id=user.id,
        nickname="BlockedUser",
    )
    db_session.add(profile)
    await db_session.flush()

    return user


@pytest_asyncio.fixture
async def test_conversation(db_session: AsyncSession, test_user: User) -> Conversation:
    """Створює тестову розмову."""
    conv = Conversation(
        id=uuid.uuid4(),
        user_id=test_user.id,
        title="Test Conversation",
        status=ConversationStatus.ACTIVE,
        started_at=datetime.now(timezone.utc),
    )
    db_session.add(conv)
    await db_session.flush()
    return conv


@pytest_asyncio.fixture
async def test_messages(
    db_session: AsyncSession, test_conversation: Conversation
) -> list[Message]:
    """Створює тестові повідомлення в розмові."""
    messages = []
    for sender, content in [
        (MessageSender.USER, "Привіт, мені сумно"),
        (MessageSender.BOT, "Привіт! Розкажи мені більше про те, що ти відчуваєш."),
        (MessageSender.USER, "Я відчуваю стрес на роботі"),
        (MessageSender.BOT, "Я розумію, робочий стрес може бути дуже виснажливим."),
    ]:
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=test_conversation.id,
            sender=sender,
            content=content,
            sent_at=datetime.now(timezone.utc),
        )
        db_session.add(msg)
        messages.append(msg)

    await db_session.flush()
    return messages


# ── Хелпери для токенів ──


def get_auth_headers(user: User) -> dict[str, str]:
    """Повертає заголовки авторизації для тестового користувача."""
    tokens = create_token_pair(
        user_id=str(user.id),
        role=user.role.value,
        email=user.email,
    )
    return {"Authorization": f"Bearer {tokens['access_token']}"}
