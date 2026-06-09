"""Залежності FastAPI: отримання поточного користувача, перевірка ролей."""

import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.exceptions import ForbiddenError, UnauthorizedError
from backend.app.core.security import decode_token
from backend.app.database import get_db
from backend.app.models.user import User, UserRole

# ── OAuth2 Bearer схема ──
security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(security_scheme)
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Отримує поточного автентифікованого користувача з JWT.

    Args:
        credentials: Bearer token з заголовка Authorization.
        db: Сесія бази даних.

    Returns:
        Об'єкт User.

    Raises:
        UnauthorizedError: Якщо токен невалідний або користувач не знайдений.
    """
    if not credentials:
        raise UnauthorizedError("Необхідна автентифікація")

    token = credentials.credentials

    try:
        payload = decode_token(token)
    except JWTError:
        raise UnauthorizedError("Невалідний або прострочений токен")

    if payload.get("type") != "access":
        raise UnauthorizedError("Невалідний тип токена")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Невалідний токен")

    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise UnauthorizedError("Невалідний токен")

    stmt = select(User).where(User.id == uid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedError("Користувача не знайдено")

    if user.is_blocked:
        raise UnauthorizedError("Акаунт заблоковано")

    if not user.is_active:
        raise UnauthorizedError("Акаунт деактивовано")

    return user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Перевіряє, що поточний користувач — адміністратор.

    Args:
        current_user: Автентифікований користувач.

    Returns:
        Об'єкт User з роллю ADMIN.

    Raises:
        ForbiddenError: Якщо користувач не є адміністратором.
    """
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError("Доступ дозволено лише адміністраторам")
    return current_user


# ── Типи-скорочення для Annotated залежностей ──
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
