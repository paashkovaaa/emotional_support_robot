"""Сервіс детекції кризових станів на основі ключових слів.

Перший шар детекції: keyword-based аналіз повідомлень українською мовою.
Другий шар (LLM-аналіз) буде додано після вибору AI-моделі.

Рівні ризику:
- NONE: немає ознак кризи
- LOW: загальний негатив, розчарування, легкий стрес
- MEDIUM: виражений відчай, безнадія, сильне емоційне виснаження
- HIGH: прямі вираження бажання смерті або зникнути
- CRITICAL: конкретні плани або дії щодо завершення життя
"""

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

# CRITICAL — конкретні плани, методи, прощання
_CRITICAL_PATTERNS: list[str] = [
    # Прямі наміри
    r"хочу (покінчити з життям|покінчити із життям|покінчити з собою|покінчити із собою)",
    r"збираюс[ья] (покінчити)",
    r"планую (покінчити)",
    r"(вирішив|вирішила) (покінчити|піти з життя)",
    r"сьогодні я (покінчу|піду з життя)",
    r"це мій останній (день|вечір|раз)",
    r"це моє останнє повідомлення",
    r"прощай(те)?",
    r"напис(ав|ала) (записку|лист|заповіт)",
    r"передай(те)? .{0,30} що я (кохаю|люблю|любив|кохав)",
    # Конкретні методи
    r"(наковт|наковтн|випити|вип['ʼ]ю) .{0,20}(таблет|пігулок|пігулки|отрут)",
    r"(стрибну|стрибнути|стрибн) .{0,20}(з вікна|з мосту|з даху|з балкон)",
]

# HIGH — серйозні ознаки кризи, бажання смерті або зникнути
_HIGH_KEYWORDS: list[str] = [
    "хочу померти", "хочу вмерти", "хочу здохнути",
    "краще б я помер", "краще б я померла", "краще б я вмер",
    "краще б мене не було",
    "не хочу жити", "не хочу більше жити",
    "хочу зникнути назавжди",
    "піти з життя", "піду з життя",
    "покінчити з життям", "покінчити з собою",
    "покінчити із життям", "покінчити із собою",
    "не прокинутись", "не прокинутися",
    "заснути і не прокинутись", "заснути і не прокинутися",
    "хочу щоб все закінчилось", "хочу щоб все закінчилося",
]

# MEDIUM — виражений відчай, безнадія, непрямі натяки
_MEDIUM_KEYWORDS: list[str] = [
    "безнадія", "безнадійно", "безнадійний", "безнадійна",
    "безвихідь", "безвихідність", "безвихідно",
    "немає сенсу", "нема сенсу", "втратив сенс", "втратила сенс",
    "ніщо не має сенсу", "нічого не має сенсу",
    "не бачу виходу", "не бачу сенсу",
    "все марно", "все марне", "все безглуздо",
    "нікому не потрібен", "нікому не потрібна", "нікому я не потрібен", "нікому я не потрібна",
    "ніхто мене не любить", "мене ніхто не любить",
    "всім буде краще без мене", "їм буде краще без мене",
    "я тягар", "я обуза", "я зайвий", "я зайва",
    "хочу зникнути", "хочу щоб мене не було",
    "не витримую", "не можу більше", "не можу так далі",
    "не витримаю", "на межі",
    "хочу все припинити", "хочу це припинити",
    "більше не можу терпіти",
    "все набридло до смерті",
    "ненавиджу себе", "ненавиджу своє життя",
    "я нікчема", "я ніщо", "я нуль",
    "паніка", "панічна атака", "панічні атаки",
    "не можу дихати від тривоги",
]

# LOW — загальний негатив, стрес, депресивні настрої
_LOW_KEYWORDS: list[str] = [
    "депресія", "депресивний", "депресивна",
    "тривога", "тривожність", "тривожний", "тривожна",
    "сум", "сумно", "сумний", "сумна",
    "самотній", "самотня", "самотність",
    "плачу", "ревy", "хочеться плакати", "хочу плакати",
    "погано мені", "мені погано", "мені дуже погано",
    "все погано", "все дуже погано", "все жахливо",
    "апатія", "байдужість",
    "безсоння", "не можу спати", "не сплю",
    "втома", "виснаження", "знесилення", "знесилений", "знесилена",
    "стрес", "вигорання", "вигоряння",
    "розпач", "відчай",
    "пустота", "порожнеча", "порожньо всередині",
    "нічого не хочу", "нічого не радує",
    "мені боляче", "болить душа",
    "не бачу майбутнього",
    "ніхто не розуміє",
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
        "📞 **0 800 500 335** — Національна гаряча лінія з психічного здоров'я\n\n"
        "Я — бот, і мої можливості обмежені. Але фахівці на гарячій лінії "
        "зможуть підтримати тебе набагато краще. 💙"
    ),
    "medium": (
        "💛 Я бачу, що тобі зараз непросто. Дякую, що довіряєш мені свої почуття. "
        "Якщо тобі потрібна додаткова підтримка — ти завжди можеш зателефонувати "
        "на гарячу лінію **7333** (Лайфлайн Україна, безкоштовно, 24/7) або "
        "**0 800 500 335** (психічне здоров'я).\n\n"
        "Пам'ятай: звертатися по допомогу — це нормально і правильно."
    ),
}


# ─────────────────────────────────────────────
# Компіляція патернів
# ─────────────────────────────────────────────

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

