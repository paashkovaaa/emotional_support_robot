"""Тести детектора кризових станів."""

import pytest

from backend.app.models.message import CrisisLevel
from backend.app.services.crisis_detector import CrisisDetector, CrisisCheckResult


@pytest.fixture
def detector() -> CrisisDetector:
    return CrisisDetector()


class TestCrisisDetectorCritical:
    """Тести CRITICAL рівня — конкретні плани/наміри."""

    def test_direct_intent_kill_self(self, detector: CrisisDetector):
        result = detector.check_message("Хочу покінчити з собою")
        assert result.crisis_level == CrisisLevel.CRITICAL
        assert result.is_crisis is True
        assert result.crisis_response is not None

    def test_decision_to_end_life(self, detector: CrisisDetector):
        result = detector.check_message("Я вирішила покінчити з життям")
        assert result.crisis_level == CrisisLevel.CRITICAL
        assert result.is_crisis is True

    def test_decision_to_end_life_male(self, detector: CrisisDetector):
        result = detector.check_message("Я вирішив покінчити з життям")
        assert result.crisis_level == CrisisLevel.CRITICAL
        assert result.is_crisis is True

    def test_planning_to_end_life(self, detector: CrisisDetector):
        result = detector.check_message("Планую покінчити")
        assert result.crisis_level == CrisisLevel.CRITICAL
        assert result.is_crisis is True

    def test_farewell(self, detector: CrisisDetector):
        result = detector.check_message("Прощайте")
        assert result.crisis_level == CrisisLevel.CRITICAL
        assert result.is_crisis is True

    def test_last_message(self, detector: CrisisDetector):
        result = detector.check_message("Це моє останнє повідомлення")
        assert result.crisis_level == CrisisLevel.CRITICAL
        assert result.is_crisis is True

    def test_pills_overdose(self, detector: CrisisDetector):
        result = detector.check_message("Вип'ю таблетки")
        assert result.crisis_level == CrisisLevel.CRITICAL
        assert result.is_crisis is True

    def test_jump_from_bridge(self, detector: CrisisDetector):
        result = detector.check_message("Стрибну з мосту")
        assert result.crisis_level == CrisisLevel.CRITICAL
        assert result.is_crisis is True

    def test_today_last_day(self, detector: CrisisDetector):
        result = detector.check_message("Це мій останній день")
        assert result.crisis_level == CrisisLevel.CRITICAL
        assert result.is_crisis is True

    def test_crisis_response_contains_phone(self, detector: CrisisDetector):
        result = detector.check_message("Хочу покінчити з життям")
        assert "7333" in result.crisis_response
        assert "103" in result.crisis_response


class TestCrisisDetectorHigh:
    """Тести HIGH рівня — серйозні ознаки кризи, бажання смерті."""

    def test_crisis_keyword_high(self, detector: CrisisDetector):
        result = detector.check_message("Не хочу більше жити")
        assert result.crisis_level == CrisisLevel.HIGH
        assert result.is_crisis is True

    def test_want_to_die(self, detector: CrisisDetector):
        result = detector.check_message("Хочу померти")
        assert result.crisis_level == CrisisLevel.HIGH
        assert result.is_crisis is True

    def test_dont_want_to_live(self, detector: CrisisDetector):
        result = detector.check_message("Не хочу жити")
        assert result.crisis_level == CrisisLevel.HIGH
        assert result.is_crisis is True

    def test_want_everything_to_end(self, detector: CrisisDetector):
        result = detector.check_message("Хочу щоб все закінчилось")
        assert result.crisis_level == CrisisLevel.HIGH
        assert result.is_crisis is True

    def test_disappear_forever(self, detector: CrisisDetector):
        result = detector.check_message("Хочу зникнути назавжди")
        assert result.crisis_level == CrisisLevel.HIGH
        assert result.is_crisis is True

    def test_better_without_me(self, detector: CrisisDetector):
        # "всім буде краще без мене" is MEDIUM level
        result = detector.check_message("Краще б мене не було")
        assert result.crisis_level == CrisisLevel.HIGH
        assert result.is_crisis is True

    def test_sleep_and_not_wake_up(self, detector: CrisisDetector):
        result = detector.check_message("Хочу заснути і не прокинутись")
        assert result.crisis_level == CrisisLevel.HIGH
        assert result.is_crisis is True

    def test_high_crisis_response_contains_phone(self, detector: CrisisDetector):
        result = detector.check_message("Хочу померти")
        assert result.crisis_response is not None
        assert "7333" in result.crisis_response


