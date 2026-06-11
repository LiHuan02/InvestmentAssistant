from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.config import Settings
from backend.services.market_service import MarketDataService
from backend.services.news_service import NewsService


def create_scheduler(
    market_service: MarketDataService,
    news_service: NewsService,
    settings: Settings,
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        market_service.refresh_all,
        "interval",
        seconds=settings.market_refresh_interval,
        id="market_refresh",
    )
    scheduler.add_job(
        news_service.refresh,
        "interval",
        seconds=settings.news_refresh_interval,
        id="news_refresh",
    )
    return scheduler
