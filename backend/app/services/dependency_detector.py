"""Сервіс детекції залежності від бота.

Відстежує патерни використання та генерує м'які попередження,
якщо поведінка вказує на формування емоційної залежності.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message, MessageSender
from backend.app.schemas.dependency import (
    DependencyCheckResult,
    DependencyWarning,
    ReminderResponse,
    UsageMetrics,
)


# ── М'які повідомлення ──

BOT_WARNING_MESSAGES = {
    "low": (
        "Я помітила, що ти останнім часом часто звертаєшся до мене — і це нормально. 💛 "
        "Але я хочу нагадати: я — лише інструмент підтримки, а не заміна живого спілкування "
        "чи професійної допомоги. Якщо тобі потрібна глибша підтримка, розглянь можливість "
        "поговорити з психологом."
    ),
    "medium": (
        "Я бачу, що ти проводиш багато часу в наших розмовах. Мені важливо, щоб ти знав(ла): "
        "я радію, що можу бути поруч, але справжній терапевтичний ефект дає робота з фахівцем. 🌱 "
        "Спробуй також проводити час із близькими людьми, гуляти надворі та займатися тим, "
        "що тобі подобається."
    ),
    "high": (
        "Я хочу бути чесною з тобою. 🤍 Я помітила, що наше спілкування стало дуже інтенсивним, "
        "і я турбуюся, що це може заважати іншим важливим речам у твоєму житті. "
        "Я — штучний інтелект, і я не можу замінити тобі людське тепло, дружбу та професійну підтримку. "
        "Будь ласка, зверніся до психолога — це буде найкращий крок для тебе. "
        "Лайфлайн Україна: 7333."
    ),
}

PERIODIC_REMINDERS = [
    "Нагадую: я — віртуальний помічник, а не заміна терапії. "
    "Якщо відчуваєш, що потребуєш професійної допомоги — зверніся до фахівця. 💙",

    "Ти знаєш, що регулярні зустрічі з психологом можуть бути набагато ефективнішими "
    "за наші розмови? Я тут, щоб підтримати між сесіями, але не замінити їх. 🌿",

    "Мені важливо нагадати: я — інструмент для емоційної підтримки, "
    "але не фахівець з психічного здоров'я. Подбай про себе — зверніся до спеціаліста, "
    "якщо відчуваєш, що це потрібно. 🤗",

    "Привіт! Я хочу нагадати, що окрім наших розмов, дуже важливо мати живе спілкування, "
    "фізичну активність та час для себе. Баланс — це ключ до благополуччя. 🌸",
]

THERAPY_REMINDER = (
    "Ти працюєш з психологом? Якщо ні — це може бути чудовим доповненням до нашого спілкування. "
    "Професіонал зможе допомогти глибше, ніж я. 💛"
)


class DependencyDetector:
    """Детектор ознак залежності від бота."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def check_dependency(self, user_id: uuid.UUID) -> DependencyCheckResult:
        """Виконує повну перевірку на ознаки залежності.

        Аналізує:
        - Кількість сесій за день/тиждень
        - Тривалість сесій
        - Кількість повідомлень
        - Кількість днів поспіль з активністю

        Args:
            user_id: UUID користувача.

        Returns:
            DependencyCheckResult з метриками та попередженнями.
        """
        now = datetime.now(timezone.utc)
        metrics = await self._calculate_metrics(user_id, now)
        warnings = self._evaluate_triggers(metrics)

        # Визначаємо рівень ризику
        if not warnings:
            risk_level = "none"
        else:
            severities = [w.severity for w in warnings]
            if "high" in severities:
                risk_level = "high"
            elif "medium" in severities:
                risk_level = "medium"
            else:
                risk_level = "low"

        # Генеруємо повідомлення бота
        bot_message = BOT_WARNING_MESSAGES.get(risk_level) if risk_level != "none" else None

        # Періодичне нагадування
        show_reminder = await self._should_show_periodic_reminder(user_id, now)

        return DependencyCheckResult(
            has_warnings=len(warnings) > 0,
            risk_level=risk_level,
            warnings=warnings,
            usage=metrics,
            bot_message=bot_message,
            show_reminder=show_reminder,
            checked_at=now,
        )

    async def get_periodic_reminder(
        self, user_id: uuid.UUID, message_count_in_session: int
    ) -> ReminderResponse:
        """Визначає, чи потрібно показати періодичне нагадування.

        Викликається під час чату кожні N повідомлень.

        Args:
            user_id: UUID користувача.
            message_count_in_session: Кількість повідомлень у поточній сесії.

        Returns:
            ReminderResponse.
        """
        now = datetime.now(timezone.utc)

        # Перевіряємо чи потрібно показати нагадування
        if message_count_in_session > 0 and (
            message_count_in_session % settings.DEPENDENCY_REMINDER_INTERVAL_MSGS == 0
        ):
            # Вибираємо нагадування на основі хешу часу
            idx = int(now.timestamp()) % len(PERIODIC_REMINDERS)
            return ReminderResponse(
                show=True,
                message=PERIODIC_REMINDERS[idx],
                type="periodic",
            )

        # Перевіряємо залежність
        metrics = await self._calculate_metrics(user_id, now)
        warnings = self._evaluate_triggers(metrics)

        if warnings:
            severities = [w.severity for w in warnings]
            if "high" in severities:
                level = "high"
            elif "medium" in severities:
                level = "medium"
            else:
                level = "low"

            return ReminderResponse(
                show=True,
                message=BOT_WARNING_MESSAGES[level],
                type="dependency_warning",
            )

        # Перевіряємо чи потрібно нагадати про терапію
        if await self._should_remind_about_therapy(user_id, now):
            return ReminderResponse(
                show=True,
                message=THERAPY_REMINDER,
                type="therapy_reminder",
            )

        return ReminderResponse(
            show=False,
            message="",
            type="periodic",
        )

    # ──────────────────────────────────────────────
    # Приватні методи
    # ──────────────────────────────────────────────

    async def _calculate_metrics(
        self, user_id: uuid.UUID, now: datetime
    ) -> UsageMetrics:
        """Розраховує метрики використання."""
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Сесії за сьогодні
        sessions_today = await self._count_sessions(user_id, today_start, now)

        # Сесії за 7 днів
        sessions_7d = await self._count_sessions(user_id, week_ago, now)

        # Сесії за 30 днів
        sessions_30d = await self._count_sessions(user_id, month_ago, now)

        # Повідомлення за сьогодні
        messages_today = await self._count_user_messages(user_id, today_start, now)

        # Повідомлення за 7 днів
        messages_7d = await self._count_user_messages(user_id, week_ago, now)

        # Середня та максимальна тривалість сесії за 7 днів
        avg_duration, max_duration = await self._calc_session_durations(
            user_id, week_ago, now
        )

        # Кількість днів поспіль з активністю
        consecutive_days = await self._count_consecutive_days(user_id, now)

        return UsageMetrics(
            sessions_today=sessions_today,
            sessions_last_7_days=sessions_7d,
            sessions_last_30_days=sessions_30d,
            messages_today=messages_today,
            messages_last_7_days=messages_7d,
            avg_session_duration_minutes=round(avg_duration, 1),
            consecutive_active_days=consecutive_days,
            longest_session_minutes=round(max_duration, 1),
        )

    def _evaluate_triggers(self, metrics: UsageMetrics) -> list[DependencyWarning]:
        """Оцінює тригери залежності."""
        warnings: list[DependencyWarning] = []

        # Тригер 1: Забагато сесій за день
        if metrics.sessions_today >= settings.DEPENDENCY_SESSIONS_PER_DAY_WARN:
            warnings.append(
                DependencyWarning(
                    trigger="excessive_daily_sessions",
                    severity="medium",
                    message_ua=(
                        f"Сьогодні у вас вже {metrics.sessions_today} сесій. "
                        "Спробуйте зробити перерву та зайнятися чимось приємним."
                    ),
                )
            )

        # Тригер 2: Забагато сесій за тиждень
        if metrics.sessions_last_7_days >= settings.DEPENDENCY_SESSIONS_PER_WEEK_WARN:
            warnings.append(
                DependencyWarning(
                    trigger="excessive_weekly_sessions",
                    severity="high",
                    message_ua=(
                        f"За останній тиждень — {metrics.sessions_last_7_days} сесій. "
                        "Рекомендуємо звернутися до професійного психолога."
                    ),
                )
            )

        # Тригер 3: Дуже тривалі сесії
        if metrics.avg_session_duration_minutes > settings.DEPENDENCY_AVG_DURATION_WARN_MIN:
            warnings.append(
                DependencyWarning(
                    trigger="long_sessions",
                    severity="medium",
                    message_ua=(
                        f"Середня тривалість ваших сесій — "
                        f"{metrics.avg_session_duration_minutes:.0f} хвилин. "
                        "Спробуйте обмежити час та робити паузи."
                    ),
                )
            )

        # Тригер 4: Забагато повідомлень за день
        if metrics.messages_today >= settings.DEPENDENCY_MESSAGES_PER_DAY_WARN:
            warnings.append(
                DependencyWarning(
                    trigger="excessive_daily_messages",
                    severity="medium",
                    message_ua=(
                        f"Сьогодні ви надіслали {metrics.messages_today} повідомлень. "
                        "Можливо, варто зробити перерву та відпочити."
                    ),
                )
            )

        # Тригер 5: Багато днів поспіль
        if metrics.consecutive_active_days >= settings.DEPENDENCY_CONSECUTIVE_DAYS_WARN:
            warnings.append(
                DependencyWarning(
                    trigger="consecutive_usage",
                    severity="low",
                    message_ua=(
                        f"Ви використовуєте бот {metrics.consecutive_active_days} днів поспіль. "
                        "Це нормально, але не забувайте про живе спілкування та активності офлайн."
                    ),
                )
            )

        return warnings

    async def _count_sessions(
        self, user_id: uuid.UUID, from_dt: datetime, to_dt: datetime
    ) -> int:
        """Підраховує кількість розмов за період."""
        stmt = (
            select(func.count())
            .select_from(Conversation)
            .where(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.started_at >= from_dt,
                    Conversation.started_at <= to_dt,
                )
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def _count_user_messages(
        self, user_id: uuid.UUID, from_dt: datetime, to_dt: datetime
    ) -> int:
        """Підраховує кількість повідомлень від користувача за період."""
        stmt = (
            select(func.count())
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(
                and_(
                    Conversation.user_id == user_id,
                    Message.sender == MessageSender.USER,
                    Message.sent_at >= from_dt,
                    Message.sent_at <= to_dt,
                )
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def _calc_session_durations(
        self, user_id: uuid.UUID, from_dt: datetime, to_dt: datetime
    ) -> tuple[float, float]:
        """Розраховує середню та максимальну тривалість сесій (хвилини).

        Тривалість = різниця між першим та останнім повідомленням розмови.
        """
        # Знаходимо розмови з повідомленнями за період
        stmt = (
            select(
                Conversation.id,
                func.min(Message.sent_at).label("first_msg"),
                func.max(Message.sent_at).label("last_msg"),
            )
            .join(Message, Message.conversation_id == Conversation.id)
            .where(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.started_at >= from_dt,
                    Conversation.started_at <= to_dt,
                )
            )
            .group_by(Conversation.id)
            .having(func.count(Message.id) > 1)  # Лише розмови з >1 повідомлення
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        if not rows:
            return 0.0, 0.0

        durations = []
        for row in rows:
            delta = (row.last_msg - row.first_msg).total_seconds() / 60.0
            durations.append(delta)

        avg_dur = sum(durations) / len(durations) if durations else 0.0
        max_dur = max(durations) if durations else 0.0

        return avg_dur, max_dur

    async def _count_consecutive_days(
        self, user_id: uuid.UUID, now: datetime
    ) -> int:
        """Підраховує кількість днів поспіль з хоча б однією сесією.

        Рахує назад від сьогодні.
        """
        # Отримуємо унікальні дати з сесіями за останні 60 днів
        sixty_days_ago = now - timedelta(days=60)

        stmt = (
            select(
                distinct(func.date(Conversation.started_at)).label("session_date")
            )
            .where(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.started_at >= sixty_days_ago,
                )
            )
            .order_by(func.date(Conversation.started_at).desc())
        )
        result = await self.db.execute(stmt)
        dates = [row.session_date for row in result.all()]

        if not dates:
            return 0

        # Рахуємо послідовні дні назад від сьогодні
        today = now.date()
        consecutive = 0

        for i in range(len(dates)):
            expected_date = today - timedelta(days=i)
            if dates[i] == expected_date:
                consecutive += 1
            else:
                break

        return consecutive

    async def _should_show_periodic_reminder(
        self, user_id: uuid.UUID, now: datetime
    ) -> bool:
        """Визначає чи потрібно показати періодичне нагадування.

        Показується, якщо за останні 7 днів було ≥3 сесій і це не перший день використання.
        """
        week_ago = now - timedelta(days=7)
        sessions = await self._count_sessions(user_id, week_ago, now)
        return sessions >= 3

    async def _should_remind_about_therapy(
        self, user_id: uuid.UUID, now: datetime
    ) -> bool:
        """Чи потрібно нагадати про терапію.

        Нагадуємо кожні 7 днів використання, якщо є ≥5 сесій.
        """
        week_ago = now - timedelta(days=7)
        sessions = await self._count_sessions(user_id, week_ago, now)
        consecutive = await self._count_consecutive_days(user_id, now)

        # Нагадуємо при 7+ днях поспіль або 5+ сесіях за тиждень
        return consecutive >= 7 or sessions >= 5