class TestCrisisDetectorMedium:
    """Тести MEDIUM рівня — виражений відчай, безнадія."""

    def test_hopelessness(self, detector: CrisisDetector):
        result = detector.check_message("Все безнадійно")
        assert result.crisis_level == CrisisLevel.MEDIUM
        assert result.is_crisis is True

    def test_no_way_out(self, detector: CrisisDetector):
        result = detector.check_message("Не бачу виходу з цього")
        assert result.crisis_level == CrisisLevel.MEDIUM
        assert result.is_crisis is True

    def test_nobody_needs_me(self, detector: CrisisDetector):
        result = detector.check_message("Нікому я не потрібна")
        assert result.crisis_level == CrisisLevel.MEDIUM
        assert result.is_crisis is True

    def test_i_am_burden(self, detector: CrisisDetector):
        result = detector.check_message("Я тягар для всіх")
        assert result.crisis_level == CrisisLevel.MEDIUM
        assert result.is_crisis is True

    def test_want_to_disappear(self, detector: CrisisDetector):
        result = detector.check_message("Хочу зникнути")
        assert result.crisis_level == CrisisLevel.MEDIUM
        assert result.is_crisis is True

    def test_cannot_take_it_anymore(self, detector: CrisisDetector):
        result = detector.check_message("Не можу більше")
        assert result.crisis_level == CrisisLevel.MEDIUM
        assert result.is_crisis is True

    def test_panic_attack(self, detector: CrisisDetector):
        result = detector.check_message("У мене панічна атака")
        assert result.crisis_level == CrisisLevel.MEDIUM
        assert result.is_crisis is True

    def test_hate_myself(self, detector: CrisisDetector):
        result = detector.check_message("Ненавиджу себе")
        assert result.crisis_level == CrisisLevel.MEDIUM
        assert result.is_crisis is True


class TestCrisisDetectorLow:
    """Тести LOW рівня — загальний негатив, стрес."""

    def test_depression(self, detector: CrisisDetector):
        result = detector.check_message("У мене депресія")
        assert result.crisis_level == CrisisLevel.LOW
        assert result.is_crisis is False  # LOW не вважається кризою

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


class TestCrisisDetectorEdgeCases:
    """Тести граничних випадків."""

    def test_case_insensitive(self, detector: CrisisDetector):
        result = detector.check_message("ХОЧУ ПОМЕРТИ")
        assert result.crisis_level == CrisisLevel.HIGH

    def test_apostrophe_normalization(self, detector: CrisisDetector):
        result = detector.check_message("Вип'ю таблетки")
        assert result.crisis_level == CrisisLevel.CRITICAL

    def test_extra_spaces(self, detector: CrisisDetector):
        result = detector.check_message("  хочу   померти  ")
        assert result.crisis_level == CrisisLevel.HIGH

    def test_matched_keywords_returned(self, detector: CrisisDetector):
        result = detector.check_message("У мене депресія і тривога")
        assert len(result.matched_keywords) >= 1

    def test_should_notify_critical(self, detector: CrisisDetector):
        result = detector.check_message("Хочу покінчити з собою")
        assert result.should_notify is True

    def test_should_notify_high(self, detector: CrisisDetector):
        result = detector.check_message("Хочу померти")
        assert result.should_notify is True

    def test_should_not_notify_medium(self, detector: CrisisDetector):
        result = detector.check_message("Все безнадійно")
        assert result.should_notify is False

    def test_should_not_notify_none(self, detector: CrisisDetector):
        result = detector.check_message("Привіт")
        assert result.should_notify is False


class TestCrisisContacts:
    """Тести кризових контактів."""

    def test_get_contacts(self, detector: CrisisDetector):
        contacts = detector.get_crisis_contacts()
        assert "contacts" in contacts
        assert len(contacts["contacts"]) > 0

