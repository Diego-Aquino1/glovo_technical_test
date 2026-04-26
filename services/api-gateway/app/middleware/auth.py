import logging
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings

logger = logging.getLogger(__name__)

_api_key_header = APIKeyHeader(
    name="X-API-Key",
    description="API Key de autenticación. Requerida en todas las peticiones.",
    auto_error=False,
)


def _constant_time_compare(a: str, b: str) -> bool:
    return secrets.compare_digest(a.encode(), b.encode())


async def require_api_key(
    api_key: str | None = Security(_api_key_header),
) -> str:
    if not api_key:
        logger.warning("[auth] Petición sin header X-API-Key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida. Incluye el header X-API-Key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not _constant_time_compare(api_key, settings.api_gateway_key):
        logger.warning("[auth] API Key inválida (primeros 4 chars: %s...)", api_key[:4])
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key inválida o sin permisos.",
        )

    return settings.api_gateway_key_role
