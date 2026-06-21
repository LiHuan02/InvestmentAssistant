"""
AI chat service using direct HTTP calls to OpenAI-compatible API.
No pydantic dependency - uses httpx directly.
"""
import json
import logging
import httpx

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位专业的投资顾问AI助手，具备以下能力：
1. 实时行情查询：获取全球主要市场的实时行情
2. K线分析：查询任意指数的历史数据
3. 新闻获取：获取最新的财经新闻和市场资讯
4. 联网搜索：搜索互联网获取最新的市场动态
5. 市场分析：基于数据和新闻，提供专业的市场分析和投资建议

使用规则：
- 回答必须基于数据，引用具体数字
- 分析要客观，兼顾多空两面
- 涉及具体投资决策时，务必附上免责声明
- 使用中文回复，格式清晰，善用表格和列表"""


async def chat_stream(
    message: str,
    history: list[dict],
    api_key: str,
    base_url: str,
    model: str,
    max_tokens: int = 2048,
    temperature: float = 0.7,
):
    """Stream chat response from OpenAI-compatible API."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    yield json.dumps({"error": f"API error {resp.status_code}: {body.decode()[:200]}"})
                    return

                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:].strip()
                    if data == "[DONE]":
                        return
                    try:
                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield json.dumps({"token": content})
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        yield json.dumps({"error": str(e)})


QUICK_COMMANDS = [
    {"id": "advice_today", "label": "今日投资建议", "prompt": "请获取当前全球市场行情，然后给出今日投资建议。", "icon": "BulbOutlined"},
    {"id": "analysis_yesterday", "label": "昨日市场回顾", "prompt": "请获取全球主要股指数据并分析昨日市场表现。", "icon": "LineChartOutlined"},
    {"id": "market_outlook", "label": "本周市场展望", "prompt": "请搜索本周重要财经事件和市场日历，展望本周走势。", "icon": "FundOutlined"},
    {"id": "sector_analysis", "label": "板块分析", "prompt": "请获取当前行情数据，分析哪些板块表现强势、哪些走弱。", "icon": "PieChartOutlined"},
    {"id": "risk_assessment", "label": "风险评估", "prompt": "请搜索当前市场主要风险因素，包括地缘政治、政策变化、经济数据等。", "icon": "WarningOutlined"},
    {"id": "commodity_update", "label": "大宗商品动态", "prompt": "请获取黄金、原油、白银等大宗商品的最新行情并分析走势。", "icon": "GoldOutlined"},
]
