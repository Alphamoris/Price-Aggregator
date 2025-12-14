from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from typing import Any
from app.models.asset import Asset, AssetType, DataSource
from app.schemas.asset import AssetFilter, AssetCreate
from app.services.cache import asset_cache
from app.services.crypto_service import CryptoService
from app.services.stock_service import StockService
from app.utils.logging import get_logger
from app.utils.exceptions import NotFoundError
from app.config import get_settings

settings = get_settings()
logger = get_logger(__name__)


class AssetService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crypto_service = CryptoService()
        self.stock_service = StockService()

    async def get_assets(self, filters: AssetFilter) -> tuple[list[Asset], int]:
        cache_key = f"assets:{filters.asset_type}:{filters.source}:{filters.symbol}:{filters.page}:{filters.page_size}"
        
        cached = asset_cache.get(cache_key)
        if cached:
            return cached["items"], cached["total"]

        query = select(Asset)
        count_query = select(func.count(Asset.id))
        
        if filters.asset_type:
            query = query.where(Asset.asset_type == filters.asset_type)
            count_query = count_query.where(Asset.asset_type == filters.asset_type)
        
        if filters.source:
            query = query.where(Asset.source == filters.source)
            count_query = count_query.where(Asset.source == filters.source)
        
        if filters.symbol:
            query = query.where(Asset.symbol.ilike(f"%{filters.symbol}%"))
            count_query = count_query.where(Asset.symbol.ilike(f"%{filters.symbol}%"))
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        offset = (filters.page - 1) * filters.page_size
        query = query.order_by(Asset.market_cap.desc().nullslast()).offset(offset).limit(filters.page_size)
        
        result = await self.db.execute(query)
        assets = list(result.scalars().all())
        
        asset_cache.set(cache_key, {"items": assets, "total": total})
        
        return assets, total

    async def get_asset_by_symbol(self, symbol: str) -> Asset:
        cache_key = f"asset:symbol:{symbol.upper()}"
        
        cached = asset_cache.get(cache_key)
        if cached:
            return cached
        
        query = select(Asset).where(Asset.symbol == symbol.upper())
        result = await self.db.execute(query)
        asset = result.scalar_one_or_none()
        
        if not asset:
            raise NotFoundError(message=f"Asset with symbol {symbol} not found")
        
        asset_cache.set(cache_key, asset)
        return asset

    async def get_cryptos(self, page: int = 1, page_size: int = 20) -> tuple[list[Asset], int]:
        filters = AssetFilter(asset_type=AssetType.CRYPTO, page=page, page_size=page_size)
        return await self.get_assets(filters)

    async def get_stocks(self, page: int = 1, page_size: int = 20) -> tuple[list[Asset], int]:
        filters = AssetFilter(asset_type=AssetType.STOCK, page=page, page_size=page_size)
        return await self.get_assets(filters)

    async def refresh_all_data(self) -> dict[str, Any]:
        logger.info("data_refresh_started")
        
        results = {
            "crypto_count": 0,
            "stock_count": 0,
            "crypto_success": False,
            "stock_success": False,
        }
        
        try:
            crypto_data = await self.crypto_service.fetch_top_cryptos(limit=50)
            await self._upsert_assets(crypto_data)
            results["crypto_count"] = len(crypto_data)
            results["crypto_success"] = True
            logger.info("crypto_refresh_complete", count=len(crypto_data))
        except Exception as e:
            logger.error("crypto_refresh_failed", error=str(e))
        
        try:
            stock_data = await self.stock_service.fetch_stocks()
            await self._upsert_assets(stock_data)
            results["stock_count"] = len(stock_data)
            results["stock_success"] = True
            logger.info("stock_refresh_complete", count=len(stock_data))
        except Exception as e:
            logger.error("stock_refresh_failed", error=str(e))
        
        asset_cache.clear()
        
        logger.info(
            "data_refresh_complete",
            crypto_count=results["crypto_count"],
            stock_count=results["stock_count"],
            crypto_success=results["crypto_success"],
            stock_success=results["stock_success"]
        )
        
        return results

    async def _upsert_assets(self, assets_data: list[dict[str, Any]]) -> None:
        if not assets_data:
            return
        
        for asset_data in assets_data:
            query = select(Asset).where(
                Asset.symbol == asset_data["symbol"],
                Asset.source == asset_data["source"]
            )
            result = await self.db.execute(query)
            existing = result.scalar_one_or_none()
            
            if existing:
                for key, value in asset_data.items():
                    setattr(existing, key, value)
            else:
                new_asset = Asset(**asset_data)
                self.db.add(new_asset)
        
        await self.db.commit()

    async def get_cache_stats(self) -> dict[str, Any]:
        return asset_cache.stats
