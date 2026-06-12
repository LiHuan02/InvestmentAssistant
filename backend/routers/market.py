from fastapi import APIRouter, Body, Request

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


@router.get("/status")
async def get_market_status(request: Request) -> dict:
    service = request.app.state.market_service
    return service.get_market_status()


@router.get("/settings")
async def get_settings_endpoint(request: Request) -> dict:
    settings = request.app.state.settings
    return {
        "market_refresh_interval": settings.market_refresh_interval,
        "news_refresh_interval": settings.news_refresh_interval,
    }


@router.post("/settings")
async def update_settings_endpoint(request: Request, payload: dict = Body(...)) -> dict:
    settings = request.app.state.settings
    if "market_refresh_interval" in payload:
        val = int(payload["market_refresh_interval"])
        if 5 <= val <= 3600:
            settings.market_refresh_interval = val
    if "news_refresh_interval" in payload:
        val = int(payload["news_refresh_interval"])
        if 30 <= val <= 86400:
            settings.news_refresh_interval = val
    return {
        "market_refresh_interval": settings.market_refresh_interval,
        "news_refresh_interval": settings.news_refresh_interval,
    }
