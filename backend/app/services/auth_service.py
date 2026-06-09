"""Сервіс автентифікації та управління користувачами."""

import uuid
from datetime import datetime, timezone

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import (
    BadRequestError,
    ConflictError,
    NotFoundError,
    UnauthorizedError,
)
from backend.app.core.security import (
    create_token_pair,
    decode_token,
    hash_password,
    verify_password,
)
from backend.app.models.profile import Profile
from backend.app.models.user import User, UserRole


class AuthService:
    """Сервіс для реєстрації, логіну, оновлення токенів."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Реєстрація ──

    async def register(self, email: str, password: str, nickname: str) -> User:
        """Реєструє нового користувача та створює профіль.

        Args:
            email: Email.
            password: Пароль (відкритий текст).
            nickname: Нікнейм для профілю.

        Returns:
            Створений об'єкт User.

        Raises:
            ConflictError: Якщо email вже зареєстрований.
        """
        # Перевіряємо чи email вже існує
        existing = await self._get_user_by_email(email)
        if existing:
            raise ConflictError("Користувач з таким email вже існує")

        # Створюємо користувача
        user = User(
            email=email,
            hashed_password=hash_password(password),
            role=UserRole.USER,
        )
        self.db.add(user)
        await self.db.flush()  # Отримуємо user.id без commit

        # Створюємо профіль
        profile = Profile(
            user_id=user.id,
            nickname=nickname,
        )
        self.db.add(profile)
        await self.db.flush()

        return user

    # ── Логін ──

    async def login(self, email: str, password: str) -> dict[str, str]:
        """Аутентифікує користувача та повертає пару токенів.

        Args:
            email: Email.
            password: Пароль.

        Returns:
            Словник з access_token, refresh_token, token_type.

        Raises:
            UnauthorizedError: Якщо email/пароль невірні або акаунт заблоковано.
        """
        user = await self._get_user_by_email(email)

        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Невірний email або пароль")

        if user.is_blocked:
            raise UnauthorizedError("Акаунт заблоковано. Зверніться до підтримки.")

        if not user.is_active:
            raise UnauthorizedError("Акаунт деактивовано")

        # Оновлюємо last_login
        user.last_login = datetime.now(timezone.utc)
        await self.db.flush()

        return create_token_pair(
            user_id=str(user.id),
            role=user.role.value,
            email=user.email,
        )

    # ── Refresh ──

    async def refresh_tokens(self, refresh_token: str) -> dict[str, str]:
        """Оновлює пару токенів за refresh token.

        Args:
            refresh_token: JWT refresh token.

        Returns:
            Нова пара токенів.

        Raises:
            UnauthorizedError: Якщо токен невалідний.
        """
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise UnauthorizedError("Невалідний refresh token")

        if payload.get("type") != "refresh":
            raise UnauthorizedError("Невалідний тип токена")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("Невалідний refresh token")

        user = await self._get_user_by_id(uuid.UUID(user_id))
        if not user:
            raise UnauthorizedError("Користувача не знайдено")

        if user.is_blocked or not user.is_active:
            raise UnauthorizedError("Акаунт заблоковано або деактивовано")

        return create_token_pair(
            user_id=str(user.id),
            role=user.role.value,
            email=user.email,
        )

    # ── Зміна пароля ──

    async def change_password(
        self, user: User, old_password: str, new_password: str
    ) -> None:
        """Змінює пароль користувача.

        Args:
            user: Об'єкт User.
            old_password: Старий пароль.
            new_password: Новий пароль.

        Raises:
            BadRequestError: Якщо старий пароль невірний.
        """
        if not verify_password(old_password, user.hashed_password):
            raise BadRequestError("Невірний поточний пароль")

        user.hashed_password = hash_password(new_password)
        await self.db.flush()

    # ── Отримання користувачів ──

    async def _get_user_by_email(self, email: str) -> User | None:
        """Отримує користувача за email."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Отримує користувача за ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
