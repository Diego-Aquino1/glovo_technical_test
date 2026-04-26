from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Stock
from app.schemas import PaginatedResponse, StockResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[StockResponse])
async def list_stock(
    sku: str | None = Query(None, description="Filtrar por SKU"),
    warehouse: str | None = Query(None, description="Filtrar por almacén"),
    page: int = Query(1, ge=1, description="Número de página (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Resultados por página"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[StockResponse]:
    query = select(Stock)
    if sku is not None:
        query = query.where(Stock.sku == sku.strip().upper())
    if warehouse is not None:
        query = query.where(Stock.warehouse == warehouse.strip().upper())

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = total_result.scalar() or 0

    offset = (page - 1) * size
    result = await db.execute(query.order_by(Stock.sku, Stock.warehouse).offset(offset).limit(size))
    items = list(result.scalars().all())

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size if total > 0 else 0,
    )
