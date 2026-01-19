from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field



class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


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


class LogautResponse(BaseModel):
    success: bool = True
    message: str = "Successful logout"


# --- Event DTOs ---

class UserCreatedEvent(BaseModel):
    """Событие создания пользователя"""
    event_type: str = "user_created"
    user_id: str
    email: str
    name: str
    created_at: datetime


class UserLoggedInEvent(BaseModel):
    """Событие входа пользователя"""
    event_type: str = "user_logged_in"
    user_id: str
    email: str
    timestamp: datetime


class UserLoggedOutEvent(BaseModel):
    """Событие выхода пользователя"""
    event_type: str = "user_logged_out"
    user_id: str
    email: str
    timestamp: datetime


class TokenRefreshedEvent(BaseModel):
    """Событие обновления токена"""
    event_type: str = "token_refreshed"
    user_id: str
    email: str
    timestamp: datetime
