from fastapi import APIRouter

from src.api.v1.auth_router import auth_router

api_v1 = APIRouter(prefix="/v1", tags=["v1"])

# Включаем роутер аутентификации
api_v1.include_router(auth_router)

@api_v1.get("/healthz")
async def healthz():
    return {"status": "ok"}