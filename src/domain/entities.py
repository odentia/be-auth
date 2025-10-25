from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """Пользователь для аутентификации"""
    id: str
    email: str
    name: str
    password_hash: str
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class TokenPair:
    """Пара токенов (access + refresh)"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 минут


@dataclass
class AuthResult:
    """Результат аутентификации"""
    user: User
    tokens: TokenPair
    success: bool = True
    message: Optional[str] = None
