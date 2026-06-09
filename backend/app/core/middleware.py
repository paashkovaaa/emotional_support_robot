"""Middleware безпеки: заголовки захисту, CORS hardening, request ID."""

import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Додає security-заголовки до кожної відповіді.

    Заголовки:
    - X-Content-Type-Options: захист від MIME sniffing
    - X-Frame-Options: захист від clickjacking
    - X-XSS-Protection: базовий захист від XSS
    - Strict-Transport-Security: примушує HTTPS
    - Referrer-Policy: обмежує передачу referrer
    - Content-Security-Policy: базова CSP політика
    - Permissions-Policy: обмежує доступ до API браузера
    - X-Request-ID: унікальний ID запиту для трасування
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Генеруємо унікальний ID запиту
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)

        # ── Security headers ──
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(self), geolocation=(), payment=()"
        )

        # HSTS — тільки для production
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # CSP — базова політика (дозволяємо inline для React)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "media-src 'self' blob:; "
            "frame-ancestors 'none'"
        )

        # Request ID для трасування
        response.headers["X-Request-ID"] = request_id

        return response


class TrustedHostMiddleware(BaseHTTPMiddleware):
    """Перевіряє, що запит приходить від довірених хостів.

    Захист від Host header attacks.
    """

    def __init__(self, app, allowed_hosts: list[str] | None = None):
        super().__init__(app)
        self.allowed_hosts = allowed_hosts or ["*"]

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if "*" in self.allowed_hosts:
            return await call_next(request)

        host = request.headers.get("host", "").split(":")[0]
        if host not in self.allowed_hosts:
            return Response(
                content="Invalid host header",
                status_code=400,
            )

        return await call_next(request)

