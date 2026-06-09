"""API роутер автентифікації."""

from fastapi import APIRouter

from backend.app.api.deps import CurrentUser, DbSession
from backend.app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from backend.app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=201,
    summary="Реєстрація нового користувача",
)
async def register(body: RegisterRequest, db: DbSession):
    """Створює нового користувача та профіль.

    - **email**: Унікальний email.
    - **password**: Пароль (мін. 8 символів).
    - **nickname**: Нікнейм для профілю.
    """
    service = AuthService(db)
    user = await service.register(
        email=body.email,
        password=body.password,
        nickname=body.nickname,
    )
    return RegisterResponse(id=user.id, email=user.email)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вхід у систему",
)
async def login(body: LoginRequest, db: DbSession):
    """Аутентифікація за email та паролем.

    Повертає пару access + refresh JWT-токенів.
    """
    service = AuthService(db)
    tokens = await service.login(email=body.email, password=body.password)
    return TokenResponse(**tokens)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Оновлення токена",
)
async def refresh(body: RefreshRequest, db: DbSession):
    """Оновлює пару токенів за допомогою refresh token."""
    service = AuthService(db)
    tokens = await service.refresh_tokens(refresh_token=body.refresh_token)
    return TokenResponse(**tokens)


@router.post(
    "/logout",
    summary="Вихід із системи",
)
async def logout(current_user: CurrentUser):
    """Логаут (клієнт видаляє токен на своєму боці).

    На серверному боці токен залишається валідним до закінчення терміну дії.
    В майбутньому можна додати blacklist токенів через Redis.
    """
    return {"message": "Вихід виконано успішно"}


@router.post(
    "/change-password",
    summary="Зміна пароля",
)
async def change_password(
    body: ChangePasswordRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """Змінює пароль поточного користувача."""
    service = AuthService(db)
    await service.change_password(
        user=current_user,
        old_password=body.old_password,
        new_password=body.new_password,
    )
    return {"message": "Пароль змінено успішно"}
