"""Сервіс адмін-панелі."""

import math
import time
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.exceptions import BadRequestError, NotFoundError
from backend.app.models.conversation import Conversation, ConversationStatus
from backend.app.models.emotion_entry import EmotionEntry
from backend.app.models.message import CrisisLevel, Message
from backend.app.models.user import User, UserRole
from backend.app.schemas.admin import (
    AdminUserListResponse,
    AdminUserRead,
    BlockUserResponse,
    CrisisStats,
    ServiceHealth,
    SystemHealth,
    SystemStats,
)

# Час старту сервера (модуль завантажується при старті)
_server_start_time = time.time()


class AdminService:
    """Сервіс для адміністративних операцій."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ──────────────────────────────────────────────
    # Список користувачів
    # ──────────────────────────────────────────────

    async def get_users(
        self,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        role: UserRole | None = None,
        is_blocked: bool | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> AdminUserListResponse:
        """Отримує список користувачів з пагінацією та фільтрацією.

        Args:
            page: Номер сторінки (починаючи з 1).
            per_page: Кількість елементів на сторінці.
            search: Пошук за email.
            role: Фільтр за роллю.
            is_blocked: Фільтр за статусом блокування.
            sort_by: Поле для сортування (created_at, email, last_login).
            sort_order: Напрямок сортування (asc, desc).

        Returns:
            AdminUserListResponse з користувачами та метаданими пагінації.
        """
        # Базовий запит
        base_query = select(User)

        # Фільтри
        filters = []
        if search:
            filters.append(User.email.ilike(f"%{search}%"))
        if role is not None:
            filters.append(User.role == role)
        if is_blocked is not None:
            filters.append(User.is_blocked == is_blocked)

        if filters:
            base_query = base_query.where(and_(*filters))

        # Підрахунок загальної кількості
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Сортування
        sort_column = self._get_sort_column(sort_by)
        if sort_order == "asc":
            base_query = base_query.order_by(sort_column.asc())
        else:
            base_query = base_query.order_by(sort_column.desc())

        # Пагінація
        offset = (page - 1) * per_page
        base_query = base_query.offset(offset).limit(per_page)

        result = await self.db.execute(base_query)
        users = list(result.scalars().all())

        # Отримуємо кількість розмов і записів емоцій для кожного користувача
        user_ids = [u.id for u in users]
        conversation_counts = await self._count_conversations(user_ids)
        emotion_counts = await self._count_emotion_entries(user_ids)

        # Формуємо відповідь
        user_reads = []
        for user in users:
            user_data = AdminUserRead(
                id=user.id,
                email=user.email,
                role=user.role,
                is_active=user.is_active,
                is_blocked=user.is_blocked,
                last_login=user.last_login,
                created_at=user.created_at,
                updated_at=user.updated_at,
                conversations_count=conversation_counts.get(user.id, 0),
                emotion_entries_count=emotion_counts.get(user.id, 0),
            )
            user_reads.append(user_data)

        pages = math.ceil(total / per_page) if total > 0 else 1

        return AdminUserListResponse(
            users=user_reads,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )

    # ──────────────────────────────────────────────
    # Блокування / розблокування
    # ──────────────────────────────────────────────

    async def block_user(
        self,
        user_id: uuid.UUID,
        is_blocked: bool,
        admin_id: uuid.UUID,
        reason: str | None = None,
    ) -> BlockUserResponse:
        """Блокує або розблоковує користувача.

        Args:
            user_id: UUID користувача.
            is_blocked: True — заблокувати, False — розблокувати.
            admin_id: UUID адміна, що виконує дію.
            reason: Причина блокування.

        Returns:
            BlockUserResponse.

        Raises:
            NotFoundError: Якщо користувача не знайдено.
            BadRequestError: Якщо адмін намагається заблокувати себе.
        """
        if user_id == admin_id:
            raise BadRequestError("Неможливо заблокувати власний акаунт")

        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("Користувача не знайдено")

        if user.role == UserRole.ADMIN:
            raise BadRequestError("Неможливо заблокувати адміністратора")

        user.is_blocked = is_blocked
        await self.db.flush()

        action = "заблоковано" if is_blocked else "розблоковано"
        message = f"Користувача {user.email or user.id} {action}"
        if reason:
            message += f". Причина: {reason}"

        return BlockUserResponse(
            id=user.id,
            email=user.email,
            is_blocked=user.is_blocked,
            message=message,
        )

    # ──────────────────────────────────────────────
    # Статистика системи
    # ──────────────────────────────────────────────

    async def get_stats(self) -> SystemStats:
        """Отримує загальну статистику системи.

        Returns:
            SystemStats з усіма метриками.
        """
        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)

        # Користувачі
        users_query = select(
            func.count().label("total"),
            func.count().filter(User.is_active.is_(True)).label("active"),
            func.count().filter(User.is_blocked.is_(True)).label("blocked"),
            func.count()
            .filter(User.created_at >= seven_days_ago)
            .label("registered_7d"),
            func.count()
            .filter(User.created_at >= thirty_days_ago)
            .label("registered_30d"),
        ).select_from(User)

        users_result = await self.db.execute(users_query)
        users_row = users_result.one()

        # Розмови
        conversations_query = select(
            func.count().label("total"),
            func.count()
            .filter(Conversation.status == ConversationStatus.ACTIVE)
            .label("active"),
        ).select_from(Conversation)

        conv_result = await self.db.execute(conversations_query)
        conv_row = conv_result.one()

        # Повідомлення
        messages_count_query = select(func.count()).select_from(Message)
        messages_result = await self.db.execute(messages_count_query)
        total_messages = messages_result.scalar_one()

        # Записи емоцій
        emotions_count_query = select(func.count()).select_from(EmotionEntry)
        emotions_result = await self.db.execute(emotions_count_query)
        total_emotions = emotions_result.scalar_one()

        # Кризова статистика
        crisis_stats = await self._get_crisis_stats()

        return SystemStats(
            total_users=users_row.total,
            active_users=users_row.active,
            blocked_users=users_row.blocked,
            total_conversations=conv_row.total,
            active_conversations=conv_row.active,
            total_messages=total_messages,
            total_emotion_entries=total_emotions,
            crisis=crisis_stats,
            users_registered_last_7_days=users_row.registered_7d,
            users_registered_last_30_days=users_row.registered_30d,
        )

    # ──────────────────────────────────────────────
    # Здоров'я системи
    # ──────────────────────────────────────────────

    async def get_health(self, redis_client: object | None) -> SystemHealth:
        """Перевіряє здоров'я всіх компонентів системи.

        Args:
            redis_client: Redis клієнт зі стейту FastAPI (або None).

        Returns:
            SystemHealth зі статусом кожного сервісу.
        """
        db_health = await self._check_db_health()
        redis_health = await self._check_redis_health(redis_client)

        # Загальний статус
        statuses = [db_health.status, redis_health.status]
        if all(s == "ok" for s in statuses):
            overall = "healthy"
        elif any(s == "error" for s in statuses):
            overall = "unhealthy"
        else:
            overall = "degraded"

        return SystemHealth(
            status=overall,
            uptime_seconds=round(time.time() - _server_start_time, 2),
            database=db_health,
            redis=redis_health,
            version=settings.APP_VERSION,
            environment=settings.ENVIRONMENT,
        )

    # ──────────────────────────────────────────────
    # Приватні хелпери
    # ──────────────────────────────────────────────

    @staticmethod
    def _get_sort_column(sort_by: str):
        """Повертає колонку для сортування."""
        columns = {
            "created_at": User.created_at,
            "email": User.email,
            "last_login": User.last_login,
            "role": User.role,
        }
        return columns.get(sort_by, User.created_at)

    async def _count_conversations(
        self, user_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, int]:
        """Підраховує кількість розмов для списку користувачів."""
        if not user_ids:
            return {}
        stmt = (
            select(
                Conversation.user_id,
                func.count().label("cnt"),
            )
            .where(Conversation.user_id.in_(user_ids))
            .group_by(Conversation.user_id)
        )
        result = await self.db.execute(stmt)
        return {row.user_id: row.cnt for row in result.all()}

    async def _count_emotion_entries(
        self, user_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, int]:
        """Підраховує кількість записів емоцій для списку користувачів."""
        if not user_ids:
            return {}
        stmt = (
            select(
                EmotionEntry.user_id,
                func.count().label("cnt"),
            )
            .where(EmotionEntry.user_id.in_(user_ids))
            .group_by(EmotionEntry.user_id)
        )
        result = await self.db.execute(stmt)
        return {row.user_id: row.cnt for row in result.all()}

    async def _get_crisis_stats(self) -> CrisisStats:
        """Збирає статистику кризових повідомлень."""
        stmt = select(
            func.count().label("total"),
            func.count()
            .filter(Message.crisis_level == CrisisLevel.LOW)
            .label("low"),
            func.count()
            .filter(Message.crisis_level == CrisisLevel.MEDIUM)
            .label("medium"),
            func.count()
            .filter(Message.crisis_level == CrisisLevel.HIGH)
            .label("high"),
            func.count()
            .filter(Message.crisis_level == CrisisLevel.CRITICAL)
            .label("critical"),
        ).where(Message.is_crisis.is_(True))

        result = await self.db.execute(stmt)
        row = result.one()

        return CrisisStats(
            total_crisis_messages=row.total,
            by_level={
                "low": row.low,
                "medium": row.medium,
                "high": row.high,
                "critical": row.critical,
            },
        )

    async def _check_db_health(self) -> ServiceHealth:
        """Перевіряє з'єднання з базою даних."""
        try:
            start = time.time()
            await self.db.execute(select(func.now()))
            latency = round((time.time() - start) * 1000, 2)
            return ServiceHealth(status="ok", latency_ms=latency)
        except Exception as e:
            return ServiceHealth(status="error", detail=str(e))

    @staticmethod
    async def _check_redis_health(redis_client: object | None) -> ServiceHealth:
        """Перевіряє з'єднання з Redis."""
        if not redis_client:
            return ServiceHealth(status="unavailable", detail="Redis не підключено")
        try:
            start = time.time()
            await redis_client.ping()  # type: ignore[union-attr]
            latency = round((time.time() - start) * 1000, 2)
            return ServiceHealth(status="ok", latency_ms=latency)
        except Exception as e:
            return ServiceHealth(status="error", detail=str(e))


