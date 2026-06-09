"""Інтеграційні тести API дихальних вправ."""

import pytest
from httpx import AsyncClient


class TestBreathingExercisesAPI:
    """Тести GET /api/breathing-exercises/."""

    async def test_list_exercises(self, client: AsyncClient):
        response = await client.get("/api/breathing-exercises/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    async def test_list_exercises_has_fields(self, client: AsyncClient):
        response = await client.get("/api/breathing-exercises/")
        data = response.json()
        for item in data:
            assert "id" in item
            assert "name_uk" in item
            assert "description_uk" in item
            assert "difficulty" in item
            assert "tags" in item

    async def test_filter_by_difficulty(self, client: AsyncClient):
        response = await client.get("/api/breathing-exercises/?difficulty=easy")
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["difficulty"] == "easy"


class TestBreathingExerciseDetailAPI:
    """Тести GET /api/breathing-exercises/{id}."""

    async def test_get_exercise_by_id(self, client: AsyncClient):
        # Спочатку отримуємо список
        list_resp = await client.get("/api/breathing-exercises/")
        exercises = list_resp.json()
        if exercises:
            ex_id = exercises[0]["id"]
            response = await client.get(f"/api/breathing-exercises/{ex_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == ex_id
            assert "phases" in data
            assert len(data["phases"]) > 0

    async def test_get_exercise_not_found(self, client: AsyncClient):
        response = await client.get("/api/breathing-exercises/nonexistent-id")
        assert response.status_code == 404


class TestBreathingTagsAPI:
    """Тести GET /api/breathing-exercises/tags."""

    async def test_list_tags(self, client: AsyncClient):
        response = await client.get("/api/breathing-exercises/tags")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

