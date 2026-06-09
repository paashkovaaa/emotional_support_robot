"""Rate limiting middleware на базі Redis."""

import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from backend.app.config import settings
from backend.app.core.exceptions import RateLimitError


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware для обмеження частоти запитів (на базі Redis).

    Використовує алгоритм sliding window за IP-адресою.
    Окремі ліміти для auth-ендпоінтів (захист від brute-force).
    """

    # Ліміти за замовчуванням
    DEFAULT_LIMIT = settings.RATE_LIMIT_PER_MINUTE  # запитів на хвилину
    AUTH_LIMIT = 10  # для /auth ендпоінтів — суворіший ліміт
    WINDOW = 60  # секунди

    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis = redis_client

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Якщо Redis не підключено — пропускаємо
        if not self.redis:
            return await call_next(request)

        # Визначаємо ключ та ліміт
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        if "/api/auth/" in path:
            limit = self.AUTH_LIMIT
            key = f"rate_limit:auth:{client_ip}"
        else:
            limit = self.DEFAULT_LIMIT
            key = f"rate_limit:general:{client_ip}"

        # Перевіряємо ліміт (sliding window counter)
        now = time.time()
        window_start = now - self.WINDOW

        pipe = self.redis.pipeline()
        # Видаляємо старі записи
        pipe.zremrangebyscore(key, 0, window_start)
        # Рахуємо поточні запити у вікні
        pipe.zcard(key)
        # Додаємо поточний запит
        pipe.zadd(key, {str(now): now})
        # Встановлюємо TTL на ключ
        pipe.expire(key, self.WINDOW)

        results = await pipe.execute()
        request_count = results[1]

        if request_count >= limit:
            retry_after = int(self.WINDOW - (now - window_start))
            raise RateLimitError(
                detail=f"Забагато запитів. Спробуйте через {retry_after} секунд."
            )

        response = await call_next(request)

        # Додаємо заголовки rate limit
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - request_count - 1))
        response.headers["X-RateLimit-Reset"] = str(int(now + self.WINDOW))

        return response
