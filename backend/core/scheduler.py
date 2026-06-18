import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.config import Settings
from backend.services.market_service import MarketDataService, _any_market_open
from backend.services.news_service import NewsService

logger = logging.getLogger(__name__)


async def _market_refresh_wrapper(market_service: MarketDataService):
    if not _any_market_open():
        logger.info("所有市场已收盘，跳过本次数据刷新")
        return
    logger.debug("市场部分开放，开始数据刷新")
    await market_service.refresh_all()


def create_scheduler(
    market_service: MarketDataService,
    news_service: NewsService,
    settings: Settings,
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _market_refresh_wrapper,
        "interval",
        seconds=settings.market_refresh_interval,
        args=[market_service],
        id="market_refresh",
    )
    scheduler.add_job(
        news_service.refresh,
        "interval",
        seconds=settings.news_refresh_interval,
        id="news_refresh",
    )
    return scheduler
