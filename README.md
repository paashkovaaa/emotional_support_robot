# 🤖💚 Emi — Віртуальний робот для емоційної підтримки

> Вебдодаток для емоційної підтримки користувачів на основі технологій штучного інтелекту.

## 📋 Зміст

- [Опис проекту](#-опис-проекту)
- [Технології](#-технології)
- [Структура проекту](#-структура-проекту)
- [Швидкий старт](#-швидкий-старт)
- [Запуск без Docker](#-запуск-без-docker)
- [API документація](#-api-документація)
- [Змінні оточення](#-змінні-оточення)
- [Ліцензія](#-ліцензія)

---

## 🌟 Опис проекту

**Emi** — це вебзастосунок, який надає емоційну підтримку через:

- 💬 **Чат з ШІ-помічником** — текстові розмови з емпатичним ботом
- 📓 **Щоденник емоцій** — відстеження емоційного стану з календарем та тегами
- 🫁 **Дихальні вправи** — анімовані техніки дихання для заспокоєння
- 🚨 **Кризова підтримка** — контакти гарячих ліній та екстреної допомоги
- 👤 **Профіль** — персоналізація стилю спілкування
- 🛡️ **Адмін-панель** — статистика, управління користувачами, база знань

---

## 🛠 Технології

### Backend
| Технологія | Призначення |
|---|---|
| **Python 3.12** | Мова програмування |
| **FastAPI** | Веб-фреймворк (REST + WebSocket) |
| **PostgreSQL 16 + pgvector** | Реляційна БД з підтримкою векторного пошуку |
| **Redis 7** | Кешування, rate limiting, pub/sub |
| **SQLAlchemy 2** | ORM (async) |
| **Alembic** | Міграції бази даних |
| **Pydantic v2** | Валідація даних |
| **JWT (PyJWT)** | Автентифікація |
| **bcrypt** | Хешування паролів |
| **AES-256** | Шифрування персональних даних |

### Frontend
| Технологія | Призначення |
|---|---|
| **React 18** | UI-фреймворк |
| **TypeScript** | Типізація |
| **Vite** | Збірка та dev-сервер |
| **Tailwind CSS 3** | Утилітарний CSS |
| **Zustand** | State management |
| **Axios** | HTTP-клієнт |
| **React Router v6** | Маршрутизація |
| **Lucide React** | Іконки |

### Інфраструктура
| Технологія | Призначення |
|---|---|
| **Docker & Docker Compose** | Контейнеризація |
| **Nginx** | Reverse proxy (production) |

---

## 📁 Структура проекту

```
emotional_support_robot/
├── backend/
│   ├── app/
│   │   ├── api/          # REST/WebSocket ендпоінти
│   │   ├── core/         # Безпека, middleware, промпти
│   │   ├── models/       # SQLAlchemy моделі
│   │   ├── schemas/      # Pydantic схеми
│   │   ├── services/     # Бізнес-логіка
│   │   └── utils/        # Утиліти
│   ├── alembic/          # Міграції БД
│   ├── data/             # JSON-дані (вправи, контакти)
│   └── tests/            # Тести
├── frontend/
│   ├── src/
│   │   ├── api/          # API-клієнти
│   │   ├── components/   # React компоненти
│   │   ├── hooks/        # Custom hooks
│   │   ├── pages/        # Сторінки
│   │   ├── stores/       # Zustand stores
│   │   ├── types/        # TypeScript типи
│   │   └── utils/        # Утиліти, константи
│   └── public/
├── docker/
│   └── nginx/            # Nginx конфігурація
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

---

## 🚀 Швидкий старт

### Передумови

- [Docker](https://docs.docker.com/get-docker/) та [Docker Compose](https://docs.docker.com/compose/install/)
- Або: Python 3.12+, Node.js 20+, PostgreSQL 16, Redis 7

### 1. Клонування

```bash
git clone <repo-url>
cd emotional_support_robot
```

### 2. Налаштування змінних оточення

```bash
cp .env.example .env
# Відредагуйте .env — обов'язково змініть JWT_SECRET_KEY та ENCRYPTION_KEY
```

### 3. Запуск через Docker Compose

```bash
docker compose up --build
```

Це запустить:
- **PostgreSQL** на порті `5432`
- **Redis** на порті `6379`
- **Backend (FastAPI)** на порті `8000`
- **Frontend (Vite)** на порті `5173`

### 4. Міграції бази даних

```bash
docker compose exec backend alembic upgrade head
```

### 5. Відкрити додаток

- **Frontend:** [http://localhost:5173](http://localhost:5173)
- **API Docs:** [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- **ReDoc:** [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc)

---

## 💻 Запуск без Docker

### Backend

```bash
# Встановити залежності
pip install -e .
# або
uv sync

# Запустити PostgreSQL та Redis локально

# Міграції
alembic upgrade head

# Запуск сервера
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Встановити залежності
npm install

# Запуск dev-сервера
npm run dev
```

---

## 📡 API документація

### Основні ендпоінти

| Група | Префікс | Опис |
|---|---|---|
| Health | `GET /api/health` | Перевірка стану сервера |
| Auth | `/api/auth/*` | Реєстрація, логін, refresh, logout |
| Profile | `/api/profile/*` | Профіль, опитування, видалення |
| Chat | `/api/chat/*` | Розмови, повідомлення, WebSocket |
| Emotions | `/api/emotions/*` | Щоденник емоцій (CRUD) |
| Breathing | `/api/breathing-exercises/*` | Дихальні вправи |
| Admin | `/api/admin/*` | Статистика, користувачі, очищення |
| Dependency | `/api/dependency/*` | Детекція залежності від бота |
| Legal | `/api/legal/*` | Політика конфіденційності, умови |

### WebSocket

```
ws://localhost:8000/api/chat/ws/{conversation_id}?token={jwt_token}
```

Повна інтерактивна документація доступна за адресою `/api/docs` (Swagger UI).

---

## ⚙️ Змінні оточення

Див. [`.env.example`](.env.example) для повного списку. Ключові змінні:

| Змінна | Опис | За замовчуванням |
|---|---|---|
| `POSTGRES_PASSWORD` | Пароль PostgreSQL | `postgres` |
| `JWT_SECRET_KEY` | Секрет для JWT токенів | ⚠️ Змініть! |
| `ENCRYPTION_KEY` | Ключ AES-256 шифрування | ⚠️ Змініть! |
| `OPENAI_API_KEY` | Ключ API OpenAI | — |
| `CORS_ORIGINS` | Дозволені джерела CORS | `["http://localhost:5173"]` |
| `RATE_LIMIT_PER_MINUTE` | Ліміт запитів на хвилину | `30` |

---

## 🔒 Безпека

- 🔐 JWT автентифікація з refresh-токенами
- 🔑 bcrypt для хешування паролів
- 🛡️ AES-256 шифрування персональних даних
- 🚫 Rate limiting через Redis
- 📋 Security headers middleware
- 🧹 Автоматичне очищення застарілих даних
- 📝 Sanitized логування (без персональних даних у логах)

---
