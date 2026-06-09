"""Безпечне логування без персональних даних.

Маскує email-адреси, UUID, IP, токени та інші чутливі дані.
"""

import logging
import re
import sys
from typing import Any, Callable, Union

# Тип для заміни: рядок або callable
_Replacement = Union[str, Callable[[re.Match[str]], str]]

# ── Патерни для маскування ──
_PATTERNS: list[tuple[re.Pattern[str], _Replacement]] = [
    # Email: user@domain.com → u***@d***.com
    (
        re.compile(r"([a-zA-Z0-9._%+-])[a-zA-Z0-9._%+-]*@([a-zA-Z0-9.-])[a-zA-Z0-9.-]*\.(\w+)"),
        r"\1***@\2***.\3",
    ),
    # UUID: повний → перші 8 символів + ***
    (
        re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"),
        lambda m: m.group()[:8] + "-****-****-****-************",
    ),
    # JWT токен: eyJ... → eyJ***
    (
        re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
        "eyJ***.***.***",
    ),
    # Bearer token у заголовках
    (
        re.compile(r"(Bearer\s+)[A-Za-z0-9._-]+", re.IGNORECASE),
        r"\1***",
    ),
    # IP-адреса: 192.168.1.100 → 192.168.*.*
    (
        re.compile(r"(\d{1,3}\.\d{1,3}\.)\d{1,3}\.\d{1,3}"),
        r"\1*.*",
    ),
    # Пароль у словниках/JSON
    (
        re.compile(r'("?password"?\s*[:=]\s*)"?[^",}\s]+"?', re.IGNORECASE),
        r'\1"***"',
    ),
]


def sanitize(text: str) -> str:
    """Маскує персональні дані в тексті.

    Args:
        text: Вхідний текст для маскування.

    Returns:
        Текст з замаскованими персональними даними.
    """
    result = text
    for pattern, replacement in _PATTERNS:
        result = pattern.sub(replacement, result)  # type: ignore[call-overload]
    return result


class SanitizedFormatter(logging.Formatter):
    """Форматер логів, який автоматично маскує персональні дані."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        return sanitize(original)


class SanitizedLogger:
    """Обгортка для стандартного логера з автоматичним маскуванням."""

    def __init__(self, name: str, level: int = logging.INFO):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)

        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(
                SanitizedFormatter(
                    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
            self._logger.addHandler(handler)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.error(msg, *args, **kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.debug(msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.critical(msg, *args, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.exception(msg, *args, **kwargs)


def get_logger(name: str) -> SanitizedLogger:
    """Фабрика для створення безпечного логера.

    Args:
        name: Ім'я логера (зазвичай __name__).

    Returns:
        SanitizedLogger з автоматичним маскуванням.

    Example:
        logger = get_logger(__name__)
        logger.info("User u***@d***.com logged in from 192.168.*.*")
    """
    return SanitizedLogger(name)

