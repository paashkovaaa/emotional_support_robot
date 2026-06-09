"""Тести безпечного логування (маскування персональних даних)."""

from backend.app.core.logging import sanitize, get_logger


class TestSanitize:
    """Тести маскування персональних даних."""

    def test_mask_email(self):
        result = sanitize("User user@example.com logged in")
        assert "user@example.com" not in result
        assert "u***@e***.com" in result

    def test_mask_multiple_emails(self):
        result = sanitize("From admin@test.org to user@example.com")
        assert "admin@test.org" not in result
        assert "user@example.com" not in result

    def test_mask_uuid(self):
        result = sanitize("User 12345678-1234-1234-1234-123456789abc deleted")
        assert "12345678-1234-1234-1234-123456789abc" not in result
        assert "12345678-****-****-****-************" in result

    def test_mask_jwt_token(self):
        token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyLTEyMyJ9.dBjftJeZ4CVP_mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        result = sanitize(f"Token: {token}")
        assert token not in result
        assert "eyJ***.***.***" in result

    def test_mask_bearer_token(self):
        result = sanitize("Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.signature")
        assert "Bearer ***" in result

    def test_mask_ip_address(self):
        result = sanitize("Request from 192.168.1.100")
        assert "192.168.1.100" not in result
        assert "192.168.*.*" in result

    def test_mask_password_in_dict(self):
        result = sanitize('{"password": "mysecret123"}')
        assert "mysecret123" not in result

    def test_no_masking_for_safe_text(self):
        text = "Hello world, this is a normal message"
        result = sanitize(text)
        assert result == text

    def test_empty_string(self):
        assert sanitize("") == ""


class TestSanitizedLogger:
    """Тести безпечного логера."""

    def test_get_logger_returns_logger(self):
        logger = get_logger("test")
        assert logger is not None

    def test_logger_has_methods(self):
        logger = get_logger("test")
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "critical")
        assert hasattr(logger, "exception")

