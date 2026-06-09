"""Конфігурація застосунку через змінні оточення."""

import json
import os
from enum import StrEnum
from pathlib import Path

from dotenv import load_dotenv

from backend.app.core.logging import get_logger

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Завантажуємо .env один раз при імпорті модуля
load_dotenv(BASE_DIR / ".env", override=True)


class Env(StrEnum):
    # ── Застосунок ──
    APP_NAME                        = "APP_NAME"
    APP_VERSION                     = "APP_VERSION"
    DEBUG                           = "DEBUG"
    ENVIRONMENT                     = "ENVIRONMENT"
    # ── Сервер ──
    HOST                            = "HOST"
    PORT                            = "PORT"
    # ── База даних ──
    POSTGRES_USER                   = "POSTGRES_USER"
    POSTGRES_PASSWORD               = "POSTGRES_PASSWORD"
    POSTGRES_HOST                   = "POSTGRES_HOST"
    POSTGRES_PORT                   = "POSTGRES_PORT"
    POSTGRES_DB                     = "POSTGRES_DB"
    # ── Redis ──
    REDIS_HOST                      = "REDIS_HOST"
    REDIS_PORT                      = "REDIS_PORT"
    REDIS_DB                        = "REDIS_DB"
    # ── JWT ──
    JWT_SECRET_KEY                  = "JWT_SECRET_KEY"
    JWT_ALGORITHM                   = "JWT_ALGORITHM"
    ACCESS_TOKEN_EXPIRE_MINUTES     = "ACCESS_TOKEN_EXPIRE_MINUTES"
    REFRESH_TOKEN_EXPIRE_DAYS       = "REFRESH_TOKEN_EXPIRE_DAYS"
    # ── AI / LLM ──
    ANTHROPIC_API_KEY               = "ANTHROPIC_API_KEY"
    ANTHROPIC_MODEL                 = "ANTHROPIC_MODEL"
    GEMINI_API_KEY                  = "GEMINI_API_KEY"
    GEMINI_MODEL                    = "GEMINI_MODEL"
    AI_MAX_TOKENS                   = "AI_MAX_TOKENS"
    AI_TEMPERATURE                  = "AI_TEMPERATURE"
    AI_CONTEXT_MESSAGES             = "AI_CONTEXT_MESSAGES"
    AI_PREV_SUMMARIES_COUNT         = "AI_PREV_SUMMARIES_COUNT"
    # ── Embedding ──
    EMBEDDING_MODEL                 = "EMBEDDING_MODEL"
    # ── Безпека ──
    ENCRYPTION_KEY                  = "ENCRYPTION_KEY"
    CORS_ORIGINS                    = "CORS_ORIGINS"
    ALLOWED_HOSTS                   = "ALLOWED_HOSTS"
    # ── Ліміти ──
    MAX_CONVERSATIONS_PER_USER      = "MAX_CONVERSATIONS_PER_USER"
    CONVERSATION_HISTORY_DAYS       = "CONVERSATION_HISTORY_DAYS"
    RATE_LIMIT_PER_MINUTE           = "RATE_LIMIT_PER_MINUTE"
    MAX_MESSAGE_LENGTH              = "MAX_MESSAGE_LENGTH"
    AUTO_CLEANUP_ENABLED            = "AUTO_CLEANUP_ENABLED"
    # ── Детекція залежності ──
    DEPENDENCY_SESSIONS_PER_DAY_WARN    = "DEPENDENCY_SESSIONS_PER_DAY_WARN"
    DEPENDENCY_SESSIONS_PER_WEEK_WARN   = "DEPENDENCY_SESSIONS_PER_WEEK_WARN"
    DEPENDENCY_AVG_DURATION_WARN_MIN    = "DEPENDENCY_AVG_DURATION_WARN_MIN"
    DEPENDENCY_MESSAGES_PER_DAY_WARN    = "DEPENDENCY_MESSAGES_PER_DAY_WARN"
    DEPENDENCY_CONSECUTIVE_DAYS_WARN    = "DEPENDENCY_CONSECUTIVE_DAYS_WARN"
    DEPENDENCY_REMINDER_INTERVAL_MSGS   = "DEPENDENCY_REMINDER_INTERVAL_MSGS"


