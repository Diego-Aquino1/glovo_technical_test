import json
import logging
from typing import Any

import redis.asyncio as aioredis
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.config import settings

logger = logging.getLogger(__name__)


class ChatHistoryManager:
    def __init__(self) -> None:
        self._client: aioredis.Redis | None = None

    async def initialize(self) -> None:
        self._client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            encoding="utf-8",
        )
        try:
            await self._client.ping()
            logger.info("[history] Conectado a Redis en %s", settings.redis_url)
        except Exception as exc:
            logger.warning("[history] Redis no disponible: %s. Historial deshabilitado.", exc)
            self._client = None

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _key(self, session_id: str) -> str:
        return f"chat:{session_id}:messages"

    async def get_messages(self, session_id: str) -> list[BaseMessage]:
        if not self._client:
            return []
        try:
            raw = await self._client.get(self._key(session_id))
            if not raw:
                return []
            data: list[dict[str, Any]] = json.loads(raw)
            messages: list[BaseMessage] = []
            for item in data:
                if item.get("role") == "human":
                    messages.append(HumanMessage(content=item["content"]))
                elif item.get("role") == "ai":
                    messages.append(AIMessage(content=item["content"]))
            return messages
        except Exception as exc:
            logger.warning("[history] Error al leer historial session=%s: %s", session_id, exc)
            return []

    async def add_turn(self, session_id: str, user_msg: str, ai_msg: str) -> None:
        if not self._client:
            return
        try:
            key = self._key(session_id)
            raw = await self._client.get(key)
            data: list[dict[str, Any]] = json.loads(raw) if raw else []

            data.append({"role": "human", "content": user_msg})
            data.append({"role": "ai", "content": ai_msg})

            max_msgs = settings.chat_history_max_messages
            if len(data) > max_msgs:
                data = data[-max_msgs:]

            await self._client.setex(
                key,
                settings.chat_history_ttl_seconds,
                json.dumps(data, ensure_ascii=False),
            )
        except Exception as exc:
            logger.warning("[history] Error al guardar historial session=%s: %s", session_id, exc)

    async def clear(self, session_id: str) -> None:
        if not self._client:
            return
        try:
            await self._client.delete(self._key(session_id))
        except Exception as exc:
            logger.warning("[history] Error al limpiar historial session=%s: %s", session_id, exc)
