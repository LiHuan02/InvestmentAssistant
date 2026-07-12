"""
Android entry point - lightweight HTTP server using only pure Python + requests + httpx + feedparser.
No pydantic, no FastAPI, no C/Rust extensions.
"""
import json
import os
import sys
import threading
import time
import asyncio
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Chaquopy places this module and the android_backend package in the same
# Python source directory inside the APK.
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from android_backend.market import fetch_all_indices
from android_backend.news import fetch_news
from android_backend.chat import chat_stream, QUICK_COMMANDS, SYSTEM_PROMPT

# ── Config ─────────────────────────────────────────────────

def _load_config() -> dict:
    """Load config from .env file."""
    config = {
        "ai_api_key": "",
        "ai_base_url": "https://ollama.com/v1",
        "ai_model": "glm-4.7",
        "ai_max_tokens": 2048,
        "ai_temperature": 0.7,
        "tavily_api_key": "",
        "market_refresh_interval": 60,
        "news_refresh_interval": 300,
    }
    env_file = os.path.join(APP_DIR, ".env")
    if not os.path.exists(env_file):
        env_file = os.path.join(os.path.dirname(APP_DIR), ".env")
    if os.path.exists(env_file):
        with open(env_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip().lower()
                val = val.strip().strip('"').strip("'")
                if key in config:
                    if key in ("ai_max_tokens", "market_refresh_interval", "news_refresh_interval"):
                        config[key] = int(val)
                    elif key == "ai_temperature":
                        config[key] = float(val)
                    else:
                        config[key] = val
    return config


# ── Conversation history (in-memory) ──────────────────────

_conversations: dict[str, list[dict]] = {}


# ── HTTP Handler ──────────────────────────────────────────

class AndroidHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves frontend and provides API endpoints."""

    config = {}
    dist_dir = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=self.dist_dir, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/v1/health":
            self._json({"status": "ok", "platform": "android"})
        elif path == "/api/v1/market/indices":
            self._json(fetch_all_indices())
        elif path.startswith("/api/v1/market/kline/"):
            symbol = path.split("/")[-1]
            qs = parse_qs(parsed.query)
            period = qs.get("period", ["day"])[0]
            self._json(self._get_kline_stub(symbol, period))
        elif path == "/api/v1/market/status":
            self._json(self._get_market_status())
        elif path == "/api/v1/news":
            self._json(fetch_news())
        elif path == "/api/v1/chat/commands":
            self._json(QUICK_COMMANDS)
        elif path == "/api/v1/chat/config":
            self._json(self._get_config_response())
        elif path == "/api/v1/chat/models":
            self._json(self._get_models())
        elif path == "/api/v1/chat/tools":
            self._json(self._get_tools())
        elif path == "/api/v1/chat/mcp":
            self._json([])
        elif path == "/api/v1/chat/skills":
            self._json(self._get_skills())
        elif path == "/api/v1/settings":
            self._json(self._get_config_response())
        elif path == "/api/v1/history":
            self._json(list(_conversations.keys()))
        elif path.startswith("/api/v1/history/"):
            conv_id = path.split("/")[-1]
            self._json({"messages": _conversations.get(conv_id, [])})
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length)) if content_length > 0 else {}

        if path == "/api/v1/chat/message":
            self._handle_chat_message(body)
        elif path == "/api/v1/settings":
            self._update_config(body)
            self._json({"updated": list(body.keys())})
        elif path == "/api/v1/settings/test-connection":
            self._json(self._test_connection(body))
        elif path == "/api/v1/chat/config":
            self._update_config(body)
            self._json({"updated": list(body.keys())})
        elif path == "/api/v1/chat/mcp/reload":
            self._json({"model": self.config.get("ai_model", "")})
        elif path.startswith("/api/v1/skill/"):
            self._json({"ok": True})
        elif path == "/api/v1/history":
            conv_id = str(int(time.time()))
            _conversations[conv_id] = []
            self._json({"id": conv_id, "title": "新对话"})
        else:
            self.send_error(404)

    def do_PUT(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length)) if content_length > 0 else {}
        self._json({"ok": True})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        conv_id = parsed.path.split("/")[-1]
        _conversations.pop(conv_id, None)
        self._json({"ok": True})

    # ── Chat handler (SSE streaming) ──────────────────────

    def _handle_chat_message(self, body: dict):
        message = body.get("message", "")
        history = body.get("history", [])
        conv_id = body.get("conversation_id", "")

        if not conv_id:
            conv_id = str(int(time.time()))
            _conversations[conv_id] = []

        # Save user message
        user_msg = {"role": "user", "content": message, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}
        _conversations.setdefault(conv_id, []).append(user_msg)

        # Send conversation ID first
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        self._sse_send(json.dumps({"conversation_id": conv_id}))

        # Stream AI response
        loop = asyncio.new_event_loop()
        try:
            full_content = ""
            async def _stream():
                nonlocal full_content
                async for chunk in chat_stream(
                    message=message,
                    history=history,
                    api_key=self.config.get("ai_api_key", ""),
                    base_url=self.config.get("ai_base_url", ""),
                    model=self.config.get("ai_model", ""),
                    max_tokens=self.config.get("ai_max_tokens", 2048),
                    temperature=self.config.get("ai_temperature", 0.7),
                ):
                    self._sse_send(chunk)
                    try:
                        data = json.loads(chunk)
                        if "token" in data:
                            full_content += data["token"]
                    except json.JSONDecodeError:
                        pass

            loop.run_until_complete(_stream())

            # Save assistant message
            assistant_msg = {"role": "assistant", "content": full_content, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}
            _conversations.setdefault(conv_id, []).append(assistant_msg)

            self._sse_send("[DONE]")
        except Exception as e:
            self._sse_send(json.dumps({"error": str(e)}))
        finally:
            loop.close()

    def _sse_send(self, data: str):
        self.wfile.write(f"data: {data}\n\n".encode("utf-8"))
        self.wfile.flush()

    # ── Helper methods ────────────────────────────────────

    def _json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _get_config_response(self) -> dict:
        c = self.config
        key = c.get("ai_api_key", "")
        masked = key[:4] + "***" + key[-4:] if len(key) > 8 else "***"
        return {
            "ai_api_key": masked,
            "ai_base_url": c.get("ai_base_url", ""),
            "ai_model": c.get("ai_model", ""),
            "ai_provider": "openai_compatible",
            "tavily_api_key": "***" if c.get("tavily_api_key") else "",
            "twelvedata_api": "",
            "rag_persist_dir": "",
            "market_refresh_interval": c.get("market_refresh_interval", 60),
            "news_refresh_interval": c.get("news_refresh_interval", 300),
            "configured": bool(c.get("ai_api_key")),
        }

    def _update_config(self, body: dict):
        for key in ("ai_api_key", "ai_base_url", "ai_model", "tavily_api_key"):
            if key in body and body[key] is not None:
                self.config[key] = body[key]
        for key in ("ai_max_tokens", "market_refresh_interval", "news_refresh_interval"):
            if key in body and body[key] is not None:
                self.config[key] = int(body[key])
        if "ai_temperature" in body and body["ai_temperature"] is not None:
            self.config["ai_temperature"] = float(body["ai_temperature"])

    def _test_connection(self, body: dict) -> dict:
        import httpx
        api_key = body.get("api_key", self.config.get("ai_api_key", ""))
        base_url = body.get("base_url", self.config.get("ai_base_url", ""))
        model = body.get("model", self.config.get("ai_model", ""))
        try:
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            resp = httpx.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json={"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5},
                timeout=15,
            )
            if resp.status_code == 200:
                return {"ok": True, "message": f"连接成功！模型 {model} 响应正常。"}
            return {"ok": False, "message": f"连接失败 (HTTP {resp.status_code})"}
        except Exception as e:
            return {"ok": False, "message": f"连接失败: {str(e)[:100]}"}

    def _get_models(self) -> dict:
        import httpx
        c = self.config
        try:
            headers = {}
            if c.get("ai_api_key"):
                headers["Authorization"] = f"Bearer {c['ai_api_key']}"
            resp = httpx.get(f"{c['ai_base_url'].rstrip('/')}/models", headers=headers, timeout=10)
            if resp.status_code == 200:
                models = [m.get("id", "") for m in resp.json().get("data", [])]
                return {"current": c.get("ai_model", ""), "models": [m for m in models if m]}
        except Exception:
            pass
        return {"current": c.get("ai_model", ""), "models": [c.get("ai_model", "")]}

    def _get_tools(self) -> list:
        return [
            {"name": "get_market_overview", "description": "获取全球所有主要市场的实时行情数据"},
            {"name": "get_latest_news", "description": "获取最新的财经新闻和市场资讯"},
            {"name": "get_market_status", "description": "获取全球各主要市场当前的开盘/收盘状态"},
        ]

    def _get_skills(self) -> list:
        return [
            {"id": "risk_warning", "name": "风险提示", "description": "每次回复末尾自动添加风险提示", "enabled": True},
            {"id": "technical_analysis", "name": "技术分析", "description": "在分析市场时加入技术指标分析", "enabled": True},
            {"id": "macro_perspective", "name": "宏观视角", "description": "分析时加入宏观经济因素考量", "enabled": False},
        ]

    def _get_kline_stub(self, symbol: str, period: str) -> dict:
        return {"dates": [], "opens": [], "highs": [], "lows": [], "closes": [], "volumes": [], "name": symbol}

    def _get_market_status(self) -> dict:
        return {
            "utc_time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "any_open": True,
            "markets": {"A股": True, "港股": True, "美股": True, "日股": True, "韩股": True, "欧洲": True, "大宗商品": True},
        }

    def log_message(self, format, *args):
        pass  # Suppress request logging


# ── Server entry point ────────────────────────────────────

def run_server(port: int = 8000):
    """Start the Android HTTP server."""
    config = _load_config()

    # Find frontend dist directory
    dist_dir = os.path.join(APP_DIR, "frontend", "dist")
    if not os.path.isdir(dist_dir):
        dist_dir = os.path.join(APP_DIR, "dist")
    if not os.path.isdir(dist_dir):
        dist_dir = os.path.join(os.path.dirname(APP_DIR), "frontend", "dist")
    if not os.path.isdir(dist_dir):
        dist_dir = APP_DIR  # fallback

    AndroidHandler.config = config
    AndroidHandler.dist_dir = dist_dir

    server = ThreadingHTTPServer(("127.0.0.1", port), AndroidHandler)
    print(f"[Android] Server started on http://127.0.0.1:{port}")
    print(f"[Android] Serving frontend: {dist_dir}")
    print(f"[Android] AI Model: {config.get('ai_model', 'unknown')}")
    server.serve_forever()
