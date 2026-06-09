"""Тести модуля шифрування (AES-256-GCM)."""

import pytest

from backend.app.core.encryption import decrypt, encrypt, is_encrypted


class TestEncryption:
    """Тести AES-256-GCM шифрування."""

    def test_encrypt_decrypt_roundtrip(self):
        original = "Секретне повідомлення"
        encrypted = encrypt(original)
        decrypted = decrypt(encrypted)
        assert decrypted == original

    def test_encrypt_returns_different_ciphertext(self):
        """Кожне шифрування має давати різний результат (різний nonce)."""
        text = "Hello World"
        e1 = encrypt(text)
        e2 = encrypt(text)
        assert e1 != e2  # Різні nonce

    def test_encrypt_empty_string(self):
        result = encrypt("")
        assert result == ""

    def test_decrypt_empty_string(self):
        result = decrypt("")
        assert result == ""

    def test_decrypt_invalid_data(self):
        with pytest.raises(ValueError, match="Помилка розшифрування"):
            decrypt("це не зашифрований текст!!!!!!!!!!!!!!!!")

    def test_encrypt_unicode(self):
        text = "Привіт, 世界! 🌍"
        encrypted = encrypt(text)
        decrypted = decrypt(encrypted)
        assert decrypted == text

    def test_encrypt_long_text(self):
        text = "A" * 10000
        encrypted = encrypt(text)
        decrypted = decrypt(encrypted)
        assert decrypted == text

    def test_is_encrypted_true(self):
        encrypted = encrypt("test data")
        assert is_encrypted(encrypted) is True

    def test_is_encrypted_false_plain_text(self):
        assert is_encrypted("plain text") is False

    def test_is_encrypted_false_empty(self):
        assert is_encrypted("") is False

    def test_is_encrypted_false_short(self):
        assert is_encrypted("abc") is False

