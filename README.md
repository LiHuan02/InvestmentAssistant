# 市场投资助手

实时全球市场行情、财经资讯与 AI 投资分析助手。支持 Windows / macOS / Linux 桌面端独立运行，Android 通过 Termux 运行。

## 功能特性

### 全球行情（16+ 指数，真实实时数据）

| 区域 | 指数 | 数据源 |
|------|------|--------|
| A股 | 上证指数、深证成指、创业板指、科创综指 | 新浪财经 / AKShare |
| 港股 | 恒生指数、国企指数、恒生科技指数 | 腾讯财经 / AKShare |
| 美股 | 道琼斯、纳斯达克综合、标普500 | 新浪财经 |
| 日股 | 日经225 | 新浪财经 / AKShare |
| 韩股 | KOSPI | AKShare |
| 欧洲 | 富时100 | 新浪财经 |
| 商品 | 黄金、原油WTI、白银 | 新浪财经 |

- 黄金/白银支持 **美元/盎司** ↔ **元/克** 一键切换（实时汇率换算）
- 指数卡片含缩略走势图，点击打开完整 K 线图
- K 线图支持 **分时 / 5日 / 日K / 周K** 切换
- 可自定义 **红涨绿跌 / 绿涨红跌** 颜色方案
- 未开市市场自动标注「休市」

### 财经资讯
- 新浪财经 API + AKShare 东方财富快讯 + 财联社电报
- CNBC RSS 国际财经新闻
- 重要新闻自动高亮（央行、降息、暴涨等关键词匹配）

### AI 投资助手
- 基于 LangGraph + LangChain，支持 OpenAI 兼容接口（OpenAI / DeepSeek / Ollama / GLM 等）
- 流式输出（SSE），逐字显示
- **7 个内置工具**：行情总览、指数详情、K线数据、最新新闻、市场状态、联网搜索、知识库检索
- **技能系统**：可启用/禁用分析技能（技术分析、风险提示、宏观视角等）
- **MCP 协议**：支持接入外部 MCP 服务器扩展能力
- **对话历史**：SQLite 持久化，支持搜索、导出
- **CLI 风格交互**：`/skill`、`/mcp`、`/model` 等斜杠命令打开交互式面板

### 斜杠命令

| 命令 | 交互方式 | 说明 |
|------|---------|------|
| `/skill` | 面板 (toggle) | ↑↓ 导航，Enter 切换启用/禁用 |
| `/mcp` | 面板 (toggle) | MCP 服务器管理 |
| `/model` | 面板 (select) | 从 API 获取真实模型列表 |
| `/temperature` | 面板 (select) | 0~2.0 温度调节 |
| `/tokens` | 面板 (select) | 512~16384 Token 数 |
| `/status` | 面板 (info) | 系统全部状态 |
| `/search <词>` | 面板 (info) | 搜索对话内容 |
| `/clear` | 静默 | 清空对话 |
| `/new` | 静默 | 新对话 |
| `/export` | 静默 | 导出为 .txt |

## 技术栈

| 层 | 技术 |
|----|------|
| 桌面壳 | Tauri 2.0 (Rust) |
| 前端 | React 19 + TypeScript + Vite + Ant Design 6 + Recharts |
| 后端 | Python 3.12 + FastAPI + WebSocket + APScheduler |
| AI | LangGraph + LangChain + langchain-openai + langchain-tavily |
| RAG | ChromaDB + langchain-chroma |
| MCP | langchain-mcp-adapters |
| 数据 | 新浪/腾讯财经 API + AKShare + yfinance |
| 状态 | Zustand (持久化) + React Query (服务端) |
| 打包 | PyInstaller (sidecar) + Tauri (安装包) |
| CI/CD | GitHub Actions (matrix: Win/Mac/Linux) |

## 安装与使用

### 发布版（推荐）

从 [Releases](../../releases) 下载对应平台的安装包：

| 平台 | 格式 | 文件 |
|------|------|------|
| Windows | NSIS 安装程序 | `InvestmentAssistant_x.x.x_x64-setup.exe` |
| macOS | DMG 磁盘映像 | `InvestmentAssistant_x.x.x_aarch64.dmg` |
| Linux | AppImage | `InvestmentAssistant_x.x.x_amd64.AppImage` |
| Linux | Debian 包 | `investment-assistant_x.x.x_amd64.deb` |
| Android | Termux 脚本 | `install-android.sh` |

安装后双击运行，首次启动会引导你配置 API Key。

### 开发版

