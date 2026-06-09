"""Тести детектора кризових станів."""

import pytest

from backend.app.models.message import CrisisLevel
from backend.app.services.crisis_detector import CrisisDetector, CrisisCheckResult


@pytest.fixture
def detector() -> CrisisDetector:
    return CrisisDetector()


class TestCrisisDetectorLow:
    """Тести LOW рівня — загальний негатив, стрес."""
    def test_anxiety(self, detector: CrisisDetector):
        result = detector.check_message("Мене мучить тривога")
        assert result.crisis_level == CrisisLevel.LOW
        assert result.is_crisis is False

    def test_sadness(self, detector: CrisisDetector):
        result = detector.check_message("Мені дуже сумно")
        assert result.crisis_level == CrisisLevel.LOW
        assert result.is_crisis is False

    def test_loneliness(self, detector: CrisisDetector):
        result = detector.check_message("Я дуже самотній")
        assert result.crisis_level == CrisisLevel.LOW
        assert result.is_crisis is False

    def test_stress(self, detector: CrisisDetector):
        result = detector.check_message("У мене сильний стрес")
        assert result.crisis_level == CrisisLevel.LOW
        assert result.is_crisis is False

    def test_crying(self, detector: CrisisDetector):
        result = detector.check_message("Я плачу")
        assert result.crisis_level == CrisisLevel.LOW

    def test_burnout(self, detector: CrisisDetector):
        result = detector.check_message("Повне вигорання")
        assert result.crisis_level == CrisisLevel.LOW

    def test_low_no_crisis_response(self, detector: CrisisDetector):
        result = detector.check_message("Мені сумно")
        assert result.crisis_response is None


class TestCrisisDetectorNone:
    """Тести NONE рівня — звичайні повідомлення."""

    def test_greeting(self, detector: CrisisDetector):
        result = detector.check_message("Привіт, як справи?")
        assert result.crisis_level == CrisisLevel.NONE
        assert result.is_crisis is False

    def test_neutral_message(self, detector: CrisisDetector):
        result = detector.check_message("Розкажи мені про дихальні вправи")
        assert result.crisis_level == CrisisLevel.NONE
        assert result.is_crisis is False

    def test_positive_message(self, detector: CrisisDetector):
        result = detector.check_message("Сьогодні чудовий день!")
        assert result.crisis_level == CrisisLevel.NONE
        assert result.is_crisis is False

    def test_empty_message(self, detector: CrisisDetector):
        result = detector.check_message("")
        assert result.crisis_level == CrisisLevel.NONE
        assert result.is_crisis is False

    def test_whitespace_only(self, detector: CrisisDetector):
        result = detector.check_message("   ")
        assert result.crisis_level == CrisisLevel.NONE
        assert result.is_crisis is False


class TestCrisisContacts:
    """Тести кризових контактів."""

    def test_get_contacts(self, detector: CrisisDetector):
        contacts = detector.get_crisis_contacts()
        assert "contacts" in contacts
        assert len(contacts["contacts"]) > 0

