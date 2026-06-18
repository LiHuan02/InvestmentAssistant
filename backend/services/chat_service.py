import json
import logging
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from backend.config import Settings
from backend.models.chat import ChatMessage, QuickCommand
from backend.services.agent_tools import (
    get_builtin_tools,
    init_tool_services,
    load_search_tools,
)
from backend.services.mcp_manager import MCPManager
from backend.services.rag_service import ChromaRAGService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位专业的投资顾问AI助手，具备以下能力：

1. **实时行情查询**：获取全球主要市场（A股、港股、美股、日股、韩股、欧洲、大宗商品）的实时行情
2. **K线分析**：查询任意指数的分时、日K、周K历史数据
3. **新闻获取**：获取最新的财经新闻和市场资讯
4. **联网搜索**：搜索互联网获取最新的市场动态、政策解读、公司公告
5. **知识库检索**：从本地知识库中检索相关投资研究报告和资料
6. **市场分析**：基于数据和新闻，提供专业的市场分析和投资建议

使用规则：
- 回答必须基于数据，引用具体数字
- 当用户询问行情、市场数据时，优先使用工具获取最新实时数据
- 当用户询问最新新闻或市场动态时，使用新闻工具或联网搜索
- 分析要客观，兼顾多空两面
- 涉及具体投资决策时，务必附上免责声明
- 使用中文回复，格式清晰，善用表格和列表
- 使用 Markdown 格式组织回复内容"""


@tool
def search_knowledge_base(query: str) -> str:
    """从本地知识库中检索与查询相关的投资研究报告和资料。参数 query: 搜索关键词。"""
    rag = _rag_service
    if not rag or not rag.is_available:
        return "知识库尚未初始化，暂无可检索的资料。"
    results = rag.search(query, top_k=3)
    if not results:
        return "未找到相关资料。"
    lines = [f"找到 {len(results)} 条相关资料:"]
    for i, doc in enumerate(results, 1):
        content = doc.get("content", "")[:200]
        meta = doc.get("metadata", {})
        source = meta.get("source", "未知")
        lines.append(f"  {i}. [{source}] {content}")
    return "\n".join(lines)


_rag_service: ChromaRAGService | None = None


class ChatService:
    QUICK_COMMANDS: list[QuickCommand] = [
        QuickCommand(id="advice_today", label="今日投资建议",
                     prompt="请获取当前全球市场行情，然后给出今日投资建议。", icon="BulbOutlined"),
        QuickCommand(id="analysis_yesterday", label="昨日市场回顾",
                     prompt="请获取全球主要股指数据并分析昨日市场表现。", icon="LineChartOutlined"),
        QuickCommand(id="market_outlook", label="本周市场展望",
                     prompt="请搜索本周重要财经事件和市场日历，展望本周走势。", icon="FundOutlined"),
        QuickCommand(id="sector_analysis", label="板块分析",
                     prompt="请获取当前行情数据，分析哪些板块表现强势、哪些走弱。", icon="PieChartOutlined"),
        QuickCommand(id="risk_assessment", label="风险评估",
                     prompt="请搜索当前市场主要风险因素，包括地缘政治、政策变化、经济数据等。", icon="WarningOutlined"),
        QuickCommand(id="commodity_update", label="大宗商品动态",
                     prompt="请获取黄金、原油、白银等大宗商品的最新行情并分析走势。", icon="GoldOutlined"),
    ]

    def __init__(self, settings: Settings, market_service: Any = None, news_service: Any = None):
        self._settings = settings
        self._llm = ChatOpenAI(
            api_key=settings.ai_api_key or "dummy",
            base_url=settings.ai_base_url,
            model=settings.ai_model,
            max_tokens=settings.ai_max_tokens,
            temperature=settings.ai_temperature,
            streaming=True,
        )

        if market_service and news_service:
            init_tool_services(market_service, news_service)

        tools: list = get_builtin_tools()
        tools.extend(load_search_tools(settings))

        global _rag_service
        _rag_service = ChromaRAGService(persist_dir=str(Path(settings.rag_persist_dir) if settings.rag_persist_dir else None))
        if _rag_service.is_available:
            tools.append(search_knowledge_base)

        config_path = str(Path(__file__).parent.parent / "mcp_config.yaml")
        self._mcp_manager = MCPManager(config_path)

        self._tools = tools
        self._agent = create_react_agent(self._llm, tools, prompt=SYSTEM_PROMPT)

    def get_commands(self) -> list[QuickCommand]:
        return self.QUICK_COMMANDS

    async def stream_message(
        self, message: str, history: list[ChatMessage]
    ) -> AsyncGenerator[str, None]:
        messages = self._build_messages(message, history)
        input_state = {"messages": messages}

        try:
            async for event in self._agent.astream_events(input_state, version="v2"):
                kind = event.get("event")
                data = event.get("data", {})

                if kind == "on_tool_start":
                    tool_name = event.get("name", "")
                    tool_input = data.get("input", {})
                    yield json.dumps({
                        "tool_start": {"name": tool_name, "input": str(tool_input)[:200]}
                    })

                elif kind == "on_tool_end":
                    tool_name = event.get("name", "")
                    output = data.get("output", "")
                    output_str = str(output)[:300] if output else ""
                    yield json.dumps({
                        "tool_end": {"name": tool_name, "output": output_str}
                    })

                elif kind == "on_chat_model_stream":
                    chunk = data.get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        token = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                        yield json.dumps({"token": token})

        except Exception as e:
            logger.error("Agent 执行失败: %s", e)
            yield json.dumps({"error": str(e)})

    def _build_messages(self, user_msg: str, history: list[ChatMessage]) -> list[BaseMessage]:
        messages: list[BaseMessage] = []
        for msg in history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
        messages.append(HumanMessage(content=user_msg))
        return messages
