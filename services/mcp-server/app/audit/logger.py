import json
import logging
from typing import Any

import asyncpg

from app.config import settings

logger = logging.getLogger(__name__)


class AuditLogger:
    _pool: asyncpg.Pool | None = None

    async def initialize(self) -> None:
        self._pool = await asyncpg.create_pool(
            settings.database_url_asyncpg,
            min_size=1,
            max_size=5,
            command_timeout=10,
        )

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def log(
        self,
        tool_called: str,
        input_params: dict[str, Any],
        output_summary: str | None = None,
        latency_ms: int | None = None,
        session_id: str | None = None,
        user_role: str | None = None,
        has_overdue: bool = False,
    ) -> None:
        if self._pool is None:
            logger.warning("[audit] Pool no disponible, registro omitido: tool=%s", tool_called)
            return

        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO audit_logs
                        (tool_called, input_params, output_summary, latency_ms,
                         session_id, user_role, has_overdue)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    tool_called,
                    json.dumps(input_params),
                    output_summary,
                    latency_ms,
                    session_id,
                    user_role,
                    has_overdue,
                )
        except Exception as exc:
            logger.error("[audit] Error al escribir registro: %s", exc)


audit_logger = AuditLogger()
