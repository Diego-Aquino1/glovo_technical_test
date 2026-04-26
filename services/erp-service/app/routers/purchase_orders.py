from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import PurchaseOrder
from app.schemas import PaginatedResponse, PurchaseOrderResponse

router = APIRouter()

VALID_STATUSES = {"CONFIRMADO", "PENDIENTE", "TRANSITO", "SOLICITADO"}


@router.get("", response_model=PaginatedResponse[PurchaseOrderResponse])
async def list_purchase_orders(
    sku: str | None = Query(None, description="Filtrar por SKU"),
    status: str | None = Query(None, description="Filtrar por estado del pedido"),
    page: int = Query(1, ge=1, description="Número de página (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Resultados por página"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[PurchaseOrderResponse]:
    query = select(PurchaseOrder)
    if sku is not None:
        query = query.where(PurchaseOrder.sku == sku.strip().upper())
    if status is not None:
        query = query.where(PurchaseOrder.order_status == status.strip().upper())

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = total_result.scalar() or 0

    offset = (page - 1) * size
    result = await db.execute(
        query.order_by(PurchaseOrder.estimated_date).offset(offset).limit(size)
    )
    items = list(result.scalars().all())

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size if total > 0 else 0,
    )
