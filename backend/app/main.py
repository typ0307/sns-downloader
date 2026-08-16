from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.api.routes import router
from app.config import get_settings
from app.errors import EXTRACT_FAILED, RATE_LIMITED, AppError
from app.limiter import limiter
from app.services.storage import LocalStorage

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.state.limiter = limiter
    app.state.settings = settings
    app.state.storage = LocalStorage(settings.storage_dir)

    allow_credentials = settings.cors_origins != "*"
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": RATE_LIMITED,
                    "message": "Too many requests. Please try again later.",
                }
            },
        )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": EXTRACT_FAILED,
                    "message": "Internal server error.",
                }
            },
        )

    app.include_router(router)
    return app


app = create_app()
