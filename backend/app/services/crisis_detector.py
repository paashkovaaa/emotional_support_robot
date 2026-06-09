from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from backend.app.core.logging import get_logger
from backend.app.core.perf_logger import record_crisis
from backend.app.models.message import CrisisLevel

logger = get_logger(__name__)

# ── Шлях до кризових контактів ──
_CONTACTS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "crisis_contacts.json"


# ─────────────────────────────────────────────
# Словники тригерних слів/фраз за рівнями
# ─────────────────────────────────────────────

_# CRITICAL — наміри або конкретні плани (пряма загроза)
_CRITICAL_PATTERNS: list[str] = [
    r"(pattern_intent_1|pattern_intent_2).{0,15}(action_1|action_2)",
    r"(pattern_method_1|pattern_method_2)",
    r"(pattern_farewell_1|pattern_farewell_2)"
    # [REDACTED]: З етичних міркувань реальні регулярні вирази
    # для детекції прямої загрози приховані
]

# HIGH — серйозні ознаки кризи, пасивні деструктивні думки
_HIGH_KEYWORDS: list[str] = [
    "маркер_пасивного_відчаю_1",
    "маркер_бажання_зникнути",
    "маркер_високого_ризику_N"
    # [REDACTED]: Повний словник фраз високого рівня небезпеки приховано
]

# MEDIUM — виражений відчай, безнадія, синдром "тягаря"
_MEDIUM_KEYWORDS: list[str] = [
    "маркер_емоційного_тягаря",
    "маркер_повної_безнадії",
    "маркер_панічної_атаки"
]

# LOW — загальний негатив, психологічний стрес, депресивні настрої
_LOW_KEYWORDS: list[str] = [
    "постійна тривожність",
    "емоційне вигорання",
    "хронічне безсоння",
    "глибока апатія",
    "відчуття самотності"
    # Для рівня LOW залишено кілька реальних прикладів для демонстрації
]


# ─────────────────────────────────────────────
# Результат перевірки
# ─────────────────────────────────────────────

@dataclass
class CrisisCheckResult:
    """Результат перевірки повідомлення на кризовий стан."""

    crisis_level: CrisisLevel
    is_crisis: bool
    matched_keywords: list[str] = field(default_factory=list)
    crisis_response: str | None = None

    @property
    def should_notify(self) -> bool:
        """Чи потрібно показати кризове сповіщення (HIGH або CRITICAL)."""
        return self.crisis_level in (CrisisLevel.HIGH, CrisisLevel.CRITICAL)


# ─────────────────────────────────────────────
# Кризові відповіді бота
# ─────────────────────────────────────────────

_CRISIS_RESPONSES: dict[str, str] = {
    "critical": (
        "🆘 Я бачу, що тобі зараз дуже тяжко, і я серйозно ставлюсь до того, "
        "що ти написав(ла). Будь ласка, зверніся за допомогою прямо зараз:\n\n"
        "📞 **7333** — Лайфлайн Україна (безкоштовно, 24/7)\n"
        "📞 **103** — Екстрена медична допомога\n\n"
        "Ти не самотній/самотня. Звертатися по допомогу — це прояв сили, не слабкості. "
        "Будь ласка, зателефонуй зараз. 💙"
    ),
    "high": (
        "🤍 Мені дуже важливо те, що ти зараз відчуваєш. Я чую тебе. "
        "Будь ласка, зверніся за професійною допомогою — є люди, які можуть допомогти:\n\n"
        "📞 **7333** — Лайфлайн Україна (безкоштовно, 24/7)\n"
        "📞 **0 800 500 335** — Національна гаряча лінія\n\n"
        "Я — бот, і мої можливості обмежені. Але фахівці на гарячій лінії "
        "зможуть підтримати тебе набагато краще. 💙"
    ),
    "medium": (
        "💛 Я бачу, що тобі зараз непросто. Дякую, що довіряєш мені свої почуття. "
        "Якщо тобі потрібна додаткова підтримка — ти завжди можеш зателефонувати "
        "на гарячу лінію **7333** (Лайфлайн Україна, безкоштовно, 24/7) або "
        "**0 800 500 335**.\n\n"
        "Пам'ятай: звертатися по допомогу — це нормально і правильно."
    ),
}

_compiled_critical: list[re.Pattern[str]] = [
    re.compile(pattern, re.IGNORECASE | re.UNICODE) for pattern in _CRITICAL_PATTERNS
]


