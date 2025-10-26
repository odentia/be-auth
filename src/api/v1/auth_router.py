from fastapi import APIRouter, HTTPException, status, Response, Depends, Request

from src.application.dto import (
    LoginRequest, AuthResponse, TokenResponse, RefreshTokenRequest, UserResponse, RegisterRequest
)
from src.application.use_cases.auth_use_cases import (
    LoginUseCase, RefreshTokenUseCase
)
from src.api.deps import get_user_repo, get_auth_services, get_jwt_service
from src.application.use_cases.register_use_cases import RegisterUseCase

# Создаем роутер для аутентификации
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    response: Response,
    user_repo=Depends(get_user_repo),
    auth_services=Depends(get_auth_services)
):
    """Вход в систему"""
    login_use_case = LoginUseCase(
        user_repo=user_repo,
        auth_service=auth_services["auth_service"],
        jwt_service=auth_services["jwt_service"]
    )
    
    result = await login_use_case.execute(request)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Устанавливаем HTTP-only куки
    _set_auth_cookies(response, result.tokens)
    
    return result


@auth_router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    request: Request,
    response: Response,
    user_repo=Depends(get_user_repo),
    auth_services=Depends(get_auth_services)
):
    """Обновление токенов"""
    # Пытаемся получить refresh токен из кук или из тела запроса
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        # Если нет в куках, пытаемся получить из тела запроса
        try:
            body = await request.json()
            refresh_token = body.get("refresh_token")
        except:
            pass
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required"
        )
    
    refresh_use_case = RefreshTokenUseCase(
        user_repo=user_repo,
        jwt_service=auth_services["jwt_service"]
    )
    
    result = await refresh_use_case.execute(refresh_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Устанавливаем HTTP-only куки
    _set_auth_cookies(response, result.tokens)
    
    return result


@auth_router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    response: Response,
    user_repo=Depends(get_user_repo),
    auth_services=Depends(get_auth_services)
):
    register_use_case = RegisterUseCase(
        user_repo=user_repo,
        auth_service=auth_services["auth_service"],
        jwt_service=auth_services["jwt_service"]
    )

    result = await register_use_case.execute(request)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    _set_auth_cookies(response, result.tokens)

    return result


@auth_router.get("/me", response_model=UserResponse)
async def get_current_user(
    request: Request,
    user_repo=Depends(get_user_repo),
    jwt_service=Depends(get_jwt_service)
):
    access_token = request.cookies.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        payload = jwt_service.verify_access_token(access_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )

        return UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed"
        )


@auth_router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    user_repo=Depends(get_user_repo),
    jwt_service=Depends(get_jwt_service)
):
    try:
        access_token = request.cookies.get("access_token")
        if access_token:
            payload = jwt_service.verify_access_token(access_token)
            if payload:
                user_id = payload.get("sub")
                print(f"User {user_id} is logging out")
    except:
        pass

    _clear_auth_cookies(response)

    return {
        "success": True,
        "message": "Successfully logged out"
    }


def _clear_auth_cookies(response: Response):
    response.delete_cookie(
        "access_token",
        path="/",
        secure=True,
        httponly=True,
        samesite="lax"
    )
    response.delete_cookie(
        "refresh_token",
        path="/",
        secure=True,
        httponly=True,
        samesite="lax"
    )


def _set_auth_cookies(response: Response, tokens: TokenResponse):
    """Установка HTTP-only кук для токенов"""
    # Access token cookie
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        max_age=tokens.expires_in,
        httponly=True,
        secure=True,  # Только для HTTPS в продакшене
        samesite="lax"
    )
    
    # Refresh token cookie (более длительный срок)
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        max_age=7 * 24 * 60 * 60,  # 7 дней
        httponly=True,
        secure=True,  # Только для HTTPS в продакшене
        samesite="lax"
    )
