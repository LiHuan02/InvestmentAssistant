# 市场投资助手

实时全球市场行情、财经资讯与 AI 投资分析助手。

## 功能特性

### 行情数据（15+ 指数，真实实时数据）
| 区域 | 指数 | 数据源 |
|------|------|--------|
| A股 | 上证指数、深证成指、创业板指、科创指数 | 新浪财经 |
| 港股 | 恒生指数、国企指数、恒生科技指数 | 腾讯财经 |
| 美股 | 道琼斯、纳斯达克综合、标普500 | 新浪财经 (gb_) |
| 日股 | 日经225 | 新浪财经 |
| 欧洲 | 富时100 | 新浪财经 |
| 大宗商品 | 黄金、原油WTI、白银 | 新浪财经 (hf_) |

- 黄金/白银支持 **美元/盎司** 与 **元/克** 一键切换（实时汇率换算）
- 每个指数卡片含缩略走势图，点击打开完整 K 线图
- K 线图支持 **分时 / 5日 / 日K / 周K** 切换
- 可自定义 **红涨绿跌 / 绿涨红跌** 颜色方案

### 财经资讯
- 新浪财经 API 实时推送（30+ 条）
- AKShare 东方财富快讯、财联社电报
- CNBC RSS 国际财经新闻
- 重要新闻自动高亮（央行、降息、暴涨等关键词匹配）

### AI 投资助手
- 基于 LangChain + OpenAI 兼容接口（支持 OpenAI / DeepSeek / Ollama）
- 流式输出（SSE），逐字显示回复
- 6 个快捷指令：今日投资建议、昨日市场回顾、本周展望、板块分析、风险评估、大宗商品动态

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 19 + TypeScript + Vite + Ant Design + Recharts |
| 后端 | Python 3.12 + FastAPI + WebSocket |
| 数据 | 新浪财经 API + 腾讯财经 API + AKShare + yfinance |
| AI | LangChain + langchain-openai |
| 状态 | Zustand（持久化设置）+ React Query（服务端状态） |

## 快速开始

### 前置条件
- Python 3.12+（已安装 [uv](https://docs.astral.sh/uv/)）
- Node.js 18+

### 安装与启动

```bash
# 1. 克隆项目
git clone <repo-url>
cd InvestmentAssistant

# 2. 安装依赖
uv sync                          # Python 后端依赖
cd frontend && npm install       # 前端依赖

# 3. 配置 AI（可选）
cp .env.example .env
# 编辑 .env 填入 AI API Key（不填则 AI 助手不可用，行情和新闻不受影响）

# 4. 启动（一条命令同时启动前后端）
cd frontend
npm run dev
```

浏览器自动打开 `http://localhost:5173`。

### 单独启动

```bash
# 后端
uv run uvicorn backend.main:app --reload --port 8000

# 前端（需先启动后端）
cd frontend && npx vite
```

## 项目结构

```
InvestmentAssistant/
├── .env.example              # 环境变量模板
├── pyproject.toml            # Python 依赖定义
├── backend/
│   ├── main.py               # FastAPI 入口，生命周期管理
│   ├── config.py             # 配置加载（pydantic-settings）
│   ├── models/               # 数据模型（IndexData, NewsItem, ChatMessage）
│   ├── services/
│   │   ├── market_service.py # 行情数据（新浪/腾讯/AKShare/yfinance 多源）
│   │   ├── news_service.py   # 新闻聚合（新浪/东方财富/财联社/CNBC）
│   │   └── chat_service.py   # AI 对话（LangChain 流式输出）
│   ├── routers/              # API 路由
│   └── core/                 # 事件总线、定时任务
├── frontend/
│   ├── dev.mjs               # 一键启动脚本（后端+前端）
│   ├── vite.config.ts        # Vite 配置（API 代理）
│   └── src/
│       ├── api/              # 后端 API 调用
│       ├── hooks/            # useMarketData, useNews, useChat, useWebSocket
│       ├── store/            # Zustand 状态（设置持久化、新闻、对话）
│       ├── components/
│       │   ├── market/       # 行情卡片、K线图表、弹窗
│       │   ├── news/         # 新闻列表、高亮卡片
│       │   └── chat/         # 对话面板、快捷指令、消息气泡
│       └── pages/            # 行情页、资讯页、助手页、设置页
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/market/indices` | 全部行情（按区域分组） |
| GET | `/api/v1/market/kline/{symbol}?period=day` | K线数据（minute/5day/day/week） |
| GET | `/api/v1/news` | 新闻列表 |
| POST | `/api/v1/chat/message` | AI 对话（SSE 流式） |
| GET | `/api/v1/chat/commands` | 快捷指令列表 |
| WS | `/ws/market` | 行情实时推送 |
| WS | `/ws/news` | 新闻实时推送 |

## 配置说明

编辑 `.env` 文件：

```env
# AI 设置（可选）
AI_API_KEY=sk-your-key
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini

# TwelveData API（可选，用于全球指数 K 线）
TWELVEDATA_API=your-key

# 服务设置
PORT=8000
MARKET_REFRESH_INTERVAL=60
```

## 数据源优先级

| 市场 | 主力 | 备用 |
|------|------|------|
| A股 | 新浪财经 API | AKShare（东方财富） |
| 港股 | AKShare | 腾讯财经 API |
| 全球指数 | 新浪财经 (gb_) | yfinance |
| 大宗商品 | 新浪财经 (hf_) | - |
| 新闻 | 新浪财经 API | AKShare + CNBC RSS |
