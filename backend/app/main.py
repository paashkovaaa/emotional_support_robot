"""FastAPI — головний файл застосунку."""

import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.core.logging import get_logger
from backend.app.core.middleware import SecurityHeadersMiddleware
from backend.app.core.rate_limit import RateLimitMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown events."""
    # ── Startup ──
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    logger.info(f"   Environment: {settings.ENVIRONMENT}")
    logger.info(f"   Debug: {settings.DEBUG}")

    # Підключення Redis
    redis_client = None
    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        await redis_client.ping()
        app.state.redis = redis_client
        logger.info("   ✅ Redis connected")
    except Exception as e:
        logger.warning(f"   ⚠️  Redis not available: {e}")
        app.state.redis = None

    # Запуск фонового очищення застарілих даних
    cleanup_task = None
    if settings.ENVIRONMENT != "test":
        from backend.app.services.cleanup_service import run_scheduled_cleanup

        cleanup_task = asyncio.create_task(run_scheduled_cleanup())
        logger.info("   🧹 Scheduled data cleanup task started")

    yield

    # ── Shutdown ──
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
    if redis_client:
        await redis_client.close()
    logger.info(f"👋 {settings.APP_NAME} shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Віртуальний робот для емоційної підтримки користувачів на основі технологій ШІ",
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/api/openapi.json" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# ── Middleware (порядок важливий — виконуються знизу вгору) ──

# 1. Security headers (найвнутрішніший — виконується останнім)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Rate limiting
app.add_middleware(RateLimitMiddleware, redis_client=None)  # Redis буде встановлений у lifespan

# 3. CORS (найзовнішніший — виконується першим)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset", "X-Request-ID"],
    max_age=600,  # Кешування preflight на 10 хвилин
)


# ── Health check ──
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Перевірка стану сервера."""
    redis_ok = False
    if hasattr(app.state, "redis") and app.state.redis:
        try:
            await app.state.redis.ping()
            redis_ok = True
        except Exception:
            pass

    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "redis": "connected" if redis_ok else "disconnected",
    }


# ── Роутери ──
from backend.app.api import auth, profile, emotions, admin, dependency, breathing, chat  # noqa: E402
from backend.app.api import legal  # noqa: E402

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(emotions.router, prefix="/api/emotions", tags=["Emotions"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(dependency.router, prefix="/api/dependency", tags=["Dependency"])
app.include_router(breathing.router, prefix="/api/breathing-exercises", tags=["Breathing"])
app.include_router(legal.router, prefix="/api/legal", tags=["Legal"])
