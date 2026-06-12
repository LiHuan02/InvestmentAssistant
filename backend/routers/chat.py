from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from backend.models.chat import ChatRequest, QuickCommand

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/message")
async def send_message(request_body: ChatRequest, request: Request):
    service = request.app.state.chat_service

    async def event_stream():
        try:
            async for event_json in service.stream_message(
                request_body.message, request_body.history
            ):
                yield f"data: {event_json}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f'data: {{"error": "{str(e)}"}}\n\n'

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
