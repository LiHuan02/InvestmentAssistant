import json
import logging

from fastapi import APIRouter, Body, Request

logger = logging.getLogger(__name__)
from fastapi.responses import StreamingResponse

from backend.config import get_settings
from backend.models.chat import ChatRequest, QuickCommand
from backend.services import history_service

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/message")
async def send_message(request_body: ChatRequest, request: Request):
    service = request.app.state.chat_service

    conv_id = request_body.conversation_id
    if not conv_id:
        conv = history_service.create_conversation()
        conv_id = conv["id"]
        history_service.auto_title(conv_id, request_body.message)

    history_service.save_message(conv_id, "user", request_body.message)

    async def event_stream():
        full_content = ""
        tool_calls = []
        try:
            yield f'data: {json.dumps({"conversation_id": conv_id})}\n\n'
            async for event_json in service.stream_message(
                request_body.message, request_body.history
            ):
                yield f"data: {event_json}\n\n"
                try:
                    ev = json.loads(event_json)
                    if "token" in ev:
                        full_content += ev["token"]
                    elif "tool_start" in ev:
                        tool_calls.append({
                            "name": ev["tool_start"]["name"],
                            "input": ev["tool_start"].get("input", ""),
                            "status": "running",
                        })
                    elif "tool_end" in ev:
                        for tc in tool_calls:
                            if tc["name"] == ev["tool_end"]["name"] and tc["status"] == "running":
                                tc["output"] = ev["tool_end"].get("output", "")
                                tc["status"] = "done"
                                break
                except (json.JSONDecodeError, KeyError):
                    pass
            if full_content:
                history_service.save_message(
                    conv_id, "assistant", full_content,
                    tool_calls if tool_calls else None
                )
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f'data: {json.dumps({"error": str(e)})}\n\n'

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/commands")
async def get_commands(request: Request) -> list[QuickCommand]:
    service = request.app.state.chat_service
    return service.get_commands()


@router.get("/config")
async def get_config():
    s = get_settings()
    return {
        "model": s.ai_model,
        "base_url": s.ai_base_url,
        "max_tokens": s.ai_max_tokens,
        "temperature": s.ai_temperature,
        "tavily_enabled": bool(s.tavily_api_key),
        "rag_enabled": bool(s.rag_persist_dir),
        "market_refresh": s.market_refresh_interval,
        "news_refresh": s.news_refresh_interval,
    }


@router.get("/models")
async def list_models():
    import requests as req
    s = get_settings()
    models = []
    try:
        url = f"{s.ai_base_url.rstrip('/')}/models"
        headers = {}
        if s.ai_api_key:
            headers["Authorization"] = f"Bearer {s.ai_api_key}"
        resp = req.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for m in data.get("data", []):
                model_id = m.get("id", "")
                if model_id:
                    models.append(model_id)
    except Exception as e:
        logger.warning("获取模型列表失败: %s", e)
    return {"current": s.ai_model, "models": models}


@router.post("/config")
async def update_config(payload: dict = Body(...), request: Request = None):
    s = get_settings()
    updated = {}
    if "model" in payload:
        s.ai_model = str(payload["model"])
        updated["model"] = s.ai_model
    if "temperature" in payload:
        val = float(payload["temperature"])
        if 0 <= val <= 2:
            s.ai_temperature = val
            updated["temperature"] = s.ai_temperature
    if "max_tokens" in payload:
        val = int(payload["max_tokens"])
        if 256 <= val <= 16384:
            s.ai_max_tokens = val
            updated["max_tokens"] = s.ai_max_tokens
    if request and updated:
        try:
            request.app.state.chat_service.reload()
        except Exception as e:
            logger.warning("Agent 重载失败: %s", e)
    return {"updated": updated}


@router.get("/tools")
async def list_tools(request: Request):
    service = request.app.state.chat_service
    tools = []
    for t in service._tools:
        tools.append({
            "name": getattr(t, "name", str(t)),
            "description": getattr(t, "description", "")[:100],
        })
    return tools


@router.get("/mcp")
async def list_mcp(request: Request):
    service = request.app.state.chat_service
    return service.mcp_list()


@router.post("/mcp/add")
async def add_mcp(payload: dict = Body(...)):
    service_cls = type(get_settings())  # just to access ChatService class methods
    from backend.services.chat_service import ChatService
    result = ChatService.mcp_add(
        name=payload.get("name", ""),
        transport=payload.get("transport", "stdio"),
        url=payload.get("url", ""),
        command=payload.get("command", ""),
        args=payload.get("args"),
    )
    return result


@router.post("/mcp/remove")
async def remove_mcp(payload: dict = Body(...)):
    from backend.services.chat_service import ChatService
    return ChatService.mcp_remove(payload.get("name", ""))


@router.post("/mcp/reload")
async def reload_mcp(request: Request):
    service = request.app.state.chat_service
    return service.reload()


# ── Skills ────────────────────────────────────────────────────

@router.get("/skills")
async def list_skills():
    from backend.services import skills_service
    return skills_service.list_skills()


@router.post("/skill/add")
async def add_skill(payload: dict = Body(...), request: Request = None):
    from backend.services import skills_service
    result = skills_service.add_skill(
        name=payload.get("name", ""),
        description=payload.get("description", ""),
        prompt=payload.get("prompt", ""),
    )
    if "error" not in result and request:
        request.app.state.chat_service.reload()
    return result


@router.post("/skill/remove")
async def remove_skill(payload: dict = Body(...), request: Request = None):
    from backend.services import skills_service
    result = skills_service.remove_skill(payload.get("id", ""))
    if "error" not in result and request:
        request.app.state.chat_service.reload()
    return result


@router.post("/skill/toggle")
async def toggle_skill(payload: dict = Body(...), request: Request = None):
    from backend.services import skills_service
    result = skills_service.toggle_skill(
        payload.get("id", ""),
        payload.get("enabled", True),
    )
    if "error" not in result and request:
        request.app.state.chat_service.reload()
    return result
