from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, TypeVar

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T", bound="Base")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):

    @declared_attr.directive
    def __tablename__(cls) -> str:  # noqa: N805
        return cls.__name__.lower()

    def to_dict(self) -> dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def update(self: T, **kwargs) -> T:
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
        return self

    async def save(self: T, session: AsyncSession) -> T:
        session.add(self)
        await session.commit()
        await session.refresh(self)
        return self

    async def delete(self, session: AsyncSession) -> None:
        await session.delete(self)
        await session.commit()

    @classmethod
    async def get_by_id(cls: type[T], session: AsyncSession, id: Any) -> T | None:
        return await session.get(cls, id)

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        return cls(**data)


UUIDStr = Annotated[str, mapped_column(UUID(as_uuid=False), primary_key=True)]


class Users(Base):
    """Таблица пользователей"""
    id: Mapped[UUIDStr]
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
