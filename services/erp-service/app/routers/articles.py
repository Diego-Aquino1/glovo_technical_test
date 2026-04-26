from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Article
from app.schemas import ArticleResponse, PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ArticleResponse])
async def list_articles(
    sku: str | None = Query(None, description="Filtrar por SKU exacto"),
    is_obsolete: bool | None = Query(None, description="Filtrar por estado de obsolescencia"),
    page: int = Query(1, ge=1, description="Número de página (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Resultados por página"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ArticleResponse]:
    query = select(Article)
    if sku is not None:
        query = query.where(Article.sku == sku.strip().upper())
    if is_obsolete is not None:
        query = query.where(Article.is_obsolete == is_obsolete)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total: int = total_result.scalar() or 0

    offset = (page - 1) * size
    result = await db.execute(query.order_by(Article.sku).offset(offset).limit(size))
    items = list(result.scalars().all())

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size if total > 0 else 0,
    )


@router.get("/{sku}", response_model=ArticleResponse)
async def get_article(
    sku: str,
    db: AsyncSession = Depends(get_db),
) -> ArticleResponse:
    result = await db.execute(select(Article).where(Article.sku == sku.strip().upper()))
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail=f"Artículo '{sku}' no encontrado.")
    return article
