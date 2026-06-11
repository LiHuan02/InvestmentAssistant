import logging
from collections.abc import AsyncGenerator

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from backend.config import Settings
from backend.models.chat import ChatMessage, ChatResponse, QuickCommand

logger = logging.getLogger(__name__)


class ChatService:
    SYSTEM_PROMPT = """你是一位专业的投资顾问助手。
请提供简洁、数据驱动的市场分析和投资建议。
尽可能引用具体的指数数据和行情数字。
分析要客观、全面，兼顾多空两面。
最后请附上简短免责声明：以上为AI分析，仅供参考，不构成投资建议。"""

    QUICK_COMMANDS: list[QuickCommand] = [
        QuickCommand(
            id="advice_today", label="今日投资建议",
            prompt="请根据今天的市场行情，给出你的投资建议。",
            icon="BulbOutlined",
        ),
        QuickCommand(
            id="analysis_yesterday", label="昨日市场回顾",
            prompt="请分析昨日全球主要股指的表现。",
            icon="LineChartOutlined",
        ),
        QuickCommand(
            id="market_outlook", label="本周市场展望",
            prompt="请展望本周的市场走势，有哪些关键事件需要关注？",
            icon="FundOutlined",
        ),
        QuickCommand(
            id="sector_analysis", label="板块分析",
            prompt="当前哪些板块表现强势，哪些板块走弱？请做详细分析。",
            icon="PieChartOutlined",
        ),
        QuickCommand(
            id="risk_assessment", label="风险评估",
            prompt="当前市场环境下，有哪些主要风险因素需要警惕？",
            icon="WarningOutlined",
        ),
        QuickCommand(
            id="commodity_update", label="大宗商品动态",
            prompt="请分析黄金、原油、白银等大宗商品的最新走势。",
            icon="GoldOutlined",
        ),
    ]

    def __init__(self, settings: Settings):
        self._llm = ChatOpenAI(
            api_key=settings.ai_api_key or "dummy",
            base_url=settings.ai_base_url,
            model=settings.ai_model,
            max_tokens=settings.ai_max_tokens,
            temperature=settings.ai_temperature,
            streaming=True,
        )
        self._history: list[dict] = []

    def get_commands(self) -> list[QuickCommand]:
        return self.QUICK_COMMANDS

    async def send_message(
        self, message: str, history: list[ChatMessage]
    ) -> ChatResponse:
        messages = self._build_messages(message, history)
        response = await self._llm.ainvoke(messages)
        content = response.content if isinstance(response.content, str) else str(response.content)
        self._history.append({"role": "user", "content": message})
        self._history.append({"role": "assistant", "content": content})
        usage = {}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = {
                "prompt_tokens": response.usage_metadata.get("input_tokens", 0),
                "completion_tokens": response.usage_metadata.get("output_tokens", 0),
            }
        return ChatResponse(
            message=ChatMessage(role="assistant", content=content),
            usage=usage if usage else None,
        )

    async def stream_message(
        self, message: str, history: list[ChatMessage]
    ) -> AsyncGenerator[str, None]:
        messages = self._build_messages(message, history)
        full_content = ""
        async for chunk in self._llm.astream(messages):
            token = chunk.content if isinstance(chunk.content, str) else ""
            if token:
                full_content += token
                yield token
        self._history.append({"role": "user", "content": message})
        self._history.append({"role": "assistant", "content": full_content})

    def get_history(self) -> list[dict]:
        return self._history

    def clear_history(self) -> None:
        self._history.clear()

    def _build_messages(
        self, user_msg: str, history: list[ChatMessage]
    ) -> list[BaseMessage]:
        messages: list[BaseMessage] = [SystemMessage(content=self.SYSTEM_PROMPT)]
        for msg in history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
        messages.append(HumanMessage(content=user_msg))
        return messages