class Settings:
    """Налаштування застосунку. Усі значення читаються явно з .env файлу."""

    def __init__(self) -> None:
        self._logger = get_logger(__name__)

        # ── Застосунок ──
        self.APP_NAME: str                      = self._get_setting(Env.APP_NAME)
        self.APP_VERSION: str                   = self._get_setting(Env.APP_VERSION)
        self.DEBUG: bool                        = self._get_setting(Env.DEBUG, default=False, cast=bool)
        self.ENVIRONMENT: str                   = self._get_setting(Env.ENVIRONMENT)

        # ── Сервер ──
        self.HOST: str                          = self._get_setting(Env.HOST)
        self.PORT: int                          = int(self._get_setting(Env.PORT))

        # ── База даних ──
        self.POSTGRES_USER: str                 = self._get_setting(Env.POSTGRES_USER)
        self.POSTGRES_PASSWORD: str             = self._get_setting(Env.POSTGRES_PASSWORD)
        self.POSTGRES_HOST: str                 = self._get_setting(Env.POSTGRES_HOST)
        self.POSTGRES_PORT: int                 = int(self._get_setting(Env.POSTGRES_PORT))
        self.POSTGRES_DB: str                   = self._get_setting(Env.POSTGRES_DB)

        # ── Redis ──
        self.REDIS_HOST: str                    = self._get_setting(Env.REDIS_HOST)
        self.REDIS_PORT: int                    = int(self._get_setting(Env.REDIS_PORT))
        self.REDIS_DB: int                      = int(self._get_setting(Env.REDIS_DB))

        # ── JWT ──
        self.JWT_SECRET_KEY: str                = self._get_setting(Env.JWT_SECRET_KEY)
        self.JWT_ALGORITHM: str                 = self._get_setting(Env.JWT_ALGORITHM)
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int   = int(self._get_setting(Env.ACCESS_TOKEN_EXPIRE_MINUTES))
        self.REFRESH_TOKEN_EXPIRE_DAYS: int     = int(self._get_setting(Env.REFRESH_TOKEN_EXPIRE_DAYS))

        # ── AI / LLM ──
        self.ANTHROPIC_API_KEY: str             = self._get_setting(Env.ANTHROPIC_API_KEY)
        self.ANTHROPIC_MODEL: str               = self._get_setting(Env.ANTHROPIC_MODEL)
        self.GEMINI_API_KEY: str                = self._get_setting(Env.GEMINI_API_KEY)
        self.GEMINI_MODEL: str                  = self._get_setting(Env.GEMINI_MODEL)
        self.AI_MAX_TOKENS: int                 = int(self._get_setting(Env.AI_MAX_TOKENS))
        self.AI_TEMPERATURE: float              = float(self._get_setting(Env.AI_TEMPERATURE))
        self.AI_CONTEXT_MESSAGES: int           = int(self._get_setting(Env.AI_CONTEXT_MESSAGES))
        self.AI_PREV_SUMMARIES_COUNT: int       = int(self._get_setting(Env.AI_PREV_SUMMARIES_COUNT))

        # ── Embedding ──
        self.EMBEDDING_MODEL: str               = self._get_setting(Env.EMBEDDING_MODEL)

        # ── Безпека ──
        self.ENCRYPTION_KEY: str                = self._get_setting(Env.ENCRYPTION_KEY)
        self.CORS_ORIGINS: list[str]            = json.loads(self._get_setting(Env.CORS_ORIGINS))
        self.ALLOWED_HOSTS: list[str]           = json.loads(self._get_setting(Env.ALLOWED_HOSTS, default='["*"]'))

        # ── Ліміти ──
        self.MAX_CONVERSATIONS_PER_USER: int    = int(self._get_setting(Env.MAX_CONVERSATIONS_PER_USER))
        self.CONVERSATION_HISTORY_DAYS: int     = int(self._get_setting(Env.CONVERSATION_HISTORY_DAYS))
        self.RATE_LIMIT_PER_MINUTE: int         = int(self._get_setting(Env.RATE_LIMIT_PER_MINUTE))
        self.MAX_MESSAGE_LENGTH: int            = int(self._get_setting(Env.MAX_MESSAGE_LENGTH, default=5000))
        self.AUTO_CLEANUP_ENABLED: bool         = self._get_setting(Env.AUTO_CLEANUP_ENABLED, default=True, cast=bool)

        # ── Детекція залежності ──
        self.DEPENDENCY_SESSIONS_PER_DAY_WARN: int  = int(self._get_setting(Env.DEPENDENCY_SESSIONS_PER_DAY_WARN))
        self.DEPENDENCY_SESSIONS_PER_WEEK_WARN: int = int(self._get_setting(Env.DEPENDENCY_SESSIONS_PER_WEEK_WARN))
        self.DEPENDENCY_AVG_DURATION_WARN_MIN: int  = int(self._get_setting(Env.DEPENDENCY_AVG_DURATION_WARN_MIN))
        self.DEPENDENCY_MESSAGES_PER_DAY_WARN: int  = int(self._get_setting(Env.DEPENDENCY_MESSAGES_PER_DAY_WARN))
        self.DEPENDENCY_CONSECUTIVE_DAYS_WARN: int  = int(self._get_setting(Env.DEPENDENCY_CONSECUTIVE_DAYS_WARN))
        self.DEPENDENCY_REMINDER_INTERVAL_MSGS: int = int(self._get_setting(Env.DEPENDENCY_REMINDER_INTERVAL_MSGS))


    def _get_setting(self, name: Env, default: str | int | bool | None = None, cast: type | None = None) -> str:
        """Зчитує змінну оточення за іменем.

        Args:
            name: Назва змінної з Env enum.
            default: Дефолтне значення. Якщо None — змінна обов'язкова.
            cast: Якщо bool — перетворює "true"/"1"/"yes" → True.

        Returns:
            Рядкове значення змінної.

        Raises:
            ValueError: Якщо обов'язкова змінна відсутня в .env.
        """
        value = os.environ.get(name)

        if value is not None:
            if default is not None:
                self._logger.warning(f"Змінна {name} перевизначена через env (значення відрізняється від дефолту).")
            else:
                self._logger.info(f"Змінна {name} завантажена з env.")

            if cast is bool:
                return value.strip().lower() in ("true", "1", "yes")  # type: ignore[return-value]
            return value

        if default is None:
            raise ValueError(
                f"Обов'язкова змінна '{name}' не знайдена в .env і не має дефолтного значення."
            )

        self._logger.info(f"Змінна {name} використовує дефолтне значення: {default!r}.")
        if cast is bool:
            return default  # type: ignore[return-value]
        return str(default)

    # ── Обчислювані URL ──

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = Settings()