class CrisisDetector:
    """Детектор кризових станів на основі ключових слів.

    Аналізує повідомлення від користувача та визначає рівень кризового ризику.
    Працює як перший шар детекції — швидкий і без залежності від AI.
    LLM-аналіз буде додано пізніше як другий шар.
    """

    def check_message(self, message: str) -> CrisisCheckResult:
        """Перевіряє повідомлення на ознаки кризового стану."""
        _start = time.perf_counter()

        if not message or not message.strip():
            record_crisis(0, 0.0, "NONE", 0)
            return CrisisCheckResult(crisis_level=CrisisLevel.NONE, is_crisis=False)

        text = self._normalize(message)
        matched: list[str] = []

        # 1. Перевірка CRITICAL (regex патерни)
        for pattern in _compiled_critical:
            match = pattern.search(text)
            if match:
                matched.append(match.group())
                self._log_crisis_event(CrisisLevel.CRITICAL, matched)
                record_crisis(len(message), (time.perf_counter() - _start) * 1000, "CRITICAL", len(matched))
                return CrisisCheckResult(
                    crisis_level=CrisisLevel.CRITICAL,
                    is_crisis=True,
                    matched_keywords=matched,
                    crisis_response=_CRISIS_RESPONSES["critical"],
                )

        # 2. Перевірка HIGH (ключові слова)
        high_matches = self._find_keywords(text, _HIGH_KEYWORDS)
        if high_matches:
            matched.extend(high_matches)
            self._log_crisis_event(CrisisLevel.HIGH, matched)
            record_crisis(len(message), (time.perf_counter() - _start) * 1000, "HIGH", len(matched))
            return CrisisCheckResult(
                crisis_level=CrisisLevel.HIGH,
                is_crisis=True,
                matched_keywords=matched,
                crisis_response=_CRISIS_RESPONSES["high"],
            )

        # 3. Перевірка MEDIUM
        medium_matches = self._find_keywords(text, _MEDIUM_KEYWORDS)
        if medium_matches:
            matched.extend(medium_matches)
            self._log_crisis_event(CrisisLevel.MEDIUM, matched)
            record_crisis(len(message), (time.perf_counter() - _start) * 1000, "MEDIUM", len(matched))
            return CrisisCheckResult(
                crisis_level=CrisisLevel.MEDIUM,
                is_crisis=True,
                matched_keywords=matched,
                crisis_response=_CRISIS_RESPONSES["medium"],
            )

        # 4. Перевірка LOW
        low_matches = self._find_keywords(text, _LOW_KEYWORDS)
        if low_matches:
            matched.extend(low_matches)
            record_crisis(len(message), (time.perf_counter() - _start) * 1000, "LOW", len(matched))
            return CrisisCheckResult(
                crisis_level=CrisisLevel.LOW,
                is_crisis=False,
                matched_keywords=matched,
                crisis_response=None,
            )

        # 5. Нічого не знайдено
        record_crisis(len(message), (time.perf_counter() - _start) * 1000, "NONE", 0)
        return CrisisCheckResult(crisis_level=CrisisLevel.NONE, is_crisis=False)

    def get_crisis_contacts(self) -> dict:
        """Повертає кризові контакти з JSON-файлу.

        Returns:
            Словник з контактами та дисклеймером.
        """
        try:
            with open(_CONTACTS_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "contacts": [
                    {"name_uk": "Лайфлайн Україна", "phone": "7333"},
                    {"name_uk": "Екстрена допомога", "phone": "103"},
                ],
            }

    # ── Приватні методи ──

    @staticmethod
    def _normalize(text: str) -> str:
        """Нормалізує текст для пошуку.

        - Переводить у нижній регістр
        - Замінює апострофи на стандартний
        - Видаляє зайві пробіли
        """
        text = text.lower().strip()
        # Нормалізація апострофів (ʼ ' ʼ → ')
        text = re.sub(r"[ʼ'`]", "'", text)
        # Видалення зайвих пробілів
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def _find_keywords(text: str, keywords: list[str]) -> list[str]:
        """Знаходить ключові слова у тексті.

        Args:
            text: Нормалізований текст повідомлення.
            keywords: Список ключових слів для пошуку.

        Returns:
            Список знайдених ключових слів.
        """
        found: list[str] = []
        for keyword in keywords:
            kw = keyword.lower()
            if kw in text:
                found.append(keyword)
        return found

    @staticmethod
    def _log_crisis_event(level: CrisisLevel, keywords: list[str]) -> None:
        """Логує кризову подію (без персональних даних).

        Зберігає лише рівень ризику та кількість знайдених тригерів.
        Конкретні слова не логуються для захисту конфіденційності.
        """
        logger.warning(
            f"🚨 CRISIS DETECTED: level={level.value}, "
            f"triggers_count={len(keywords)}"
        )


# ── Singleton-інстанс для зручності ──
crisis_detector = CrisisDetector()

