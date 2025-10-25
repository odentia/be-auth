from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Запрос на вход в систему"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Ответ с токенами"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Запрос на обновление токена"""
    refresh_token: str


class UserResponse(BaseModel):
    """Информация о пользователе"""
    id: str
    email: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AuthResponse(BaseModel):
    """Полный ответ аутентификации"""
    user: UserResponse
    tokens: TokenResponse


class ErrorResponse(BaseModel):
    """Стандартный ответ с ошибкой"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
