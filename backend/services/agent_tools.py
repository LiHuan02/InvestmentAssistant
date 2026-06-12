import json
import logging
from typing import Any

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

_market_service = None
_news_service = None


def init_tool_services(market_service: Any, news_service: Any) -> None:
    global _market_service, _news_service
    _market_service = market_service
    _news_service = news_service


@tool
def get_market_overview() -> str:
    """获取全球所有主要市场的实时行情数据，包括A股、港股、美股、日股、韩股、欧洲和大宗商品。
    返回每个指数的最新价格、涨跌幅和单位名称。"""
    if not _market_service:
        return "行情服务未初始化"
    cached = _market_service.get_cached()
    if not cached:
        return "暂无行情数据，请稍后再试"
    lines = []
    for region, indices in cached.items():
        lines.append(f"【{region}】")
        for idx in indices:
            line = f"  {idx.name}: {idx.price} ({idx.change_percent:+.2f}%)"
            if idx.unit:
                line += f" {idx.unit}"
            if idx.alt_price and idx.alt_unit:
                line += f" | 中国价: {idx.alt_price} {idx.alt_unit}"
            lines.append(line)
    return "\n".join(lines)


@tool
def get_index_detail(symbol: str) -> str:
    """查询单个指数的详细信息。
    参数 symbol: 指数代码，如 000001(上证)、HSI(恒生)、^DJI(道琼斯)、^N225(日经)、GC=F(黄金) 等。"""
    if not _market_service:
        return "行情服务未初始化"
    idx = _market_service.get_index(symbol)
    if not idx:
        return f"未找到指数 {symbol}，请检查代码是否正确"
    result = {
        "名称": idx.name,
        "代码": idx.symbol,
        "区域": idx.region,
        "最新价": idx.price,
        "涨跌额": idx.change,
        "涨跌幅": f"{idx.change_percent:+.2f}%",
        "单位": idx.unit or "",
    }
    if idx.alt_price and idx.alt_unit:
        result["中国价"] = f"{idx.alt_price} {idx.alt_unit}"
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def get_kline_data(symbol: str, period: str = "day") -> str:
    """获取指数的K线历史数据。
    参数 symbol: 指数代码。
    参数 period: 周期，可选 minute(分时)、5day(5日)、day(日K)、week(周K)。"""
    if not _market_service:
        return "行情服务未初始化"
    data = _market_service.get_kline(symbol, period)
    if not data or not data.get("dates"):
        return f"未获取到 {symbol} 的 {period} K线数据"
    n = len(data["dates"])
    lines = [f"{data['name']} {period}K线 (共{n}条):"]
    show_n = min(10, n)
    for i in range(n - show_n, n):
        lines.append(
            f"  {data['dates'][i]}: 开{data['opens'][i]} 高{data['highs'][i]} "
            f"低{data['lows'][i]} 收{data['closes'][i]}"
        )
    if n > show_n:
        lines.insert(1, f"  ... (省略前{n - show_n}条)")
    return "\n".join(lines)


@tool
def get_latest_news(limit: int = 10) -> str:
    """获取最新的财经新闻标题和摘要。
    参数 limit: 返回新闻条数，默认10条，最多30条。"""
    if not _news_service:
        return "新闻服务未初始化"
    items = _news_service._cache[:min(limit, 30)]
    if not items:
        return "暂无新闻数据"
    lines = [f"最新 {len(items)} 条财经新闻:"]
    for item in items:
        tag = "[重要] " if item.is_important else ""
        lines.append(f"  {tag}[{item.source}] {item.title}")
        if item.summary and item.summary != item.title:
            lines.append(f"    {item.summary[:100]}")
    return "\n".join(lines)


@tool
def get_market_status() -> str:
    """获取全球各主要市场当前的开盘/收盘状态。"""
    if not _market_service:
        return "行情服务未初始化"
    status = _market_service.get_market_status()
    lines = [f"当前UTC时间: {status['utc_time']}"]
    for region, is_open in status["markets"].items():
        lines.append(f"  {region}: {'交易中' if is_open else '已收盘'}")
    return "\n".join(lines)


def get_all_tools() -> list:
    return [
        get_market_overview,
        get_index_detail,
        get_kline_data,
        get_latest_news,
        get_market_status,
    ]
