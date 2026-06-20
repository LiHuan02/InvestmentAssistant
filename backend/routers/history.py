from fastapi import APIRouter
from pydantic import BaseModel

from backend.services import history_service

router = APIRouter(prefix="/api/v1/history", tags=["history"])


class TitleUpdate(BaseModel):
    title: str


@router.get("")
async def list_conversations(limit: int = 50):
    return history_service.list_conversations(limit)


@router.get("/{conv_id}")
async def get_conversation(conv_id: str):
    conv = history_service.get_conversation(conv_id)
    if not conv:
        return {"error": "对话不存在"}
    return conv


@router.post("")
async def create_conversation():
    return history_service.create_conversation()


@router.put("/{conv_id}/title")
async def update_title(conv_id: str, body: TitleUpdate):
    history_service.update_title(conv_id, body.title)
    return {"ok": True}


@router.delete("/{conv_id}")
async def delete_conversation(conv_id: str):
    history_service.delete_conversation(conv_id)
    return {"ok": True}
