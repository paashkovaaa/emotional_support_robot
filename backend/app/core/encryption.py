"""Утиліти шифрування чутливих даних (AES-256-GCM).

Використовується для шифрування контенту повідомлень у БД.
"""

import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from backend.app.config import settings

# ── Довжина nonce для AES-GCM ──
_NONCE_LENGTH = 12  # 96 біт — рекомендація NIST


def _get_key() -> bytes:
    """Отримати 256-бітний ключ шифрування з конфігурації.

    Якщо ENCRYPTION_KEY не має рівно 32 байти — хешуємо через SHA-256.
    """
    raw = settings.ENCRYPTION_KEY.encode("utf-8")
    if len(raw) == 32:
        return raw
    return hashlib.sha256(raw).digest()


def encrypt(plaintext: str) -> str:
    """Шифрує рядок за допомогою AES-256-GCM.

    Args:
        plaintext: Відкритий текст.

    Returns:
        Base64-закодований рядок формату: nonce + ciphertext + tag.
    """
    if not plaintext:
        return plaintext

    key = _get_key()
    nonce = os.urandom(_NONCE_LENGTH)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

    # nonce (12 байт) + ciphertext+tag
    encrypted = nonce + ciphertext
    return base64.b64encode(encrypted).decode("utf-8")


def decrypt(encrypted_text: str) -> str:
    """Розшифровує рядок, зашифрований AES-256-GCM.

    Args:
        encrypted_text: Base64-закодований шифротекст.

    Returns:
        Розшифрований відкритий текст.

    Raises:
        ValueError: Якщо розшифрування не вдалося.
    """
    if not encrypted_text:
        return encrypted_text

    try:
        key = _get_key()
        raw = base64.b64decode(encrypted_text)

        nonce = raw[:_NONCE_LENGTH]
        ciphertext = raw[_NONCE_LENGTH:]

        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Помилка розшифрування: {e}") from e


def is_encrypted(text: str) -> bool:
    """Перевіряє, чи текст є зашифрованим (base64 + мінімальна довжина).

    Евристична перевірка — не гарантує 100% точність.
    """
    if not text or len(text) < 20:
        return False
    try:
        raw = base64.b64decode(text)
        return len(raw) > _NONCE_LENGTH
    except Exception:
        return False

