from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status

from src.core.logging import get_logger
log = get_logger(__name__)



@dataclass(slots=True)
class AppError(Exception):

    type: str 
    title: str
    detail: str | None = None
    status_code: int = status.HTTP_400_BAD_REQUEST
    instance: str | None = None
    extra: dict[str, Any] | None = None

    def to_problem(self, request: Request) -> dict[str, Any]:
        problem = {
            "type": f"/problems/{self.type}",
            "title": self.title,
            "status": self.status_code,
            "detail": self.detail,
            "instance": self.instance or str(request.url),
        }
        if self.extra:
            problem.update(self.extra)
        return problem


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:

        log.error(
            f"AppError [{exc.type}] {exc.title}",
            extra={"status_code": exc.status_code, "url": str(request.url), "detail": exc.detail},
            exc_info=True, 
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_problem(request),
            media_type="application/problem+json",
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        log.warning(f"Validation error at {request.url}: {exc}")

        problem = {
            "type": "/problems/validation_error",
            "title": "Validation error",
            "status": status.HTTP_400_BAD_REQUEST,
            "detail": str(exc),
            "instance": str(request.url),
        }

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=problem,
            media_type="application/problem+json",
        )
