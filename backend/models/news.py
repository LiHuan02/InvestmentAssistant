from datetime import datetime

from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    id: str
    title: str
    summary: str
    source: str
    url: str
    published_at: datetime
    related_symbols: list[str] = []
    is_important: bool = False
