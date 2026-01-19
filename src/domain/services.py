from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import Settings
from src.domain.entities import User, TokenPair, AuthResult

if TYPE_CHECKING:
    import redis


class PasswordService:
    """Сервис для работы с паролями"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return self.pwd_context.verify(plain_password, hashed_password)


class JWTService:
    """Сервис для работы с JWT токенами"""
    
    def __init__(self, settings: Settings, redis_client: Optional["redis.Redis"] = None):
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
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def hash_password(self, password: str) -> str:
        return self.get_password_hash(password)