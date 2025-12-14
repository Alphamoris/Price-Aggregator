from sqlalchemy import String, DateTime, Numeric, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from decimal import Decimal
import enum
from app.database import Base


class AssetType(str, enum.Enum):
    CRYPTO = "crypto"
    STOCK = "stock"


class DataSource(str, enum.Enum):
    COINGECKO = "coingecko"
    ALPHAVANTAGE = "alphavantage"


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    asset_type: Mapped[AssetType] = mapped_column(SQLEnum(AssetType), index=True, nullable=False)
    price_usd: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=True)
    change_24h: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=True)
    market_cap: Mapped[Decimal] = mapped_column(Numeric(30, 2), nullable=True)
    volume_24h: Mapped[Decimal] = mapped_column(Numeric(30, 2), nullable=True)
    source: Mapped[DataSource] = mapped_column(SQLEnum(DataSource), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, symbol={self.symbol}, type={self.asset_type})>"
