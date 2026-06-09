"""Інтеграційні тести API здоров'я та юридичних сторінок."""

import pytest
from httpx import AsyncClient


class TestHealthAPI:
    """Тести GET /api/health."""

    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "app" in data


class TestLegalAPI:
    """Тести юридичних ендпоінтів."""

    async def test_privacy_policy(self, client: AsyncClient):
        response = await client.get("/api/legal/privacy")
        assert response.status_code == 200

    async def test_terms_of_service(self, client: AsyncClient):
        response = await client.get("/api/legal/terms")
        assert response.status_code == 200

