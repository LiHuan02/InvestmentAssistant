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


@router.get("/status")
async def get_market_status(request: Request) -> dict:
    service = request.app.state.market_service
    return service.get_market_status()


@router.get("/settings")
async def get_market_settings(request: Request) -> dict:
    settings = request.app.state.settings
    return {
        "market_refresh_interval": settings.market_refresh_interval,
        "news_refresh_interval": settings.news_refresh_interval,
    }


@router.post("/settings")
async def update_market_settings(request: Request, payload: dict) -> dict:
    settings = request.app.state.settings
    scheduler = request.app.state.scheduler
    updated = {}
    m = payload.get("market_refresh_interval")
    n = payload.get("news_refresh_interval")
    if m is not None:
        settings.market_refresh_interval = int(m)
        try:
            scheduler.reschedule_job("market_refresh", trigger="interval", seconds=settings.market_refresh_interval)
        except Exception:
            pass
        updated["market_refresh_interval"] = settings.market_refresh_interval
    if n is not None:
        settings.news_refresh_interval = int(n)
        try:
            scheduler.reschedule_job("news_refresh", trigger="interval", seconds=settings.news_refresh_interval)
        except Exception:
            pass
        updated["news_refresh_interval"] = settings.news_refresh_interval
    return {"updated": updated}
