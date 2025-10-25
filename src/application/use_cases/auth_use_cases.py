from __future__ import annotations

from typing import Optional

from src.application.dto import LoginRequest, AuthResponse, UserResponse, TokenResponse
from src.domain.entities import User
from src.domain.repositories import UserRepository
from src.domain.services import AuthService, JWTService


class LoginUseCase:
    """Use case для входа в систему"""
    
    def __init__(
        self,
        user_repo: UserRepository,
        auth_service: AuthService,
        jwt_service: JWTService
    ):
        self.user_repo = user_repo
        self.auth_service = auth_service
        self.jwt_service = jwt_service
    
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
        jwt_service: JWTService
    ):
        self.user_repo = user_repo
        self.jwt_service = jwt_service
    
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
