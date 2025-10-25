from __future__ import annotations

from src.domain.entities import User
from src.infrastructure.persistence.models import Users


def user_to_domain(user_model: Users) -> User:
    """Преобразование модели БД в доменную сущность"""
    return User(
        id=user_model.id,
        email=user_model.email,
        name=user_model.name,
        password_hash=user_model.password_hash,
        is_active=user_model.is_active,
        created_at=user_model.created_at,
        updated_at=user_model.updated_at
    )


def user_to_model(user: User) -> Users:
    """Преобразование доменной сущности в модель БД"""
    return Users(
        id=user.id,
        email=user.email,
        name=user.name,
        password_hash=user.password_hash,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )
