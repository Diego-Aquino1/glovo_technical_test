import uuid

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        description="Pregunta de negocio en lenguaje natural.",
        examples=["¿Cuándo podré entregar 500 unidades del producto 'ZAP-001' al cliente 'GARCIA SA'?"],
    )
    session_id: str | None = Field(
        default=None,
        description="ID de sesión para mantener el historial de conversación. Se genera automáticamente si no se proporciona.",
    )
    user_role: str = Field(
        default="viewer",
        description="Rol del usuario para aplicar RBAC en el MCP Server.",
    )


class QueryResponse(BaseModel):
    answer: str = Field(description="Respuesta generada por el agente.")
    session_id: str = Field(description="ID de sesión (útil para continuar la conversación).")
    tool_calls_made: list[str] = Field(
        default_factory=list,
        description="Nombres de las tools MCP invocadas durante el razonamiento.",
    )
    error: bool = Field(default=False, description="True si ocurrió un error al procesar la consulta.")


def generate_session_id() -> str:
    return str(uuid.uuid4())
