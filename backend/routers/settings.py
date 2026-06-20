import logging
import os
import re
from pathlib import Path

from fastapi import APIRouter, Body
from pydantic import BaseModel

from backend.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

ENV_FILE = Path(".env")


def _mask_key(key: str) -> str:
    if not key or len(key) < 8:
        return "***"
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


def _read_env() -> dict[str, str]:
    env = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _write_env_key(key: str, value: str) -> None:
    lines = []
    found = False
    if ENV_FILE.exists():
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith(f"{key}=") or stripped.startswith(f"# {key}="):
                    lines.append(f'{key}="{value}"\n')
                    found = True
                else:
                    lines.append(line)
    if not found:
        lines.append(f'\n{key}="{value}"\n')
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)


class SettingsResponse(BaseModel):
    ai_api_key: str
    ai_base_url: str
    ai_model: str
    ai_provider: str
    tavily_api_key: str
    twelvedata_api: str
    rag_persist_dir: str
    market_refresh_interval: int
    news_refresh_interval: int
    configured: bool


class SettingsUpdate(BaseModel):
    ai_api_key: str | None = None
    ai_base_url: str | None = None
    ai_model: str | None = None
    tavily_api_key: str | None = None
    twelvedata_api: str | None = None
    rag_persist_dir: str | None = None
    market_refresh_interval: int | None = None
    news_refresh_interval: int | None = None


class TestConnection(BaseModel):
    api_key: str = ""
    base_url: str = ""
    model: str = ""


@router.get("")
async def get_app_settings() -> SettingsResponse:
    s = get_settings()
    return SettingsResponse(
        ai_api_key=_mask_key(s.ai_api_key),
        ai_base_url=s.ai_base_url,
        ai_model=s.ai_model,
        ai_provider="openai_compatible",
        tavily_api_key=_mask_key(s.tavily_api_key),
        twelvedata_api=_mask_key(s.twelvedata_api),
        rag_persist_dir=s.rag_persist_dir,
        market_refresh_interval=s.market_refresh_interval,
        news_refresh_interval=s.news_refresh_interval,
        configured=bool(s.ai_api_key),
    )


@router.post("")
async def update_app_settings(payload: SettingsUpdate):
    s = get_settings()
    updated = {}

    field_map = {
        "ai_api_key": "AI_API_KEY",
        "ai_base_url": "AI_BASE_URL",
        "ai_model": "AI_MODEL",
        "tavily_api_key": "TAVILY_API_KEY",
        "twelvedata_api": "TWELVEDATA_API",
        "rag_persist_dir": "RAG_PERSIST_DIR",
    }

    for attr, env_key in field_map.items():
        val = getattr(payload, attr, None)
        if val is not None:
            setattr(s, attr, val)
            _write_env_key(env_key, val)
            updated[attr] = True

    if payload.market_refresh_interval is not None:
        s.market_refresh_interval = payload.market_refresh_interval
        _write_env_key("MARKET_REFRESH_INTERVAL", str(payload.market_refresh_interval))
        updated["market_refresh_interval"] = True

    if payload.news_refresh_interval is not None:
        s.news_refresh_interval = payload.news_refresh_interval
        _write_env_key("NEWS_REFRESH_INTERVAL", str(payload.news_refresh_interval))
        updated["news_refresh_interval"] = True

    return {"updated": list(updated.keys())}


@router.post("/test-connection")
async def test_connection(payload: TestConnection):
    import requests as req

    api_key = payload.api_key or get_settings().ai_api_key
    base_url = payload.base_url or get_settings().ai_base_url
    model = payload.model or get_settings().ai_model

    try:
        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        resp = req.post(
            url,
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 5,
            },
            timeout=15,
        )

        if resp.status_code == 200:
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {
                "ok": True,
                "message": f"连接成功！模型 {model} 响应正常。",
                "response": content[:50],
            }
        else:
            error_msg = resp.text[:200]
            return {"ok": False, "message": f"连接失败 (HTTP {resp.status_code}): {error_msg}"}
    except req.exceptions.Timeout:
        return {"ok": False, "message": "连接超时，请检查 Base URL 是否正确。"}
    except req.exceptions.ConnectionError:
        return {"ok": False, "message": "无法连接到服务器，请检查 Base URL。"}
    except Exception as e:
        return {"ok": False, "message": f"连接失败: {str(e)[:100]}"}
