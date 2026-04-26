import time
from typing import Any

import httpx

from app.audit.logger import audit_logger
from app.erp_client import erp_client
from app.security.rbac import check_permission
from app.security.validator import validate_role, validate_sku
from app.semantic.layer import semantic_layer

EXCLUDED_WAREHOUSES: frozenset[str] = frozenset({"ALM-RESERVADO"})


async def get_stock_availability(
    sku: str,
    user_role: str = "viewer",
    session_id: str | None = None,
) -> dict[str, Any]:
    """
    Devuelve el stock físico disponible por almacén para un SKU dado.

    Excluye automáticamente los almacenes reservados (ALM-RESERVADO) que no
    están disponibles para comprometer en nuevas ventas.
    Maneja paginación automáticamente para garantizar el dataset completo.

    Args:
        sku: Código del artículo a consultar (debe existir y no estar obsoleto).
        user_role: Rol del usuario ('viewer', 'manager', 'admin').
        session_id: ID de sesión para trazabilidad.

    Returns:
        Diccionario con:
        - sku (str): SKU consultado.
        - total_available (float): Suma de stock en almacenes disponibles.
        - by_warehouse (list): Detalle por almacén [{warehouse, available_quantity, location}].
        - excluded_warehouses (list): Almacenes excluidos del cálculo.
        - has_stock (bool): True si hay stock disponible.
    """
    start = time.monotonic()
    input_params: dict[str, Any] = {"sku": sku, "user_role": user_role, "session_id": session_id}

    semantic_layer.assert_read_only("SELECT")

    try:
        normalized_sku = validate_sku(sku)
        normalized_role = validate_role(user_role)
        check_permission(normalized_role, "get_stock_availability")
    except (ValueError, PermissionError) as exc:
        return {"error": str(exc), "status": "validation_error"}

    try:
        all_rows = await erp_client.get_all_pages("/stock", {"sku": normalized_sku})
    except httpx.HTTPError as exc:
        return {"error": f"ERP Service no disponible: {exc}", "status": "service_error"}

    available_rows = [r for r in all_rows if r["warehouse"] not in EXCLUDED_WAREHOUSES]
    excluded_rows = [r for r in all_rows if r["warehouse"] in EXCLUDED_WAREHOUSES]

    total_available: float = sum(float(r["available_quantity"]) for r in available_rows)

    by_warehouse = [
        {
            "warehouse": r["warehouse"],
            "available_quantity": float(r["available_quantity"]),
            "location": r.get("location"),
        }
        for r in sorted(available_rows, key=lambda x: x["warehouse"])
    ]

    excluded_warehouses = [r["warehouse"] for r in excluded_rows]

    result: dict[str, Any] = {
        "sku": normalized_sku,
        "total_available": total_available,
        "by_warehouse": by_warehouse,
        "excluded_warehouses": excluded_warehouses,
        "has_stock": total_available > 0,
        "message": (
            f"Stock disponible para '{normalized_sku}': {total_available} unidades "
            f"en {len(by_warehouse)} almacén(es). "
            + (
                f"ALM-RESERVADO excluido ({sum(float(r['available_quantity']) for r in excluded_rows)} uds)."
                if excluded_rows
                else ""
            )
        ),
    }

    latency_ms = int((time.monotonic() - start) * 1000)
    await audit_logger.log(
        tool_called="get_stock_availability",
        input_params=input_params,
        output_summary=f"total_available={total_available}, warehouses={len(by_warehouse)}",
        latency_ms=latency_ms,
        session_id=session_id,
        user_role=user_role,
    )

    return semantic_layer.enrich_response(result)
