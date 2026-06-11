from datetime import datetime

from pydantic import BaseModel, Field


class IndexData(BaseModel):
    symbol: str
    name: str
    region: str
    price: float
    change: float
    change_percent: float
    sparkline: list[float] = []
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    unit: str = ""
    alt_price: float | None = None
    alt_unit: str = ""


class MarketSummary(BaseModel):
    overall_sentiment: str
    top_gainer: IndexData | None = None
    top_loser: IndexData | None = None
    indices_by_region: dict[str, list[IndexData]] = {}
    updated_at: datetime = Field(default_factory=datetime.utcnow)
