from __future__ import annotations

from datetime import datetime
from typing import Optional

from src.application.dto import (
    LoginRequest, AuthResponse, UserResponse, TokenResponse,
    UserLoggedInEvent, TokenRefreshedEvent
)
from src.domain.repositories import UserRepository
from src.domain.services import AuthService, JWTService
from src.infrastructure.mq.publisher import EventPublisher


class LoginUseCase:
    """Use case для входа в систему"""
    
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
    
    async def execute(self, request: LoginRequest) -> Optional[AuthResponse]:
        """Выполнить вход в систему"""
        # Получаем пользователя по email
        user = await self.user_repo.get_by_email(request.email)
        if not user:
            return None
        
        # Проверяем пароль
        if not self.auth_service.authenticate_user(user, request.password):
            return None
        
        # Создаем токены
        auth_result = self.auth_service.create_auth_result(user)
        
        # Публикуем событие входа пользователя
        if self.event_publisher:
            try:
                event = UserLoggedInEvent(
                    user_id=user.id,
                    email=user.email,
                    timestamp=datetime.utcnow()
                )
                await self.event_publisher.publish(event)
            except Exception as e:
                # Логируем ошибку, но не прерываем процесс входа
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to publish user_logged_in event: {e}")
        
        return AuthResponse(
            user=UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            ),
            tokens=TokenResponse(
                access_token=auth_result.tokens.access_token,
                refresh_token=auth_result.tokens.refresh_token,
                token_type=auth_result.tokens.token_type,
                expires_in=auth_result.tokens.expires_in
            )
        )


class RefreshTokenUseCase:
    """Use case для обновления токенов"""
    
    def __init__(
        self,
        user_repo: UserRepository,
        jwt_service: JWTService,
        event_publisher: Optional[EventPublisher] = None
    ):
        self.user_repo = user_repo
        self.jwt_service = jwt_service
        self.event_publisher = event_publisher
    
    async def execute(self, refresh_token: str) -> Optional[AuthResponse]:
        """Обновить токены"""
        # Проверяем JWT токен
        payload = self.jwt_service.verify_refresh_token(refresh_token)
        if not payload:
            return None
        
        # Получаем пользователя
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            return None
        
        # Создаем новые токены
        tokens = self.jwt_service.create_token_pair(user)
        
        # Публикуем событие обновления токена
        if self.event_publisher:
            try:
                event = TokenRefreshedEvent(
                    user_id=user.id,
                    email=user.email,
                    timestamp=datetime.utcnow()
                )
                await self.event_publisher.publish(event)
            except Exception as e:
                # Логируем ошибку, но не прерываем процесс обновления токена
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to publish token_refreshed event: {e}")
        
        return AuthResponse(
            user=UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            ),
            tokens=TokenResponse(
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_type=tokens.token_type,
                expires_in=tokens.expires_in
            )
        )
