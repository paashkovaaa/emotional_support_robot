FROM python:3.12-slim

WORKDIR /app

# Системні залежності
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо pyproject.toml та README.md для встановлення залежностей
COPY pyproject.toml README.md ./

# Встановлюємо pip та залежності
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Копіюємо код та alembic конфігурацію
COPY backend/ ./backend/
COPY alembic.ini ./

# Порт
EXPOSE 8000

# Запуск
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
