import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.core.event_bus import event_bus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/market")
async def ws_market(websocket: WebSocket):
    await websocket.accept()
    queue = event_bus.subscribe("market_update")
    try:
        while True:
            data = await queue.get()
            serialized = []
            for group in data.values():
                for idx in group:
                    serialized.append(idx.model_dump(mode="json"))
            await websocket.send_json(
                {
                    "type": "market_update",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": serialized,
                }
            )
    except WebSocketDisconnect:
        logger.info("Market WebSocket client disconnected")
    finally:
        event_bus.unsubscribe("market_update", queue)
