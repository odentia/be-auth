from __future__ import annotations

from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import User
from src.domain.repositories import UserRepository
from src.infrastructure.persistence.models import Users
from src.infrastructure.persistence.mappers import user_to_domain, user_to_model


class SQLUserRepository:
    """SQLAlchemy реализация репозитория пользователей"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Получить пользователя по ID"""
        result = await self.session.execute(
            select(Users).where(Users.id == user_id)
        )
        user_model = result.scalar_one_or_none()
        return user_to_domain(user_model) if user_model else None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        result = await self.session.execute(
            select(Users).where(Users.email == email)
        )
        user_model = result.scalar_one_or_none()
        return user_to_domain(user_model) if user_model else None
    
    async def create(self, user: User) -> User:
        """Создать нового пользователя"""
        user_model = user_to_model(user)
        self.session.add(user_model)
        await self.session.commit()
        await self.session.refresh(user_model)
        return user_to_domain(user_model)
    
    async def update(self, user: User) -> User:
        """Обновить пользователя"""
        user_model = user_to_model(user)
        await self.session.merge(user_model)
        await self.session.commit()
        return user
    
    async def delete(self, user_id: str) -> bool:
        """Удалить пользователя"""
        result = await self.session.execute(
            delete(Users).where(Users.id == user_id)
        )
        await self.session.commit()
        return result.rowcount > 0
