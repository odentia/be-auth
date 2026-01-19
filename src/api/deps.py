from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.config import Settings
from src.core.logging import get_logger

from src.application.uow import UnitOfWork  # interface / Protocol
from src.infrastructure.uow_sqlalchemy import SQLAlchemyUoW  # impl
from src.domain.services import PasswordService, JWTService, AuthService
from src.infrastructure.persistence.repositories import SQLUserRepository
from src.infrastructure.mq.publisher import EventPublisher

log = get_logger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)

def get_settings(request: Request) -> Settings:

    settings: Settings = request.app.state.settings
    return settings


def _get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:

    sf: async_sessionmaker[AsyncSession] | None = getattr(request.app.state, "session_factory", None)
    if sf is None:

        from src.core.db import get_session_factory as _fallback_get_sf

        sf = _fallback_get_sf()
    if sf is None:
        raise RuntimeError("Session factory is not initialized. Check lifespan startup.")
    return sf

async def get_session(request: Request) -> AsyncIterator[AsyncSession]:

    session_factory = _get_session_factory(request)
    async with session_factory() as session:
        yield session

def get_uow(request: Request) -> UnitOfWork:

    session_factory = _get_session_factory(request)
    return SQLAlchemyUoW(session_factory)

@asynccontextmanager
async def request_scoped_uow(session: AsyncSession) -> AsyncIterator[UnitOfWork]:

    uow = SQLAlchemyUoW.from_existing_session(session)
    try:
        yield uow
        await uow.commit()
    finally:
        await uow.close()


async def get_uow_scoped(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncIterator[UnitOfWork]:
    async with request_scoped_uow(session) as uow:
        yield uow

async def get_current_token(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:

    return "" if creds is None else creds.credentials


def get_password_service(settings: Settings = Depends(get_settings)) -> PasswordService:
    """Получить сервис для работы с паролями"""
    return PasswordService()


def get_jwt_service(settings: Settings = Depends(get_settings)) -> JWTService:
    """Получить сервис для работы с JWT"""
    return JWTService(settings)


def get_auth_service(
    password_service: PasswordService = Depends(get_password_service),
    jwt_service: JWTService = Depends(get_jwt_service)
) -> AuthService:
    """Получить сервис аутентификации"""
    return AuthService(password_service, jwt_service)


def get_auth_services(
    password_service: PasswordService = Depends(get_password_service),
    jwt_service: JWTService = Depends(get_jwt_service),
    auth_service: AuthService = Depends(get_auth_service)
) -> dict:
    """Получить все сервисы аутентификации"""
    return {
        "password_service": password_service,
        "jwt_service": jwt_service,
        "auth_service": auth_service
    }


def get_user_repo(session: SessionDep) -> SQLUserRepository:
    """Получить репозиторий пользователей"""
    return SQLUserRepository(session)


def get_event_publisher(request: Request) -> EventPublisher | None:
    """Получить EventPublisher из app state"""
    publisher: EventPublisher | None = getattr(request.app.state, "event_publisher", None)
    return publisher


async def require_authenticated_user(
    token: Annotated[str, Depends(get_current_token)],
    settings: SettingsDep,
) -> dict:
    """Проверка аутентификации пользователя"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверяем JWT токен
    jwt_service = JWTService(settings)
    payload = jwt_service.verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "sub": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role"),
        "roles": [payload.get("role", "user")]
    }


SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]
UoWDep = Annotated[UnitOfWork, Depends(get_uow)]
CurrentUserDep = Annotated[dict, Depends(require_authenticated_user)]
