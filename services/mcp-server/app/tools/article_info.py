import time
from typing import Any

import httpx

from app.audit.logger import audit_logger
from app.erp_client import erp_client
from app.security.rbac import check_permission
from app.security.validator import validate_role, validate_sku
from app.semantic.layer import semantic_layer


async def get_article_info(
    sku: str,
    user_role: str = "viewer",
    session_id: str | None = None,
) -> dict[str, Any]:
    """
    Verifica si un artículo existe en el catálogo ERP y si está activo (no obsoleto).

    IMPORTANTE: Esta tool DEBE ser la primera en ejecutarse en cualquier flujo
    que consulte stock o reposiciones. Si el artículo no existe o está obsoleto,
    el agente debe detener el flujo e informar al usuario sin ejecutar más tools.

    Args:
        sku: Código único del artículo en el ERP (ej: 'ZAP-001').
        user_role: Rol del usuario que realiza la consulta ('viewer', 'manager', 'admin').
        session_id: Identificador de sesión de chat para trazabilidad en auditoría.

    Returns:
        Diccionario con:
        - exists (bool): True si el artículo está en el catálogo.
        - is_obsolete (bool | None): True si el artículo está descatalogado.
        - description (str | None): Descripción legible del artículo.
        - sku (str): SKU normalizado consultado.
    """
    start = time.monotonic()
    input_params: dict[str, Any] = {"sku": sku, "user_role": user_role, "session_id": session_id}

    semantic_layer.assert_read_only("SELECT")

    try:
        normalized_sku = validate_sku(sku)
        normalized_role = validate_role(user_role)
        check_permission(normalized_role, "get_article_info")
    except (ValueError, PermissionError) as exc:
        return {"error": str(exc), "status": "validation_error"}

    try:
        article = await erp_client.get_article(normalized_sku)
    except httpx.HTTPError as exc:
        return {"error": f"ERP Service no disponible: {exc}", "status": "service_error"}

    if article is None:
        result: dict[str, Any] = {
            "exists": False,
            "is_obsolete": None,
            "description": None,
            "sku": normalized_sku,
            "message": (
                f"El artículo '{normalized_sku}' no existe en el catálogo ERP. "
                "No continúes el flujo con este SKU."
            ),
        }
    else:
        result = {
            "exists": True,
            "is_obsolete": article["is_obsolete"],
            "description": article["description"],
            "sku": normalized_sku,
        }
        if article["is_obsolete"]:
            result["message"] = (
                f"El artículo '{normalized_sku}' está OBSOLETO y descatalogado. "
                "No puede comprometerse para nuevas ventas."
            )

    latency_ms = int((time.monotonic() - start) * 1000)
    await audit_logger.log(
        tool_called="get_article_info",
        input_params=input_params,
        output_summary=f"exists={result.get('exists')}, is_obsolete={result.get('is_obsolete')}",
        latency_ms=latency_ms,
        session_id=session_id,
        user_role=user_role,
    )

    return semantic_layer.enrich_response(result)
