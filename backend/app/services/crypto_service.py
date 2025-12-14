import httpx
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from app.config import get_settings
from app.utils.logging import get_logger
from app.utils.exceptions import ExternalAPIError, RateLimitError
from app.models.asset import AssetType, DataSource

settings = get_settings()
logger = get_logger(__name__)


class CryptoService:
    def __init__(self):
        self.base_url = settings.coingecko_base_url
        self.max_retries = 3
        self.base_delay = 1
        self._circuit_open = False
        self._circuit_failures = 0
        self._circuit_threshold = 5
        self._circuit_reset_time: datetime | None = None

    async def _make_request(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if self._circuit_open:
            if self._circuit_reset_time and datetime.now(timezone.utc) > self._circuit_reset_time:
                self._circuit_open = False
                self._circuit_failures = 0
                logger.info("circuit_breaker_reset", service="coingecko")
            else:
                raise ExternalAPIError(
                    message="Circuit breaker open",
                    source="coingecko",
                    details={"reset_time": self._circuit_reset_time.isoformat() if self._circuit_reset_time else None}
                )

        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, params=params)
                    
                    if response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        raise RateLimitError(
                            message="CoinGecko rate limit exceeded",
                            retry_after=retry_after
                        )
                    
                    response.raise_for_status()
                    self._circuit_failures = 0
                    return response.json()
                    
            except httpx.HTTPStatusError as e:
                logger.warning(
                    "coingecko_request_failed",
                    attempt=attempt + 1,
                    status_code=e.response.status_code,
                    url=url
                )
                if attempt == self.max_retries - 1:
                    self._handle_failure()
                    raise ExternalAPIError(
                        message=f"CoinGecko API error: {e.response.status_code}",
                        source="coingecko"
                    )
                    
            except httpx.RequestError as e:
                logger.warning(
                    "coingecko_connection_error",
                    attempt=attempt + 1,
                    error=str(e),
                    url=url
                )
                if attempt == self.max_retries - 1:
                    self._handle_failure()
                    raise ExternalAPIError(
                        message=f"CoinGecko connection error: {str(e)}",
                        source="coingecko"
                    )
            
            delay = self.base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
        
        raise ExternalAPIError(message="Max retries exceeded", source="coingecko")

    def _handle_failure(self) -> None:
        self._circuit_failures += 1
        if self._circuit_failures >= self._circuit_threshold:
            self._circuit_open = True
            self._circuit_reset_time = datetime.now(timezone.utc).replace(
                minute=datetime.now(timezone.utc).minute + 5
            )
            logger.warning(
                "circuit_breaker_opened",
                service="coingecko",
                failures=self._circuit_failures
            )

    async def fetch_top_cryptos(self, limit: int = 50) -> list[dict[str, Any]]:
        logger.info("fetching_crypto_data", limit=limit)
        
        data = await self._make_request(
            "coins/markets",
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": limit,
                "page": 1,
                "sparkline": "false",
                "price_change_percentage": "24h"
            }
        )
        
        assets = []
        fetched_at = datetime.now(timezone.utc)
        
        for coin in data:
            assets.append({
                "symbol": coin.get("symbol", "").upper(),
                "name": coin.get("name", ""),
                "asset_type": AssetType.CRYPTO,
                "price_usd": Decimal(str(coin.get("current_price", 0))) if coin.get("current_price") else None,
                "change_24h": Decimal(str(coin.get("price_change_percentage_24h", 0))) if coin.get("price_change_percentage_24h") else None,
                "market_cap": Decimal(str(coin.get("market_cap", 0))) if coin.get("market_cap") else None,
                "volume_24h": Decimal(str(coin.get("total_volume", 0))) if coin.get("total_volume") else None,
                "source": DataSource.COINGECKO,
                "fetched_at": fetched_at,
            })
        
        logger.info("crypto_data_fetched", count=len(assets))
        return assets

    async def health_check(self) -> bool:
        try:
            await self._make_request("ping")
            return True
        except Exception:
            return False
