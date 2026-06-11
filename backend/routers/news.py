from fastapi import APIRouter, Request

from backend.models.news import NewsItem

router = APIRouter(prefix="/api/v1/news", tags=["news"])


@router.get("")
async def get_news(
    request: Request, limit: int = 20, offset: int = 0
) -> list[NewsItem]:
    service = request.app.state.news_service
    return await service.get_cached(limit=limit, offset=offset)
