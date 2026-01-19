from __future__ import annotations

from typing import Optional, Protocol
from src.domain.entities import User


class UserRepository(Protocol):
    """Репозиторий для работы с пользователями"""
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Получить пользователя по ID"""
        ...
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        ...
    
    async def create(self, user: User) -> User:
        """Создать нового пользователя"""
        ...
    
    async def update(self, user: User) -> User:
        """Обновить пользователя"""
        ...
    
    async def delete(self, user_id: str) -> bool:
        """Удалить пользователя"""
        ...
