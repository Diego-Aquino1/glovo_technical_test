import logging
import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.middleware.auth import require_api_key

logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)
logger = logging.getLogger(__name__)

_http_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _http_client
    _http_client = httpx.AsyncClient(
        base_url=settings.orchestrator_url,
        timeout=settings.proxy_timeout,
        follow_redirects=True,
    )
    logger.info("[api-gateway] Proxy configurado hacia %s", settings.orchestrator_url)
    yield
    if _http_client:
        await _http_client.aclose()


app = FastAPI(
    title="API Gateway",
    version="0.1.0",
    description=(
        "Punto de entrada público del Asistente de Compromiso de Stock. "
        "Autenticación mediante header `X-API-Key`."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.post("/query")
async def proxy_query(
    request: Request,
    user_role: str = Depends(require_api_key),
) -> JSONResponse:
    request_id = str(uuid.uuid4())[:8]

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El cuerpo de la petición debe ser JSON válido.",
        )

    body["user_role"] = user_role

    logger.info(
        "[api-gateway] req=%s role=%s query_preview='%s...'",
        request_id,
        user_role,
        str(body.get("query", ""))[:60],
    )

    try:
        response = await _http_client.post("/query", json=body)
        response.raise_for_status()
    except httpx.TimeoutException:
        logger.error("[api-gateway] req=%s Timeout al contactar el orchestrator", request_id)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="El agente tardó demasiado en responder. Intenta de nuevo.",
        )
    except httpx.HTTPStatusError as exc:
        logger.error(
            "[api-gateway] req=%s Error upstream: %s", request_id, exc.response.status_code
        )
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Error en el servicio de IA: {exc.response.text}",
        )
    except httpx.HTTPError as exc:
        logger.error("[api-gateway] req=%s Orchestrator no disponible: %s", request_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de IA no está disponible en este momento.",
        )

    logger.info("[api-gateway] req=%s completado OK", request_id)
    return JSONResponse(content=response.json(), status_code=response.status_code)


@app.delete("/sessions/{session_id}", status_code=204)
async def clear_session(
    session_id: str,
    user_role: str = Depends(require_api_key),
) -> None:
    try:
        await _http_client.delete(f"/sessions/{session_id}")
    except httpx.HTTPError:
        pass


@app.get("/health")
async def health_check() -> dict:
    orchestrator_ok = False
    try:
        resp = await _http_client.get("/health", timeout=5.0)
        orchestrator_ok = resp.status_code == 200
    except Exception:
        pass

    return {
        "status": "ok",
        "service": "api-gateway",
        "orchestrator_reachable": orchestrator_ok,
    }
