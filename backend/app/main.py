import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import close_db, init_db
from app.routers import assets_router, auth_router, health_router
from app.tasks import shutdown_scheduler, start_scheduler
from app.utils.exceptions import AppException
from app.utils.logging import get_logger, setup_logging

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = get_logger(__name__)

    logger.info("application_startup", app_name=settings.app_name, version=settings.app_version)

    await init_db()
    logger.info("database_initialized")

    start_scheduler()

    yield

    logger.info("application_shutdown")
    shutdown_scheduler()
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Asset Aggregator API - Crypto & Stock Market Data",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        path=request.url.path,
        method=request.method
    )

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger = get_logger(__name__)
    logger.warning(
        "app_exception",
        status_code=exc.status_code,
        message=exc.message,
        details=exc.details
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger = get_logger(__name__)
    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "details": {}
        }
    )


app.include_router(auth_router, prefix="/api/v1")
app.include_router(assets_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health"
    }
