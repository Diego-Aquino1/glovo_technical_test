import uuid
from datetime import date, datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Article(Base):
    __tablename__ = "articles"

    sku: Mapped[str] = mapped_column(sa.String(20), primary_key=True)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    is_obsolete: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("false")
    )


class Stock(Base):
    __tablename__ = "stocks"
    __table_args__ = (sa.UniqueConstraint("sku", "warehouse", name="uq_sku_warehouse"),)

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(
        sa.String(20), sa.ForeignKey("articles.sku", ondelete="CASCADE"), nullable=False
    )
    warehouse: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    available_quantity: Mapped[Decimal] = mapped_column(
        sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")
    )
    location: Mapped[str | None] = mapped_column(sa.String(20), nullable=True)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(
        sa.String(20), sa.ForeignKey("articles.sku", ondelete="CASCADE"), nullable=False
    )
    pending_quantity: Mapped[Decimal] = mapped_column(sa.Numeric(12, 2), nullable=False)
    estimated_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    supplier: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    order_status: Mapped[str] = mapped_column(sa.String(20), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    user_role: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    tool_called: Mapped[str] = mapped_column(sa.Text, nullable=False)
    input_params: Mapped[dict] = mapped_column(JSONB, nullable=False)
    output_summary: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    has_overdue: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
