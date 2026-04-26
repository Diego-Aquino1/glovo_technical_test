import time
from datetime import date
from typing import Any

import httpx

from app.audit.logger import audit_logger
from app.erp_client import erp_client
from app.security.rbac import check_permission
from app.security.validator import validate_role, validate_sku
from app.semantic.layer import semantic_layer


async def get_pending_replenishments(
    sku: str,
    user_role: str = "viewer",
    session_id: str | None = None,
) -> dict[str, Any]:
    """
    Obtiene las órdenes de compra pendientes para un SKU y detecta
    fechas de reposición vencidas que podrían indicar inconsistencias en el ERP.

    Las órdenes con fecha estimada anterior a hoy se marcan como VENCIDAS.
    El agente debe incluir una alerta explícita en su respuesta cuando
    has_overdue_orders sea True, ya que las fechas de entrega no son confiables.

    Args:
        sku: Código del artículo a consultar.
        user_role: Rol del usuario ('viewer', 'manager', 'admin').
        session_id: ID de sesión para trazabilidad.

    Returns:
        Diccionario con:
        - sku (str): SKU consultado.
        - orders (list): Lista de órdenes ordenadas por fecha estimada.
          Cada orden incluye: pending_quantity, estimated_date, supplier,
          order_status, is_overdue (bool).
        - has_overdue_orders (bool): True si alguna orden tiene fecha pasada.
        - overdue_count (int): Número de órdenes vencidas.
        - overdue_detail (str | None): Descripción de la situación de órdenes vencidas.
        - total_pending_future (float): Cantidad total en órdenes con fecha futura válida.
    """
    start = time.monotonic()
    input_params: dict[str, Any] = {"sku": sku, "user_role": user_role, "session_id": session_id}
    today = date.today()

    semantic_layer.assert_read_only("SELECT")

    try:
        normalized_sku = validate_sku(sku)
        normalized_role = validate_role(user_role)
        check_permission(normalized_role, "get_pending_replenishments")
    except (ValueError, PermissionError) as exc:
        return {"error": str(exc), "status": "validation_error"}

    try:
        all_rows = await erp_client.get_all_pages("/purchase-orders", {"sku": normalized_sku})
    except httpx.HTTPError as exc:
        return {"error": f"ERP Service no disponible: {exc}", "status": "service_error"}

    if not all_rows:
        result: dict[str, Any] = {
            "sku": normalized_sku,
            "orders": [],
            "has_overdue_orders": False,
            "overdue_count": 0,
            "overdue_detail": None,
            "total_pending_future": 0.0,
            "message": f"No hay órdenes de compra pendientes para '{normalized_sku}'.",
        }
        await audit_logger.log(
            tool_called="get_pending_replenishments",
            input_params=input_params,
            output_summary="no_orders",
            latency_ms=int((time.monotonic() - start) * 1000),
            session_id=session_id,
            user_role=user_role,
        )
        return semantic_layer.enrich_response(result)

    enriched_orders = []
    for row in sorted(all_rows, key=lambda x: x["estimated_date"]):
        estimated = date.fromisoformat(row["estimated_date"])
        is_overdue = estimated < today
        enriched_orders.append(
            {
                "pending_quantity": float(row["pending_quantity"]),
                "estimated_date": row["estimated_date"],
                "supplier": row["supplier"],
                "order_status": row["order_status"],
                "is_overdue": is_overdue,
            }
        )

    overdue_orders = [o for o in enriched_orders if o["is_overdue"]]
    future_orders = [o for o in enriched_orders if not o["is_overdue"]]
    has_overdue = len(overdue_orders) > 0
    total_pending_future = sum(o["pending_quantity"] for o in future_orders)

    overdue_detail: str | None = None
    if has_overdue:
        overdue_detail = (
            f"ALERTA: {len(overdue_orders)} orden(es) tienen fecha de entrega vencida "
            f"(anterior a {today.isoformat()}). "
            f"Cantidades afectadas: {sum(o['pending_quantity'] for o in overdue_orders):.0f} uds. "
            "Las fechas comprometidas basadas en estas órdenes NO son confiables. "
            "Se recomienda verificar directamente con los proveedores."
        )

    result = {
        "sku": normalized_sku,
        "orders": enriched_orders,
        "has_overdue_orders": has_overdue,
        "overdue_count": len(overdue_orders),
        "overdue_detail": overdue_detail,
        "total_pending_future": total_pending_future,
        "message": (
            f"{'AVISO: ' + overdue_detail + ' ' if has_overdue else ''}"
            f"Reposiciones futuras válidas: {total_pending_future:.0f} uds en "
            f"{len(future_orders)} orden(es)."
        ),
    }

    latency_ms = int((time.monotonic() - start) * 1000)
    await audit_logger.log(
        tool_called="get_pending_replenishments",
        input_params=input_params,
        output_summary=(
            f"total_orders={len(enriched_orders)}, overdue={len(overdue_orders)}, "
            f"future_qty={total_pending_future}"
        ),
        latency_ms=latency_ms,
        session_id=session_id,
        user_role=user_role,
        has_overdue=has_overdue,
    )

    return semantic_layer.enrich_response(result)
