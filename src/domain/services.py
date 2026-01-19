from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import Settings
from src.domain.entities import User, TokenPair, AuthResult


class PasswordService:
    """Сервис для работы с паролями"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def _prepare_password(self, password: str) -> str:
        """Подготовка пароля для bcrypt (ограничение 72 байта)"""
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            # Если пароль длиннее 72 байт, предварительно хешируем его SHA256
            # Используем base64 для компактного представления (44 символа = 44 байта)
            hash_bytes = hashlib.sha256(password_bytes).digest()
            prepared = base64.b64encode(hash_bytes).decode('ascii')
            # Base64 строка из 32 байт всегда будет 44 символа (44 байта), что < 72
            # Но на всякий случай проверяем и обрезаем
            prepared_bytes = prepared.encode('ascii')
            if len(prepared_bytes) > 72:
                return prepared_bytes[:72].decode('ascii', errors='ignore')
            return prepared
        return password
    
    def hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        prepared_password = self._prepare_password(password)
        return self.pwd_context.hash(prepared_password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        prepared_password = self._prepare_password(plain_password)
        return self.pwd_context.verify(prepared_password, hashed_password)


class JWTService:
    """Сервис для работы с JWT токенами"""
    
    def __init__(self, settings: Settings):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days
    
    def create_access_token(self, user: User) -> str:
        """Создание access токена"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode = {
            "sub": user.id,
            "email": user.email,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user: User) -> str:
        """Создание refresh токена"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode = {
            "sub": user.id,
            "exp": expire,
            "type": "refresh"
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_access_token(self, token: str) -> Optional[dict]:
        """Проверка access токена"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != "access":
                return None
            return payload
        except JWTError:
            return None
    
    def verify_refresh_token(self, token: str) -> Optional[dict]:
        """Проверка refresh токена"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != "refresh":
                return None
            return payload
        except JWTError:
            return None
    
    def create_token_pair(self, user: User) -> TokenPair:
        """Создание пары токенов"""
        access_token = self.create_access_token(user)
        refresh_token = self.create_refresh_token(user)
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_expire_minutes * 60
        )


class AuthService:
    """Основной сервис аутентификации"""
    
    def __init__(self, password_service: PasswordService, jwt_service: JWTService):
        self.password_service = password_service
        self.jwt_service = jwt_service
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def _prepare_password(self, password: str) -> str:
        """Подготовка пароля для bcrypt (ограничение 72 байта)"""
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            # Если пароль длиннее 72 байт, предварительно хешируем его SHA256
            # Используем base64 для компактного представления (44 символа = 44 байта)
            hash_bytes = hashlib.sha256(password_bytes).digest()
            prepared = base64.b64encode(hash_bytes).decode('ascii')
            # Base64 строка из 32 байт всегда будет 44 символа (44 байта), что < 72
            # Но на всякий случай проверяем и обрезаем
            prepared_bytes = prepared.encode('ascii')
            if len(prepared_bytes) > 72:
                return prepared_bytes[:72].decode('ascii', errors='ignore')
            return prepared
        return password
    
    def authenticate_user(self, user: User, password: str) -> bool:
        """Аутентификация пользователя по паролю"""
        if not user or not user.is_active:
            return False
        return self.password_service.verify_password(password, user.password_hash)
    
    def create_auth_result(self, user: User) -> AuthResult:
        """Создание результата аутентификации"""
        tokens = self.jwt_service.create_token_pair(user)
        return AuthResult(user=user, tokens=tokens)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        prepared_password = self._prepare_password(plain_password)
        return self.pwd_context.verify(prepared_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Хеширование пароля"""
        prepared_password = self._prepare_password(password)
        return self.pwd_context.hash(prepared_password)

    def hash_password(self, password: str) -> str:
        """Хеширование пароля (алиас)"""
        return self.get_password_hash(password)