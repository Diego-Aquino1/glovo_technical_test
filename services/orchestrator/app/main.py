import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.agent.orchestrator import process_query
from app.config import settings
from app.history.redis_history import ChatHistoryManager
from app.schemas import QueryRequest, QueryResponse, generate_session_id

logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)
logger = logging.getLogger(__name__)

chat_history = ChatHistoryManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[orchestrator] Inicializando historial Redis...")
    await chat_history.initialize()
    logger.info("[orchestrator] Listo.")
    yield
    await chat_history.close()


app = FastAPI(
    title="Orchestrator Service",
    version="0.1.0",
    description="Agente orquestador que interpreta preguntas de negocio y ejecuta el DAG de tools MCP.",
    lifespan=lifespan,
)


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    if not request.query.strip():
        raise HTTPException(status_code=422, detail="La consulta no puede estar vacía.")

    session_id = request.session_id or generate_session_id()

    result = await process_query(
        query=request.query,
        session_id=session_id,
        user_role=request.user_role,
        history_manager=chat_history,
    )

    return QueryResponse(
        answer=result["answer"],
        session_id=session_id,
        tool_calls_made=result["tool_calls_made"],
        error=result["error"],
    )


@app.delete("/sessions/{session_id}", status_code=204)
async def clear_session(session_id: str) -> None:
    await chat_history.clear(session_id)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok", "service": "orchestrator"}
