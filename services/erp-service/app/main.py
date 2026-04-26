from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.routers import articles, purchase_orders, stock


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="Mini ERP Service — expone artículos, stocks y órdenes de compra con paginación.",
    lifespan=lifespan,
)

app.include_router(articles.router, prefix="/articles", tags=["articles"])
app.include_router(stock.router, prefix="/stock", tags=["stock"])
app.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["purchase-orders"])


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok", "service": settings.app_title}
