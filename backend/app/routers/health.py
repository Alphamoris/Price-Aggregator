from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.schemas.health import (
    DatabaseStatus,
    DependenciesResponse,
    DependencyCheckResult,
    DependencyChecks,
    HealthResponse,
)
from app.services.crypto_service import CryptoService
from app.services.stock_service import StockService

settings = get_settings()
router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    db_connected = False
    db_latency = 0.0

    try:
        start = datetime.now(UTC)
        await db.execute(text("SELECT 1"))
        db_latency = (datetime.now(UTC) - start).total_seconds() * 1000
        db_connected = True
    except Exception:
        pass

    overall_status = "healthy" if db_connected else "unhealthy"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(UTC),
        version=settings.app_version,
        database=DatabaseStatus(
            connected=db_connected,
            latency_ms=round(db_latency, 2)
        )
    )


@router.get("/dependencies", response_model=DependenciesResponse)
async def dependency_check(db: AsyncSession = Depends(get_db)) -> DependenciesResponse:
    db_check = DependencyCheckResult(status="unhealthy", latency_ms=None, error=None)
    coingecko_check = DependencyCheckResult(status="unhealthy", latency_ms=None, error=None)
    alphavantage_check = DependencyCheckResult(status="unhealthy", latency_ms=None, error=None)
    cache_check = DependencyCheckResult(status="healthy", latency_ms=None, error=None)

    try:
        start = datetime.now(UTC)
        await db.execute(text("SELECT 1"))
        latency = (datetime.now(UTC) - start).total_seconds() * 1000
        db_check = DependencyCheckResult(status="healthy", latency_ms=round(latency, 2), error=None)
    except Exception as e:
        db_check = DependencyCheckResult(status="unhealthy", latency_ms=None, error=str(e))

    crypto_service = CryptoService()
    try:
        start = datetime.now(UTC)
        if await crypto_service.health_check():
            latency = (datetime.now(UTC) - start).total_seconds() * 1000
            coingecko_check = DependencyCheckResult(status="healthy", latency_ms=round(latency, 2), error=None)
        else:
            coingecko_check = DependencyCheckResult(status="unhealthy", latency_ms=None, error="Health check failed")
    except Exception as e:
        coingecko_check = DependencyCheckResult(status="unhealthy", latency_ms=None, error=str(e))

    stock_service = StockService()
    try:
        start = datetime.now(UTC)
        if await stock_service.health_check():
            latency = (datetime.now(UTC) - start).total_seconds() * 1000
            alphavantage_check = DependencyCheckResult(status="healthy", latency_ms=round(latency, 2), error=None)
        else:
            alphavantage_check = DependencyCheckResult(status="unhealthy", latency_ms=None, error="Health check failed")
    except Exception as e:
        alphavantage_check = DependencyCheckResult(status="unhealthy", latency_ms=None, error=str(e))

    checks = DependencyChecks(
        database=db_check,
        coingecko=coingecko_check,
        alphavantage=alphavantage_check,
        cache=cache_check
    )

    all_healthy = all(
        check.status == "healthy"
        for check in [db_check, coingecko_check, alphavantage_check, cache_check]
    )

    some_healthy = any(
        check.status == "healthy"
        for check in [db_check, coingecko_check, alphavantage_check, cache_check]
    )

    if all_healthy:
        overall_status = "healthy"
    elif some_healthy:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return DependenciesResponse(
        status=overall_status,
        timestamp=datetime.now(UTC),
        checks=checks
    )

