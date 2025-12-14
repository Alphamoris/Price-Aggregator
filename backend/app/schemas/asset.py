from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.asset import AssetType, DataSource


class AssetBase(BaseModel):
    symbol: str
    name: str
    asset_type: AssetType
    price_usd: Decimal | None = None
    change_24h: Decimal | None = None
    market_cap: Decimal | None = None
    volume_24h: Decimal | None = None
    source: DataSource


class AssetCreate(AssetBase):
    fetched_at: datetime


class AssetResponse(AssetBase):
    id: int
    fetched_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssetListResponse(BaseModel):
    items: list[AssetResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AssetRefreshResponse(BaseModel):
    crypto_count: int
    stock_count: int
    crypto_success: bool
    stock_success: bool
    message: str


class AssetFilter(BaseModel):
    asset_type: AssetType | None = None
    source: DataSource | None = None
    symbol: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
