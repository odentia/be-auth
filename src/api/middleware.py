from __future__ import annotations

from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import Settings
from src.domain.services import JWTService


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware для аутентификации пользователей"""
    
    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings
        self.jwt_service = JWTService(settings)
    
    async def dispatch(self, request: Request, call_next):
        """Обработка запроса с проверкой аутентификации"""
        # Пропускаем публичные эндпоинты
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)
        
        # Пытаемся получить токен из кук или заголовка Authorization
        token = None
        
        # 1. Проверяем куки (приоритет для HTTP-only)
        access_token_cookie = request.cookies.get("access_token")
        if access_token_cookie:
            token = access_token_cookie
        
        # 2. Если нет в куках, проверяем заголовок Authorization
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization"
            )
        
        # Проверяем токен
        payload = self.jwt_service.verify_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Добавляем информацию о пользователе в request state
        request.state.user_id = payload.get("sub")
        request.state.user_email = payload.get("email")
        
        return await call_next(request)
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Проверка, является ли эндпоинт публичным"""
        public_paths = [
            "/api/v1/healthz",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
        return any(path.startswith(public_path) for public_path in public_paths)
