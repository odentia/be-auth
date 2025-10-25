# be-auth

Сервис аутентификации для микросервисной архитектуры.

## Описание

Этот сервис отвечает за:
- Аутентификацию пользователей
- Генерацию и валидацию JWT токенов
- HTTP-only куки для безопасности

## Технологии

- FastAPI - веб-фреймворк
- SQLAlchemy - ORM
- PostgreSQL - база данных
- Alembic - миграции БД
- JWT - токены аутентификации
- bcrypt - хеширование паролей

## Установка и запуск

### 1. Установка зависимостей

```bash
uv sync
```

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/auth_db
ALEMBIC_DATABASE_URL=postgresql://user:password@localhost:5432/auth_db

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
APP_NAME=be-auth
APP_VERSION=0.1.0
ENV=dev
ENABLE_DOCS=true

# HTTP
HTTP_HOST=0.0.0.0
HTTP_PORT=8000
RELOAD=false

# CORS
CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:8080

# Logging
LOG_LEVEL=INFO

# Observability
PUBLIC_BASE_URL=http://localhost:8000
```

### 3. Запуск миграций

```bash
uv run alembic upgrade head
```

### 4. Запуск сервиса

```bash
uv run python -m src.api
```

## API Endpoints

### Аутентификация

- `POST /api/v1/auth/login` - Вход в систему
- `POST /api/v1/auth/refresh` - Обновление токенов

### Системные

- `GET /api/v1/healthz` - Проверка здоровья сервиса

## Архитектура

Сервис построен по принципам Clean Architecture:

- **Domain** - бизнес-логика и сущности
- **Application** - use cases и DTO
- **Infrastructure** - репозитории и внешние сервисы
- **API** - HTTP endpoints и middleware

## Безопасность

- Пароли хешируются с помощью bcrypt
- JWT токены подписываются секретным ключом
- HTTP-only куки для защиты от XSS
- Валидация входных данных

## Разработка

### Структура проекта

```
src/
├── api/                 # HTTP endpoints и middleware
├── application/         # Use cases и DTO
├── core/               # Конфигурация и утилиты
├── domain/             # Бизнес-логика и сущности
└── infrastructure/     # Репозитории и внешние сервисы
```

### Добавление новых функций

1. Создайте доменную сущность в `src/domain/entities.py`
2. Добавьте репозиторий в `src/domain/repositories.py`
3. Реализуйте репозиторий в `src/infrastructure/persistence/repositories.py`
4. Создайте use case в `src/application/use_cases/`
5. Добавьте endpoint в `src/api/v1/`