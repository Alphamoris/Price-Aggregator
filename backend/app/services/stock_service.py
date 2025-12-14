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

TRACKED_STOCKS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]


class StockService:
    def __init__(self):
        self.base_url = settings.alphavantage_base_url
        self.api_key = settings.alphavantage_api_key
        self.max_retries = 3
        self.base_delay = 1
        self._circuit_open = False
        self._circuit_failures = 0
        self._circuit_threshold = 3
        self._circuit_reset_time: datetime | None = None
        self._daily_calls = 0
        self._daily_limit = 25
        self._last_reset_date: datetime | None = None

    def _check_daily_limit(self) -> None:
        now = datetime.now(timezone.utc)
        if self._last_reset_date is None or self._last_reset_date.date() != now.date():
            self._daily_calls = 0
            self._last_reset_date = now
        
        if self._daily_calls >= self._daily_limit:
            raise RateLimitError(
                message="Alpha Vantage daily limit reached",
                details={"daily_calls": self._daily_calls, "limit": self._daily_limit}
            )

    async def _make_request(self, params: dict[str, Any]) -> dict[str, Any]:
        self._check_daily_limit()
        
        if self._circuit_open:
            if self._circuit_reset_time and datetime.now(timezone.utc) > self._circuit_reset_time:
                self._circuit_open = False
                self._circuit_failures = 0
                logger.info("circuit_breaker_reset", service="alphavantage")
            else:
                raise ExternalAPIError(
                    message="Circuit breaker open",
                    source="alphavantage",
                    details={"reset_time": self._circuit_reset_time.isoformat() if self._circuit_reset_time else None}
                )

        params["apikey"] = self.api_key
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(self.base_url, params=params)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    if "Note" in data:
                        raise RateLimitError(
                            message="Alpha Vantage rate limit exceeded",
                            retry_after=60
                        )
                    
                    if "Error Message" in data:
                        raise ExternalAPIError(
                            message=data["Error Message"],
                            source="alphavantage"
                        )
                    
                    self._daily_calls += 1
                    self._circuit_failures = 0
                    return data
                    
            except httpx.HTTPStatusError as e:
                logger.warning(
                    "alphavantage_request_failed",
                    attempt=attempt + 1,
                    status_code=e.response.status_code
                )
                if attempt == self.max_retries - 1:
                    self._handle_failure()
                    raise ExternalAPIError(
                        message=f"Alpha Vantage API error: {e.response.status_code}",
                        source="alphavantage"
                    )
                    
            except httpx.RequestError as e:
                logger.warning(
                    "alphavantage_connection_error",
                    attempt=attempt + 1,
                    error=str(e)
                )
                if attempt == self.max_retries - 1:
                    self._handle_failure()
                    raise ExternalAPIError(
                        message=f"Alpha Vantage connection error: {str(e)}",
                        source="alphavantage"
                    )
            
            delay = self.base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
        
        raise ExternalAPIError(message="Max retries exceeded", source="alphavantage")

    def _handle_failure(self) -> None:
        self._circuit_failures += 1
        if self._circuit_failures >= self._circuit_threshold:
            self._circuit_open = True
            self._circuit_reset_time = datetime.now(timezone.utc).replace(
                hour=datetime.now(timezone.utc).hour + 1
            )
            logger.warning(
                "circuit_breaker_opened",
                service="alphavantage",
                failures=self._circuit_failures
            )

    async def fetch_stock_quote(self, symbol: str) -> dict[str, Any] | None:
        try:
            data = await self._make_request({
                "function": "GLOBAL_QUOTE",
                "symbol": symbol
            })
            
            quote = data.get("Global Quote", {})
            if not quote:
                return None
            
            return {
                "symbol": quote.get("01. symbol", symbol),
                "name": symbol,
                "asset_type": AssetType.STOCK,
                "price_usd": Decimal(quote.get("05. price", "0")) if quote.get("05. price") else None,
                "change_24h": Decimal(quote.get("10. change percent", "0").replace("%", "")) if quote.get("10. change percent") else None,
                "market_cap": None,
                "volume_24h": Decimal(quote.get("06. volume", "0")) if quote.get("06. volume") else None,
                "source": DataSource.ALPHAVANTAGE,
                "fetched_at": datetime.now(timezone.utc),
            }
        except (RateLimitError, ExternalAPIError):
            raise
        except Exception as e:
            logger.error("stock_quote_parse_error", symbol=symbol, error=str(e))
            return None

    async def fetch_stocks(self, symbols: list[str] | None = None) -> list[dict[str, Any]]:
        symbols = symbols or TRACKED_STOCKS
        logger.info("fetching_stock_data", symbols=symbols)
        
        assets = []
        
        for i, symbol in enumerate(symbols):
            try:
                quote = await self.fetch_stock_quote(symbol)
                if quote:
                    assets.append(quote)
                if i < len(symbols) - 1:
                    await asyncio.sleep(12)
            except RateLimitError:
                logger.warning("stock_fetch_rate_limited", symbol=symbol, remaining=symbols[i:])
                break
            except ExternalAPIError as e:
                logger.warning("stock_fetch_failed", symbol=symbol, error=str(e))
                continue
        
        logger.info("stock_data_fetched", count=len(assets))
        return assets

    async def health_check(self) -> bool:
        try:
            await self._make_request({
                "function": "GLOBAL_QUOTE",
                "symbol": "IBM"
            })
            return True
        except Exception:
            return False