#### 前置条件
- Python 3.12+（已安装 [uv](https://docs.astral.sh/uv/)）
- Node.js 18+
- （桌面打包额外需要）Rust + Tauri CLI

#### 安装与启动

```bash
# 1. 克隆项目
git clone <repo-url>
cd InvestmentAssistant

# 2. 安装依赖
uv sync                          # Python 后端依赖
cd frontend && npm install       # 前端依赖
cd ..

# 3. 启动（一条命令同时启动前后端）
cd frontend && npm run dev
```

浏览器自动打开 `http://localhost:5173`。首次使用时在设置页配置 API Key。

#### 单独启动

```bash
# 后端
uv run uvicorn backend.main:app --reload --port 8000

# 前端（需先启动后端）
cd frontend && npx vite
```

### Android (Termux)

```bash
# 在 Termux 中运行
pkg install curl
curl -sSL <repo-raw-url>/scripts/install-android.sh | bash
./start.sh
```

## 构建打包

### 桌面端

```bash
# 1. 安装 Tauri CLI
cargo install tauri-cli

# 2. 构建 Python sidecar
# Windows:
powershell -File scripts/build-sidecar.ps1
# macOS/Linux:
bash scripts/build-sidecar.sh

# 3. 构建 Tauri 安装包
cargo tauri build
```

输出位置：`src-tauri/target/release/bundle/`

### CI/CD 自动构建

推送 `v*` 格式的 tag 即可触发自动构建：

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions 会在 Win/Mac/Linux 三个平台自动构建并创建 Release。

## 项目结构

```
InvestmentAssistant/
├── pyproject.toml                # Python 依赖
├── .env.example                  # 环境变量模板
├── README.md                     # 本文档
│
├── backend/                      # Python 后端
│   ├── main.py                   # FastAPI 入口
│   ├── config.py                 # 配置管理
│   ├── investment-backend.spec   # PyInstaller spec
│   ├── mcp_config.yaml           # MCP 服务器配置
│   ├── models/                   # 数据模型
│   ├── routers/                  # API 路由
│   │   ├── chat.py               # 对话 + Agent
│   │   ├── history.py            # 对话历史
│   │   ├── market.py             # 行情 + K线
│   │   ├── news.py               # 新闻
│   │   ├── settings.py           # 设置管理
│   │   └── ws.py                 # WebSocket
│   ├── services/                 # 业务逻辑
│   │   ├── agent_tools.py        # Agent 内置工具
│   │   ├── chat_service.py       # LangGraph Agent
│   │   ├── history_service.py    # SQLite 对话历史
│   │   ├── market_service.py     # 多源行情数据
│   │   ├── mcp_manager.py        # MCP 服务器管理
│   │   ├── news_service.py       # 新闻聚合
│   │   ├── rag_service.py        # ChromaDB RAG
│   │   ├── skills_service.py     # 技能管理
│   │   └── settings_service.py   # 设置服务
│   └── core/
│       ├── event_bus.py          # 事件总线
│       └── scheduler.py          # 定时任务
│
├── frontend/                     # React 前端
│   ├── dev.mjs                   # 开发启动脚本
│   ├── vite.config.ts            # Vite 配置
│   └── src/
│       ├── App.tsx               # 路由 + 首次检测
│       ├── api/                  # API 客户端
│       ├── hooks/                # 自定义 Hooks
│       ├── store/                # Zustand 状态
│       ├── components/
│       │   ├── chat/             # 对话组件（面板、命令、气泡）
│       │   ├── layout/           # 布局（侧边栏、头部）
│       │   ├── market/           # 行情（卡片、K线、弹窗）
│       │   └── news/             # 新闻（列表、卡片）
│       ├── pages/                # 页面
│       │   ├── ChatPage.tsx
│       │   ├── MarketPage.tsx
│       │   ├── NewsPage.tsx
│       │   ├── SettingsPage.tsx
│       │   └── SetupPage.tsx     # 首次引导
│       └── types/                # TypeScript 类型
│
├── src-tauri/                    # Tauri 桌面壳
│   ├── Cargo.toml                # Rust 依赖
│   ├── tauri.conf.json           # Tauri 配置
│   ├── src/main.rs               # Rust 入口
│   └── binaries/                 # PyInstaller 输出
│
├── scripts/                      # 构建脚本
│   ├── build-sidecar.sh          # Mac/Linux sidecar 构建
│   ├── build-sidecar.ps1         # Windows sidecar 构建
│   └── install-android.sh        # Termux 安装脚本
│
├── .github/workflows/
│   └── release.yml               # CI/CD 流水线
│
└── data/                         # 运行时数据（gitignore）
    ├── conversations.db          # SQLite 对话历史
    ├── rag_db/                   # ChromaDB 向量库
    └── skills.json               # 技能配置
```

## 配置说明

### 环境变量 (.env)

```env
# AI 设置（必填，支持任何 OpenAI 兼容接口）
AI_API_KEY=sk-your-key
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini

# 联网搜索（可选）
TAVILY_API_KEY=tvly-your-key

# K线数据（可选）
TWELVEDATA_API=your-key

# RAG 知识库（可选，设置路径后自动启用）
RAG_PERSIST_DIR=./data/rag_db

# 服务设置
PORT=8000
MARKET_REFRESH_INTERVAL=60
NEWS_REFRESH_INTERVAL=300
```

### MCP 服务器 (backend/mcp_config.yaml)

```yaml
mcp_servers:
  alpha_vantage:
    enabled: true
    transport: streamable_http
    url: "https://mcp.alphavantage.co/mcp"
    env:
      ALPHAVANTAGE_API_KEY: "${ALPHAVANTAGE_API_KEY}"

  brave_search:
    enabled: true
    command: npx
    args: ["-y", "@modelcontextprotocol/server-brave-search"]
    transport: stdio
    env:
      BRAVE_API_KEY: "${BRAVE_API_KEY}"
```

### 支持的 AI 提供商

| 提供商 | Base URL | 免费额度 |
|--------|----------|---------|
| OpenAI | `https://api.openai.com/v1` | 付费 |
| DeepSeek | `https://api.deepseek.com/v1` | 有免费额度 |
| Ollama 本地 | `http://localhost:11434/v1` | 免费 |
| Ollama Cloud | `https://ollama.com/v1` | 部分免费 |
| GLM (智谱) | `https://open.bigmodel.cn/api/paas/v4` | 有免费额度 |
| MiniMax | `https://api.minimax.chat/v1` | 有免费额度 |
| Kimi (月之暗面) | `https://api.moonshot.cn/v1` | 有免费额度 |

## 数据源优先级

| 市场 | 主力 | 备用 |
|------|------|------|
| A股 | 新浪财经 | AKShare（东方财富） |
| 港股 | AKShare | 腾讯财经 |
| 全球指数 | 新浪财经 (gb_) | yfinance |
| 大宗商品 | 新浪财经 (hf_) | - |
| 新闻 | 新浪财经 + AKShare | CNBC RSS |

## 许可证

MIT License
