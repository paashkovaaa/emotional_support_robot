"""Тести сервісу дихальних вправ."""

import pytest

from backend.app.core.exceptions import NotFoundError
from backend.app.services.breathing_service import BreathingService


@pytest.fixture
def breathing_service() -> BreathingService:
    return BreathingService()


class TestBreathingServiceGetAll:
    """Тести отримання списку вправ."""

    def test_get_all_returns_list(self, breathing_service: BreathingService):
        exercises = breathing_service.get_all()
        assert isinstance(exercises, list)
        assert len(exercises) > 0

    def test_get_all_has_required_fields(self, breathing_service: BreathingService):
        exercises = breathing_service.get_all()
        for ex in exercises:
            assert ex.id
            assert ex.name_uk
            assert ex.description_uk
            assert ex.cycles > 0
            assert ex.total_duration_seconds > 0
            assert ex.difficulty in ("easy", "medium", "hard")
            assert isinstance(ex.tags, list)

    def test_filter_by_difficulty(self, breathing_service: BreathingService):
        easy = breathing_service.get_all(difficulty="easy")
        for ex in easy:
            assert ex.difficulty == "easy"

    def test_filter_by_nonexistent_difficulty(self, breathing_service: BreathingService):
        result = breathing_service.get_all(difficulty="impossible")
        assert result == []

    def test_filter_by_tag(self, breathing_service: BreathingService):
        all_exercises = breathing_service.get_all()
        if all_exercises:
            # Беремо перший тег з першої вправи
            first_tag = all_exercises[0].tags[0] if all_exercises[0].tags else None
            if first_tag:
                filtered = breathing_service.get_all(tag=first_tag)
                assert len(filtered) > 0


class TestBreathingServiceGetById:
    """Тести отримання вправи за ID."""

    def test_get_by_id_success(self, breathing_service: BreathingService):
        all_exercises = breathing_service.get_all()
        if all_exercises:
            exercise = breathing_service.get_by_id(all_exercises[0].id)
            assert exercise.id == all_exercises[0].id
            assert exercise.name_uk
            assert len(exercise.phases) > 0

    def test_get_by_id_has_phases(self, breathing_service: BreathingService):
        all_exercises = breathing_service.get_all()
        if all_exercises:
            exercise = breathing_service.get_by_id(all_exercises[0].id)
            for phase in exercise.phases:
                assert phase.phase in ("inhale", "hold", "exhale")
                assert phase.label_uk
                assert phase.duration_seconds > 0

    def test_get_by_id_not_found(self, breathing_service: BreathingService):
        with pytest.raises(NotFoundError):
            breathing_service.get_by_id("nonexistent-id")


class TestBreathingServiceGetTags:
    """Тести отримання тегів."""

    def test_get_tags_returns_list(self, breathing_service: BreathingService):
        tags = breathing_service.get_tags()
        assert isinstance(tags, list)

    def test_get_tags_sorted(self, breathing_service: BreathingService):
        tags = breathing_service.get_tags()
        assert tags == sorted(tags)

    def test_get_tags_unique(self, breathing_service: BreathingService):
        tags = breathing_service.get_tags()
        assert len(tags) == len(set(tags))

