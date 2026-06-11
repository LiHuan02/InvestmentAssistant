import asyncio
import hashlib
import logging
import re
from datetime import datetime

from backend.models.news import NewsItem

logger = logging.getLogger(__name__)


class NewsService:
    def __init__(self):
        self._cache: list[NewsItem] = []
        self._seen_ids: set[str] = set()

    async def refresh(self) -> list[NewsItem]:
        try:
            loop = asyncio.get_event_loop()
            sina_items = await loop.run_in_executor(None, self._fetch_sina_news)
            if sina_items:
                self._merge_to_cache(sina_items)

            wscn_items = await loop.run_in_executor(None, self._fetch_wallstreetcn)
            if wscn_items:
                self._merge_to_cache(wscn_items)

            ak_items = await loop.run_in_executor(None, self._fetch_akshare_flash)
            if ak_items:
                self._merge_to_cache(ak_items)

            rss_items = await loop.run_in_executor(None, self._fetch_rss_news)
            if rss_items:
                self._merge_to_cache(rss_items)

            return self._cache
        except Exception as e:
            logger.error("刷新新闻失败: %s", e)
            return self._cache

    _IMPORTANT_KEYWORDS = [
        "突发", "紧急", "重大", "重磅", "暴涨", "暴跌", "熔断", "崩盘",
        "央行", "美联储", "降息", "加息", "GDP", "战争", "制裁",
        "关税", "贸易战", "黑天鹅", "闪崩", "停牌",
        "大涨", "大跌", "创新高", "创新低", "突破",
    ]

    def _merge_to_cache(self, new_items: list[NewsItem]) -> None:
        for item in new_items:
            if item.id not in self._seen_ids:
                self._seen_ids.add(item.id)
                if not item.is_important:
                    text = item.title + item.summary
                    item.is_important = any(kw in text for kw in self._IMPORTANT_KEYWORDS)
                self._cache.append(item)
        self._cache.sort(key=lambda x: (not x.is_important, -x.published_at.timestamp()))
        self._cache = self._cache[:60]

    async def get_cached(self, limit: int = 30, offset: int = 0) -> list[NewsItem]:
        return self._cache[offset: offset + limit]

    def _fetch_sina_news(self) -> list[NewsItem]:
        items = []
        try:
            import requests as req
            url = "https://feed.mix.sina.com.cn/api/roll/get"
            params = {"pageid": 153, "lid": 2509, "k": "", "num": 30, "page": 1}
            resp = req.get(url, params=params, timeout=10)
            data = resp.json()
            for item_data in data.get("result", {}).get("data", []):
                title = item_data.get("title", "")
                if not title:
                    continue
                summary = item_data.get("intro", title)
                link = item_data.get("url", "#")
                ctime = int(item_data.get("ctime", 0))
                published_at = datetime.fromtimestamp(ctime) if ctime else datetime.utcnow()
                source = item_data.get("media_name", "新浪财经")

                item_id = hashlib.md5(title.encode()).hexdigest()[:12]
                items.append(NewsItem(
                    id=item_id, title=title,
                    summary=summary[:200],
                    source=source, url=link,
                    published_at=published_at,
                    related_symbols=[],
                ))
            logger.info("新浪新闻 获取 %d 条", len(items))
        except Exception as e:
            logger.warning("新浪新闻获取失败: %s", e)
        return items

    def _fetch_wallstreetcn(self) -> list[NewsItem]:
        items = []
        try:
            import requests as req
            url = "https://api-one-wscn.awtmt.com/apiv1/content/articles/latest"
            resp = req.get(url, params={"limit": 20}, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            data = resp.json()
            for item_data in data.get("data", {}).get("items", []):
                resource = item_data.get("resource", {})
                title = resource.get("title", "")
                if not title:
                    continue
                content = resource.get("content_short", title)
                uri = resource.get("uri", "")
                link = f"https://wallstreetcn.com/articles/{uri}" if uri else "#"
                ts = resource.get("display_time", 0)
                published_at = datetime.fromtimestamp(ts) if ts else datetime.utcnow()

                item_id = hashlib.md5(title.encode()).hexdigest()[:12]
                items.append(NewsItem(
                    id=item_id, title=title,
                    summary=self._strip_html(content)[:200],
                    source="华尔街见闻", url=link,
                    published_at=published_at,
                    related_symbols=[],
                ))
            logger.info("华尔街见闻 获取 %d 条新闻", len(items))
        except Exception as e:
            logger.warning("华尔街见闻新闻获取失败: %s", e)
        return items

    def _fetch_akshare_flash(self) -> list[NewsItem]:
        items = []
        try:
            import akshare as ak
            try:
                df = ak.stock_info_global_em()
                if df is not None and not df.empty:
                    for _, row in df.head(15).iterrows():
                        title = str(row.get("标题", row.iloc[0] if len(row) > 0 else ""))
                        content = str(row.get("内容", title))
                        pub_time = str(row.get("发布时间", ""))
                        if not title:
                            continue
                        try:
                            published_at = datetime.strptime(pub_time, "%Y-%m-%d %H:%M:%S")
                        except (ValueError, TypeError):
                            published_at = datetime.utcnow()
                        item_id = hashlib.md5(title.encode()).hexdigest()[:12]
                        items.append(NewsItem(
                            id=item_id, title=title, summary=content[:200],
                            source="东方财富", url="#",
                            published_at=published_at, related_symbols=[],
                        ))
                    logger.info("AKShare 东方财富快讯 %d 条", len(items))
            except Exception as e:
                logger.warning("AKShare 东方财富快讯失败: %s", e)

            try:
                df = ak.stock_info_global_cls()
                if df is not None and not df.empty:
                    count = 0
                    for _, row in df.head(10).iterrows():
                        title = str(row.get("标题", row.iloc[0] if len(row) > 0 else ""))
                        content = str(row.get("内容", title))
                        pub_time = str(row.get("发布时间", ""))
                        if not title:
                            continue
                        try:
                            published_at = datetime.strptime(pub_time, "%Y-%m-%d %H:%M:%S")
                        except (ValueError, TypeError):
                            published_at = datetime.utcnow()
                        item_id = hashlib.md5(title.encode()).hexdigest()[:12]
                        items.append(NewsItem(
                            id=item_id, title=title, summary=content[:200],
                            source="财联社", url="#",
                            published_at=published_at, related_symbols=[],
                        ))
                        count += 1
                    logger.info("AKShare 财联社快讯 %d 条", count)
            except Exception as e:
                logger.warning("AKShare 财联社快讯失败: %s", e)
        except ImportError:
            logger.warning("akshare 未安装")
        return items

    def _fetch_rss_news(self) -> list[NewsItem]:
        items = []
        feeds = [
            ("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664", "CNBC财经"),
            ("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20409666", "CNBC市场"),
        ]
        try:
            import feedparser
            import socket
            old_timeout = socket.getdefaulttimeout()
            for url, source_name in feeds:
                try:
                    socket.setdefaulttimeout(8)
                    feed = feedparser.parse(url)
                    socket.setdefaulttimeout(old_timeout)
                    for entry in feed.entries[:10]:
                        title = entry.get("title", "")
                        if not title:
                            continue
                        summary = entry.get("summary", title)
                        link = entry.get("link", "#")
                        pub_time = entry.get("published_parsed") or entry.get("updated_parsed")
                        published_at = datetime(*pub_time[:6]) if pub_time else datetime.utcnow()
                        item_id = hashlib.md5(title.encode()).hexdigest()[:12]
                        items.append(NewsItem(
                            id=item_id, title=title,
                            summary=self._strip_html(summary)[:200],
                            source=source_name, url=link,
                            published_at=published_at, related_symbols=[],
                        ))
                    if feed.entries:
                        logger.info("RSS %s 获取 %d 条", source_name, min(len(feed.entries), 10))
                except Exception as e:
                    logger.warning("RSS %s 失败: %s", source_name, e)
            socket.setdefaulttimeout(old_timeout)
        except ImportError:
            logger.warning("feedparser 未安装")
        return items

    @staticmethod
    def _strip_html(text: str) -> str:
        clean = re.sub(r"<[^>]+>", "", text)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean
