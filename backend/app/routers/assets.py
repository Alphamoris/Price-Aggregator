from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from math import ceil
from app.database import get_db
from app.models.user import User
from app.models.asset import AssetType, DataSource
from app.schemas.asset import AssetResponse, AssetListResponse, AssetRefreshResponse, AssetFilter
from app.services.asset_service import AssetService
from app.dependencies import get_current_active_user, get_admin_user

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("", response_model=AssetListResponse)
async def list_assets(
    asset_type: AssetType | None = None,
    source: DataSource | None = None,
    symbol: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    filters = AssetFilter(
        asset_type=asset_type,
        source=source,
        symbol=symbol,
        page=page,
        page_size=page_size
    )
    
    asset_service = AssetService(db)
    assets, total = await asset_service.get_assets(filters)
    
    return AssetListResponse(
        items=[AssetResponse.model_validate(a) for a in assets],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 0
    )


@router.get("/crypto", response_model=AssetListResponse)
async def list_crypto_assets(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    asset_service = AssetService(db)
    assets, total = await asset_service.get_cryptos(page=page, page_size=page_size)
    
    return AssetListResponse(
        items=[AssetResponse.model_validate(a) for a in assets],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 0
    )


@router.get("/stocks", response_model=AssetListResponse)
async def list_stock_assets(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    asset_service = AssetService(db)
    assets, total = await asset_service.get_stocks(page=page, page_size=page_size)
    
    return AssetListResponse(
        items=[AssetResponse.model_validate(a) for a in assets],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 0
    )


@router.get("/cache-stats")
async def get_cache_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    asset_service = AssetService(db)
    return await asset_service.get_cache_stats()


@router.post("/refresh", response_model=AssetRefreshResponse)
async def refresh_assets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    asset_service = AssetService(db)
    results = await asset_service.refresh_all_data()
    
    message = "Data refresh completed"
    if not results["crypto_success"] and not results["stock_success"]:
        message = "Data refresh failed for all sources"
    elif not results["crypto_success"]:
        message = "Crypto data refresh failed, stocks updated"
    elif not results["stock_success"]:
        message = "Stock data refresh failed, crypto updated"
    
    return AssetRefreshResponse(
        crypto_count=results["crypto_count"],
        stock_count=results["stock_count"],
        crypto_success=results["crypto_success"],
        stock_success=results["stock_success"],
        message=message
    )


@router.get("/{symbol}", response_model=AssetResponse)
async def get_asset_by_symbol(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    asset_service = AssetService(db)
    asset = await asset_service.get_asset_by_symbol(symbol)
    return AssetResponse.model_validate(asset)
