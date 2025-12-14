from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DatabaseStatus(BaseModel):
    connected: bool
    latency_ms: float


class HealthResponse(BaseModel):
    status: Literal["healthy", "unhealthy"] 
    timestamp: datetime
    database: DatabaseStatus


class DependencyCheckResult(BaseModel):
    status: Literal["healthy", "unhealthy"] 
    latency_ms: float | None 
    error: str | None


class DependencyChecks(BaseModel):
    database: DependencyCheckResult
    coingecko: DependencyCheckResult
    alphavantage: DependencyCheckResult
    cache: DependencyCheckResult


class DependenciesResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"] 
    timestamp: datetime 
    checks: DependencyChecks
