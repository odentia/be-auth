# Архитектура сервиса аутентификации

## Обзор

Сервис аутентификации построен по принципам Clean Architecture и следует микросервисной архитектуре. Основная ответственность - генерация и валидация JWT токенов, аутентификация пользователей.

## Архитектурные слои

### 1. Domain Layer (Доменный слой)
**Расположение**: `src/domain/`

**Ответственность**: Содержит бизнес-логику и бизнес-правила приложения.

**Компоненты**:
- `entities.py` - Доменные сущности (User, TokenPair, RefreshToken, AuthResult)
- `repositories.py` - Интерфейсы репозиториев (UserRepository, RefreshTokenRepository)
- `services.py` - Доменные сервисы (PasswordService, JWTService, AuthService)
- `value_objects.py` - Объекты-значения (UserRole)

**Принципы**:
- Не зависит от внешних слоев
- Содержит только бизнес-логику
- Использует интерфейсы для зависимостей

### 2. Application Layer (Слой приложения)
**Расположение**: `src/application/`

**Ответственность**: Координирует выполнение use cases и управляет потоком данных.

**Компоненты**:
- `dto.py` - Data Transfer Objects для HTTP API
- `use_cases/` - Use cases (LoginUseCase, RegisterUseCase, RefreshTokenUseCase)
- `uow.py` - Unit of Work для управления транзакциями

**Принципы**:
- Зависит только от Domain layer
- Содержит use cases и DTO
- Не содержит бизнес-логику

### 3. Infrastructure Layer (Инфраструктурный слой)
**Расположение**: `src/infrastructure/`

**Ответственность**: Реализует интерфейсы из Domain layer и взаимодействует с внешними системами.

**Компоненты**:
- `persistence/` - Работа с базой данных
  - `models.py` - SQLAlchemy модели
  - `repositories.py` - Реализация репозиториев
  - `mappers.py` - Преобразование между доменными сущностями и моделями БД
- `clients/` - HTTP клиенты для других сервисов
- `mq/` - Работа с message queue

**Принципы**:
- Реализует интерфейсы из Domain layer
- Содержит техническую логику
- Может зависеть от внешних библиотек

### 4. API Layer (Слой API)
**Расположение**: `src/api/`

**Ответственность**: HTTP endpoints, middleware, dependency injection.

**Компоненты**:
- `app.py` - Создание FastAPI приложения
- `v1/` - API версии 1
  - `routers.py` - Основной роутер
  - `auth_router.py` - Роутер аутентификации
- `middleware.py` - Middleware для аутентификации
- `deps.py` - Dependency injection
- `lifespan.py` - Управление жизненным циклом приложения

**Принципы**:
- Тонкий слой для HTTP
- Зависит от Application layer
- Содержит только HTTP-специфичную логику

## Поток аутентификации

### 1. Регистрация пользователя
```
Client → POST /api/v1/auth/register
       → RegisterUseCase
       → PasswordService.hash_password()
       → UserRepository.create()
       → JWTService.create_token_pair()
       → RefreshTokenRepository.create()
       → HTTP-only cookies
```

### 2. Вход в систему
```
Client → POST /api/v1/auth/login
       → LoginUseCase
       → UserRepository.get_by_email()
       → AuthService.authenticate_user()
       → JWTService.create_token_pair()
       → HTTP-only cookies
```

### 3. Обновление токенов
```
Client → POST /api/v1/auth/refresh
       → RefreshTokenUseCase
       → JWTService.verify_refresh_token()
       → RefreshTokenRepository.get_by_hash()
       → JWTService.create_token_pair()
       → HTTP-only cookies
```

### 4. Проверка аутентификации
```
Request → AuthMiddleware
        → JWTService.verify_access_token()
        → Request.state (user info)
        → Protected endpoint
```

## Безопасность

### 1. Хеширование паролей
- Используется bcrypt с автоматической генерацией соли
- Пароли никогда не хранятся в открытом виде

### 2. JWT токены
- Access токены: короткий срок жизни (30 минут)
- Refresh токены: длительный срок жизни (7 дней)
- Подпись: HMAC SHA-256
- Ротация refresh токенов при каждом обновлении

### 3. HTTP-only куки
- Защита от XSS атак
- Автоматическая отправка с каждым запросом
- Secure флаг для HTTPS

### 4. Валидация данных
- Pydantic схемы для валидации входных данных
- Проверка email формата
- Ограничения на длину пароля

## База данных

### Таблицы

#### users
- `id` (UUID, PK) - Уникальный идентификатор
- `email` (VARCHAR, UNIQUE) - Email пользователя
- `name` (VARCHAR) - Имя пользователя
- `password_hash` (VARCHAR) - Хеш пароля
- `role` (VARCHAR) - Роль пользователя
- `is_active` (BOOLEAN) - Активность пользователя
- `created_at` (TIMESTAMP) - Дата создания
- `updated_at` (TIMESTAMP) - Дата обновления

#### refreshtokens
- `id` (UUID, PK) - Уникальный идентификатор
- `user_id` (VARCHAR, FK) - ID пользователя
- `token_hash` (VARCHAR, UNIQUE) - Хеш refresh токена
- `expires_at` (TIMESTAMP) - Дата истечения
- `is_revoked` (BOOLEAN) - Отозван ли токен
- `created_at` (TIMESTAMP) - Дата создания

## Конфигурация

### Переменные окружения

#### База данных
- `DATABASE_URL` - URL для SQLAlchemy (async)
- `ALEMBIC_DATABASE_URL` - URL для Alembic (sync)

#### Redis
- `REDIS_URL` - URL для подключения к Redis

#### JWT
- `JWT_SECRET_KEY` - Секретный ключ для подписи
- `JWT_ALGORITHM` - Алгоритм подписи (HS256)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` - Время жизни access токена
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS` - Время жизни refresh токена

#### Приложение
- `APP_NAME` - Название приложения
- `ENV` - Окружение (dev/test/prod)
- `CORS_ALLOW_ORIGINS` - Разрешенные CORS origins

## Тестирование

### Unit тесты
- Тестирование доменных сервисов
- Тестирование use cases
- Мокирование репозиториев

### Integration тесты
- Тестирование API endpoints
- Тестирование с реальной БД
- Тестирование middleware

### E2E тесты
- Полный цикл аутентификации
- Тестирование с фронтендом

## Мониторинг и логирование

### Логирование
- Структурированные JSON логи
- Корреляция запросов через request_id
- Уровни логирования (DEBUG, INFO, WARNING, ERROR)

### Метрики
- Количество аутентификаций
- Время ответа API
- Ошибки аутентификации

### Health checks
- `/api/v1/healthz` - Проверка здоровья сервиса
- Проверка подключения к БД
- Проверка подключения к Redis

## Развертывание

### Docker
- Многоэтапная сборка
- Минимальный образ на основе Alpine
- Переменные окружения через .env

### Миграции
- Alembic для управления схемой БД
- Автоматическое применение миграций при запуске
- Откат миграций при необходимости

### Масштабирование
- Горизонтальное масштабирование через load balancer
- Stateless архитектура
- Внешнее хранение сессий в Redis
