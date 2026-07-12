import json
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from backend.runtime_paths import runtime_file

logger = logging.getLogger(__name__)

DB_FILE = runtime_file("data/conversations.db")


def _get_conn() -> sqlite3.Connection:
    Path(DB_FILE).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL DEFAULT '新对话',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tool_calls TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_updated ON conversations(updated_at DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id)")
    conn.commit()
    return conn


def create_conversation(title: str = "新对话") -> dict:
    conn = _get_conn()
    now = datetime.utcnow().isoformat()
    conv_id = str(uuid.uuid4())[:8]
    conn.execute(
        "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (conv_id, title, now, now),
    )
    conn.commit()
    conn.close()
    return {"id": conv_id, "title": title, "created_at": now, "updated_at": now}


def list_conversations(limit: int = 50) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_conversation(conv_id: str) -> dict | None:
    conn = _get_conn()
    row = conn.execute(
        "SELECT id, title, created_at, updated_at FROM conversations WHERE id = ?", (conv_id,)
    ).fetchone()
    if not row:
        conn.close()
        return None
    messages = conn.execute(
        "SELECT role, content, tool_calls, timestamp FROM messages WHERE conversation_id = ? ORDER BY id",
        (conv_id,),
    ).fetchall()
    conn.close()
    return {
        **dict(row),
        "messages": [
            {
                "role": m["role"],
                "content": m["content"],
                "timestamp": m["timestamp"],
                "toolCalls": json.loads(m["tool_calls"]) if m["tool_calls"] else None,
            }
            for m in messages
        ],
    }


def save_message(conv_id: str, role: str, content: str, tool_calls: list | None = None) -> None:
    conn = _get_conn()
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO messages (conversation_id, role, content, tool_calls, timestamp) VALUES (?, ?, ?, ?, ?)",
        (conv_id, role, content, json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None, now),
    )
    conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conv_id))
    conn.commit()
    conn.close()


def update_title(conv_id: str, title: str) -> None:
    conn = _get_conn()
    conn.execute("UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                 (title, datetime.utcnow().isoformat(), conv_id))
    conn.commit()
    conn.close()


def delete_conversation(conv_id: str) -> None:
    conn = _get_conn()
    conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
    conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    conn.commit()
    conn.close()


def auto_title(conv_id: str, first_message: str) -> str:
    title = first_message[:30].strip()
    if len(first_message) > 30:
        title += "..."
    update_title(conv_id, title)
    return title
