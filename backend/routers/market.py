from fastapi import APIRouter, Request

from backend.models.market import IndexData

router = APIRouter(prefix="/api/v1/market", tags=["market"])


@router.get("/indices")
async def get_all_indices(request: Request) -> dict[str, list[IndexData]]:
    service = request.app.state.market_service
    return service.get_cached()


@router.get("/kline/{symbol}")
async def get_kline(
    symbol: str,
    request: Request,
    period: str = "day",
) -> dict:
    service = request.app.state.market_service
    return service.get_kline(symbol, period)
