import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "unhealthy"]
    assert "timestamp" in data
    assert "database" in data
    assert "connected" in data["database"]
    assert "latency_ms" in data["database"]


@pytest.mark.asyncio
async def test_dependencies_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/health/dependencies")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "checks" in data
    assert "database" in data["checks"]
    assert "cache" in data["checks"]
    assert "coingecko" in data["checks"]
    assert "alphavantage" in data["checks"]

    for check_name in ["database", "cache", "coingecko", "alphavantage"]:
        check = data["checks"][check_name]
        assert "status" in check
        assert check["status"] in ["healthy", "unhealthy"]


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "docs" in data
