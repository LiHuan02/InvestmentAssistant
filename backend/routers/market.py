from fastapi import APIRouter, Request

from backend.models.market import IndexData, MarketSummary
from backend.services.market_service import COMMODITY_UNITS

router = APIRouter(prefix="/api/v1/market", tags=["market"])


@router.get("/indices")
async def get_all_indices(request: Request) -> dict[str, list[IndexData]]:
    service = request.app.state.market_service
    return service.get_cached()


@router.get("/indices/{symbol}")
async def get_index(symbol: str, request: Request) -> IndexData | None:
    service = request.app.state.market_service
    return service.get_index(symbol)


@router.get("/summary")
async def get_market_summary(request: Request) -> MarketSummary:
    service = request.app.state.market_service
    cached = service.get_cached()
    all_indices = [idx for group in cached.values() for idx in group]

    top_gainer = max(all_indices, key=lambda x: x.change_percent) if all_indices else None
    top_loser = min(all_indices, key=lambda x: x.change_percent) if all_indices else None

    gains = sum(1 for idx in all_indices if idx.change > 0)
    total = len(all_indices)
    if total == 0:
        sentiment = "neutral"
    elif gains / total > 0.6:
        sentiment = "bullish"
    elif gains / total < 0.4:
        sentiment = "bearish"
    else:
        sentiment = "mixed"

    return MarketSummary(
        overall_sentiment=sentiment,
        top_gainer=top_gainer,
        top_loser=top_loser,
        indices_by_region=cached,
    )


@router.get("/kline/{symbol}")
async def get_kline(
    symbol: str,
    request: Request,
    period: str = "day",
) -> dict:
    service = request.app.state.market_service
    return service.get_kline(symbol, period)


@router.get("/commodity-units")
async def get_commodity_units() -> dict:
    return COMMODITY_UNITS
