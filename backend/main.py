import asyncio
import logging
import os
import socket
from contextlib import asynccontextmanager

import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.core.scheduler import create_scheduler
from backend.routers import chat, history, market, news, ws
from backend.routers import settings as settings_router
from backend.services.chat_service import ChatService
from backend.services.market_service import MarketDataService
from backend.services.news_service import NewsService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _initial_fetch(market_service: MarketDataService, news_service: NewsService):
    logger.info("Fetching initial market data in background...")
    await market_service.refresh_all()
    logger.info("Fetching initial news in background...")
    await news_service.refresh()
    logger.info("Initial data fetch complete")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    market_service = MarketDataService(settings)
    news_service = NewsService()
    chat_service = ChatService(settings, market_service, news_service)

    app.state.market_service = market_service
    app.state.news_service = news_service
    app.state.chat_service = chat_service

    scheduler = create_scheduler(market_service, news_service, settings)
    scheduler.start()
    app.state.scheduler = scheduler
    app.state.settings = settings
    logger.info("Scheduler started")

    asyncio.create_task(_initial_fetch(market_service, news_service))

    yield

    scheduler.shutdown()
    logger.info("Scheduler stopped")


settings = get_settings()

app = FastAPI(
    title="Investment Assistant",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market.router)
app.include_router(news.router)
app.include_router(chat.router)
app.include_router(history.router)
app.include_router(settings_router.router)
app.include_router(ws.router)


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


def _port_is_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) != 0


def run_server() -> None:
    """Run Uvicorn when launched as a PyInstaller sidecar."""
    host = os.getenv("HOST", settings.host)
    port = int(os.getenv("PORT", str(settings.port)))
    if not _port_is_available("127.0.0.1", port):
        logger.error("Port %s is already in use", port)
        return
    uvicorn.run(app, host=host, port=port, log_level="info", log_config=None)


if __name__ == "__main__":
    run_server()
