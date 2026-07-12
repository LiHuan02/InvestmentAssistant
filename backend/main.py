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


async def _initialize_chat_service(
    app: FastAPI,
    settings,
    market_service: MarketDataService,
    news_service: NewsService,
):
    try:
        # ChatService initializes Chroma/LangChain and can be slow in a frozen
        # executable. Do it after Uvicorn has started serving health checks.
        app.state.chat_service = ChatService(settings, market_service, news_service)
        app.state.ready = True
        logger.info("Backend initialization complete")
        asyncio.create_task(_initial_fetch(market_service, news_service))
    except Exception:
        logger.exception("Backend initialization failed")
        app.state.init_error = "backend initialization failed; see backend.log"
        app.state.ready = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    market_service = MarketDataService(settings)
    news_service = NewsService()

    app.state.market_service = market_service
    app.state.news_service = news_service
    app.state.chat_service = None
    app.state.ready = False
    app.state.init_error = None
    app.state.settings = settings

    scheduler = create_scheduler(market_service, news_service, settings)
    scheduler.start()
    app.state.scheduler = scheduler
    app.state.init_task = asyncio.create_task(
        _initialize_chat_service(app, settings, market_service, news_service)
    )
    logger.info("Backend process started; initializing services in background")

    yield

    app.state.init_task.cancel()
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
    return {
        "status": "ok",
        "version": "0.1.0",
        "ready": getattr(app.state, "ready", False),
        "error": getattr(app.state, "init_error", None),
    }


def _port_is_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) != 0


def run_server() -> None:
    """Run Uvicorn when launched as a PyInstaller sidecar."""
    host = os.getenv("HOST", settings.host)
    port = int(os.getenv("PORT", str(settings.port)))
    logger.info("Starting Uvicorn on %s:%s", host, port)
    if not _port_is_available("127.0.0.1", port):
        logger.error("Port %s is already in use", port)
        return
    uvicorn.run(app, host=host, port=port, log_level="info", log_config=None)


if __name__ == "__main__":
    run_server()
