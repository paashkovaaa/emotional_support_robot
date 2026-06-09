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
| **React 19** | UI-фреймворк |
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
