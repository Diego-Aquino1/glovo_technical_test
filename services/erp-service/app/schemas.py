from datetime import date
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sku: str
    description: str
    is_obsolete: bool


class StockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    warehouse: str
    available_quantity: float
    location: str | None


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    pending_quantity: float
    estimated_date: date
    supplier: str
    order_status: str
