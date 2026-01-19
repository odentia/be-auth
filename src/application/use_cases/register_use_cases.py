import uuid
from datetime import datetime
from typing import Optional
from src.application.dto import (
    RegisterRequest, AuthResponse, TokenResponse, UserResponse,
    UserCreatedEvent
)
from src.domain.entities import User
from src.domain.repositories import UserRepository
from src.domain.services import AuthService, JWTService
from src.infrastructure.mq.publisher import EventPublisher


class RegisterUseCase:
    def __init__(
            self,
            user_repo: UserRepository,
            auth_service: AuthService,
            jwt_service: JWTService,
            event_publisher: Optional[EventPublisher] = None
    ):
        self.user_repo = user_repo
        self.auth_service = auth_service
        self.jwt_service = jwt_service
        self.event_publisher = event_publisher

    async def execute(self, request: RegisterRequest) -> Optional[AuthResponse]:
        # Проверяем, существует ли пользователь с таким email
        existing_user = await self.user_repo.get_by_email(request.email)
        if existing_user:
            return None

        # Хешируем пароль
        hashed_password = self.auth_service.get_password_hash(request.password)

        # Создаем пользователя
        user = User(
            id=str(uuid.uuid4()),
            email=request.email,
            name=request.name,
            password_hash=hashed_password,
            is_active=True
        )

        # Сохраняем пользователя
        saved_user = await self.user_repo.create(user)

        # Публикуем событие создания пользователя
        if self.event_publisher:
            try:
                event = UserCreatedEvent(
                    user_id=str(saved_user.id),
                    email=saved_user.email,
                    name=saved_user.name,
                    created_at=saved_user.created_at or datetime.utcnow()
                )
                await self.event_publisher.publish(event)
            except Exception as e:
                # Логируем ошибку, но не прерываем процесс регистрации
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to publish user_created event: {e}")

        # Генерируем токены - передаем объект пользователя
        access_token = self.jwt_service.create_access_token(saved_user)
        refresh_token = self.jwt_service.create_refresh_token(saved_user)

        # Создаем ответ
        return AuthResponse(
            user=UserResponse(
                id=str(saved_user.id),
                email=saved_user.email,
                name=saved_user.name,
                is_active=saved_user.is_active,
                created_at=saved_user.created_at,
                updated_at=saved_user.updated_at
            ),
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.jwt_service.access_token_expire_minutes * 60  # в секундах
            )
        )
