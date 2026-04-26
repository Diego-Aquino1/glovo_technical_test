import logging
from dataclasses import dataclass
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.interceptors import MCPToolCallRequest
from langchain_openai import ChatOpenAI

from app.agent.prompts import build_system_prompt
from app.config import settings
from app.history.redis_history import ChatHistoryManager

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    user_role: str
    session_id: str | None


async def inject_context(request: MCPToolCallRequest, handler):
    ctx: AgentContext = request.runtime.context
    modified_request = request.override(
        args={
            **request.args,
            "user_role": getattr(ctx, "user_role", "viewer"),
            "session_id": getattr(ctx, "session_id", None),
        }
    )
    return await handler(modified_request)


_llm: ChatOpenAI | None = None
_mcp_client: MultiServerMCPClient | None = None


def get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
            max_retries=3,
        )
    return _llm


def get_mcp_client() -> MultiServerMCPClient:
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MultiServerMCPClient(
            {
                "erp": {
                    "transport": "http",
                    "url": settings.mcp_server_url,
                }
            },
            tool_interceptors=[inject_context],
        )
    return _mcp_client


def _extract_tool_calls(messages: list[BaseMessage]) -> list[str]:
    tool_names: list[str] = []
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                name = tc.get("name") or tc.get("function", {}).get("name", "")
                if name and name not in tool_names:
                    tool_names.append(name)
    return tool_names


async def process_query(
    query: str,
    session_id: str,
    user_role: str,
    history_manager: ChatHistoryManager,
) -> dict[str, Any]:
    llm = get_llm()
    client = get_mcp_client()

    history: list[BaseMessage] = await history_manager.get_messages(session_id)
    messages_to_send: list[BaseMessage] = [*history, HumanMessage(content=query)]

    try:
        tools = await client.get_tools()
        logger.debug("[orchestrator] Tools MCP cargadas: %s", [t.name for t in tools])
    except Exception as exc:
        logger.exception("[orchestrator] Error cargando tools MCP: %s", exc)
        return {
            "answer": "No se pudo conectar con el servidor de datos.",
            "tool_calls_made": [],
            "error": True,
        }

    try:
        agent = create_agent(
            llm,
            tools,
            system_prompt=build_system_prompt(user_role),
            context_schema=AgentContext,
        )

        result = await agent.ainvoke(
            {"messages": messages_to_send},
            context=AgentContext(user_role=user_role, session_id=session_id),
            config={"recursion_limit": settings.agent_max_iterations},
        )

    except Exception as exc:
        logger.exception("[orchestrator] Error al ejecutar el agente: %s", exc)
        return {
            "answer": (
                "Lo siento, ocurrió un error al procesar tu consulta. "
                "Por favor, inténtalo de nuevo en unos momentos."
            ),
            "tool_calls_made": [],
            "error": True,
        }

    final_messages: list[BaseMessage] = result.get("messages", [])
    answer = ""
    for msg in reversed(final_messages):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            answer = str(msg.content)
            break

    if not answer:
        answer = "No pude generar una respuesta. Por favor, reformula la pregunta."

    tool_calls_made = _extract_tool_calls(final_messages)

    await history_manager.add_turn(session_id, query, answer)

    logger.info(
        "[orchestrator] session=%s tools=%s answer_len=%d",
        session_id,
        tool_calls_made,
        len(answer),
    )

    return {
        "answer": answer,
        "tool_calls_made": tool_calls_made,
        "error": False,
    }
