"""Сервіс для роботи з дихальними вправами.

Завантажує вправи з JSON-файлу при ініціалізації та надає методи
для отримання списку та деталей кожної вправи.
"""

import json
from pathlib import Path
from typing import cast

from backend.app.core.exceptions import NotFoundError
from backend.app.schemas.breathing import BreathingExerciseRead, BreathingExerciseShort

# Шлях до JSON-файлу з вправами
_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "breathing_exercises.json"

# Кешовані дані (завантажуються один раз)
_exercises: list[dict] = []
_loaded: bool = False


def _load_exercises() -> list[dict]:
    """Завантажити вправи з JSON-файлу (з кешуванням)."""
    global _exercises, _loaded
    if not _loaded:
        with open(_DATA_PATH, encoding="utf-8") as f:
            _exercises = cast(list[dict], json.load(f))
        _loaded = True
    return _exercises


class BreathingService:
    """Сервіс дихальних вправ."""

    def get_all(
        self,
        tag: str | None = None,
        difficulty: str | None = None,
    ) -> list[BreathingExerciseShort]:
        """Повертає список усіх дихальних вправ (коротка форма).

        Args:
            tag: Фільтр за тегом (наприклад, 'тривога').
            difficulty: Фільтр за складністю ('easy', 'medium', 'hard').

        Returns:
            Відфільтрований список вправ.
        """
        exercises = _load_exercises()

        if tag:
            tag_lower = tag.lower()
            exercises = [e for e in exercises if tag_lower in [t.lower() for t in e.get("tags", [])]]

        if difficulty:
            diff_lower = difficulty.lower()
            exercises = [e for e in exercises if e.get("difficulty", "").lower() == diff_lower]

        return [BreathingExerciseShort(**e) for e in exercises]

    def get_by_id(self, exercise_id: str) -> BreathingExerciseRead:
        """Повертає деталі вправи за ID.

        Args:
            exercise_id: Ідентифікатор вправи.

        Returns:
            Повна інформація про вправу.

        Raises:
            NotFoundError: Якщо вправу не знайдено.
        """
        exercises = _load_exercises()

        for exercise in exercises:
            if exercise["id"] == exercise_id:
                return BreathingExerciseRead(**exercise)

        raise NotFoundError(f"Вправу з ID '{exercise_id}' не знайдено")

    def get_tags(self) -> list[str]:
        """Повертає список усіх унікальних тегів.

        Returns:
            Відсортований список тегів.
        """
        exercises = _load_exercises()
        tags: set[str] = set()
        for exercise in exercises:
            tags.update(exercise.get("tags", []))
        return sorted(tags)

