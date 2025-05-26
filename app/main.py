from fastapi import FastAPI
from app.api.errors.http_error import http_error_handler
from app.api.errors.validation_error import http422_error_handler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.api.errors.sentry import init_sentry
from app.core.config import settings


def get_application() -> FastAPI:
    app = FastAPI(
        title="Lu Estilo API",
        description="API for Lu Estilo inventory and order management system.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    init_sentry()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    app.add_event_handler("startup",
        lambda: print("Starting up the application...")                      
    )

    app.add_event_handler("shutdown",
        lambda: print("Shutting down the application...")
    )

    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, http422_error_handler)

    return app

app = get_application()