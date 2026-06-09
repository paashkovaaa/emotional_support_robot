"""Pydantic-схеми для вправ на дихання."""

from pydantic import BaseModel, Field


class BreathingPhase(BaseModel):
    """Одна фаза дихальної вправи."""

    phase: str = Field(
        description="Тип фази: inhale | hold | exhale",
        examples=["inhale", "hold", "exhale"],
    )
    label_uk: str = Field(
        description="Опис фази українською",
        examples=["Вдих", "Затримка", "Видих"],
    )
    duration_seconds: int = Field(
        ge=1,
        description="Тривалість фази у секундах",
    )


class BreathingExerciseRead(BaseModel):
    """Повна інформація про дихальну вправу."""

    id: str = Field(description="Унікальний ідентифікатор вправи")
    name_uk: str = Field(description="Назва вправи українською")
    description_uk: str = Field(description="Опис вправи українською")
    phases: list[BreathingPhase] = Field(description="Фази дихального циклу")
    cycles: int = Field(ge=1, description="Кількість циклів")
    total_duration_seconds: int = Field(
        ge=1, description="Загальна тривалість вправи у секундах"
    )
    difficulty: str = Field(
        description="Складність: easy | medium | hard",
        examples=["easy", "medium", "hard"],
    )
    tags: list[str] = Field(description="Теги вправи")


class BreathingExerciseShort(BaseModel):
    """Коротка інформація про дихальну вправу (для списку)."""

    id: str
    name_uk: str
    description_uk: str
    cycles: int
    total_duration_seconds: int
    difficulty: str
    tags: list[str]

