"""
News service using feedparser for RSS feeds.
"""
import re
import logging
import feedparser

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    ("https://feedx.net/rss/caijing.xml", "财经网"),
    ("https://feedx.net/rss/ftchinese.xml", "FT中文网"),
    ("https://www.yicai.com/rss/feed.xml", "第一财经"),
    ("https://feedx.net/rss/wallstreetcn.xml", "华尔街见闻"),
]

IMPORTANT_KEYWORDS = [
    "突发", "紧急", "重大", "重磅", "暴涨", "暴跌", "熔断", "崩盘",
    "央行", "美联储", "降息", "加息", "GDP", "战争", "制裁",
    "关税", "贸易战", "大涨", "大跌", "创新高", "创新低",
]


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def fetch_news(limit: int = 30) -> list[dict]:
    """Fetch news from RSS feeds."""
    all_items = []
    for url, source in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = entry.get("title", "")
                if not title:
                    continue
                summary = _strip_html(entry.get("summary", title))[:200]
                link = entry.get("link", "#")
                pub_time = entry.get("published_parsed") or entry.get("updated_parsed")
                if pub_time:
                    from datetime import datetime
                    published = datetime(*pub_time[:6]).isoformat()
                else:
                    published = datetime.utcnow().isoformat()

                text = title + summary
                is_important = any(kw in text for kw in IMPORTANT_KEYWORDS)

                all_items.append({
                    "id": str(hash(title))[:12],
                    "title": title,
                    "summary": summary,
                    "source": source,
                    "url": link,
                    "published_at": published,
                    "related_symbols": [],
                    "is_important": is_important,
                })
        except Exception as e:
            logger.warning("RSS %s 获取失败: %s", source, e)

    all_items.sort(key=lambda x: x["published_at"], reverse=True)
    return all_items[:limit]
