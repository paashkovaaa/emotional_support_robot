"""Pydantic-схеми для детекції залежності від бота."""

from datetime import datetime

from pydantic import BaseModel, Field


class UsageMetrics(BaseModel):
    """Метрики використання за період."""

    sessions_today: int = Field(description="Кількість сесій за сьогодні")
    sessions_last_7_days: int = Field(description="Кількість сесій за останні 7 днів")
    sessions_last_30_days: int = Field(description="Кількість сесій за останні 30 днів")
    messages_today: int = Field(description="Кількість повідомлень за сьогодні")
    messages_last_7_days: int = Field(description="Кількість повідомлень за 7 днів")
    avg_session_duration_minutes: float = Field(
        description="Середня тривалість сесії в хвилинах (за 7 днів)",
    )
    consecutive_active_days: int = Field(
        description="Кількість днів поспіль з активністю",
    )
    longest_session_minutes: float = Field(
        description="Найдовша сесія за 7 днів (хвилини)",
    )


class DependencyWarning(BaseModel):
    """Окреме попередження про ознаки залежності."""

    trigger: str = Field(description="Ідентифікатор тригера")
    severity: str = Field(description="low | medium | high")
    message_ua: str = Field(description="Повідомлення українською для користувача")


class DependencyCheckResult(BaseModel):
    """Результат перевірки на залежність."""

    has_warnings: bool = Field(description="Чи є попередження")
    risk_level: str = Field(description="none | low | medium | high")
    warnings: list[DependencyWarning] = Field(
        default_factory=list,
        description="Список попереджень",
    )
    usage: UsageMetrics = Field(description="Метрики використання")
    bot_message: str | None = Field(
        default=None,
        description="М'яке повідомлення від бота (якщо є попередження)",
    )
    show_reminder: bool = Field(
        default=False,
        description="Чи потрібно показати періодичне нагадування",
    )
    checked_at: datetime = Field(description="Час перевірки")


class ReminderResponse(BaseModel):
    """Відповідь з нагадуванням."""

    show: bool = Field(description="Чи потрібно показувати нагадування")
    message: str = Field(description="Текст нагадування")
    type: str = Field(description="periodic | dependency_warning | therapy_reminder")

