from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from src.api.lifespan import build_lifespan
from src.api.v1.routers import api_v1
from src.api.middleware import AuthMiddleware
from src.core.config import Settings, load_settings
from src.core.logging import init_logging


def create_app(settings: Settings | None = None) -> FastAPI:

    settings = settings or load_settings()
    init_logging(level=settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.enable_docs else None,
        lifespan=build_lifespan(settings),
    )

    # Middlewares
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Добавляем middleware аутентификации
    app.add_middleware(AuthMiddleware, settings=settings)

    # Routers
    app.include_router(api_v1, prefix="/api")

    # Expose settings for runtime access
    app.state.settings = settings
    return app
