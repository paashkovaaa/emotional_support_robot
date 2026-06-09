"""API роутер для дихальних вправ."""

from fastapi import APIRouter, Query

from backend.app.schemas.breathing import (
    BreathingExerciseRead,
    BreathingExerciseShort,
)
from backend.app.services.breathing_service import BreathingService

router = APIRouter()


@router.get(
    "/",
    response_model=list[BreathingExerciseShort],
    summary="Список дихальних вправ",
)
async def list_breathing_exercises(
    tag: str | None = Query(default=None, description="Фільтр за тегом (наприклад, 'тривога')"),
    difficulty: str | None = Query(default=None, description="Фільтр за складністю: easy | medium | hard"),
):
    """Повертає список усіх дихальних вправ.

    Підтримує фільтрацію:
    - **tag** — показати лише вправи з певним тегом.
    - **difficulty** — показати лише вправи певної складності.
    """
    service = BreathingService()
    return service.get_all(tag=tag, difficulty=difficulty)


@router.get(
    "/tags",
    response_model=list[str],
    summary="Список доступних тегів",
)
async def list_tags():
    """Повертає список усіх унікальних тегів дихальних вправ.

    Корисно для фільтрації на фронтенді.
    """
    service = BreathingService()
    return service.get_tags()


@router.get(
    "/{exercise_id}",
    response_model=BreathingExerciseRead,
    summary="Деталі дихальної вправи",
)
async def get_breathing_exercise(exercise_id: str):
    """Повертає повну інформацію про дихальну вправу, включно з фазами.

    Фази описують послідовність дій (вдих, затримка, видих)
    із зазначеною тривалістю кожної фази у секундах.
    """
    service = BreathingService()
    return service.get_by_id(exercise_id)

