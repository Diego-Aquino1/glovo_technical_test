"""Initial schema: articles, stocks, purchase_orders, audit_logs

Revision ID: 0001
Revises:
Create Date: 2026-04-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "articles",
        sa.Column("sku", sa.String(20), primary_key=True),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column(
            "is_obsolete",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.create_table(
        "stocks",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "sku",
            sa.String(20),
            sa.ForeignKey("articles.sku", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("warehouse", sa.String(50), nullable=False),
        sa.Column(
            "available_quantity",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("location", sa.String(20), nullable=True),
        sa.UniqueConstraint("sku", "warehouse", name="uq_sku_warehouse"),
    )

    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "sku",
            sa.String(20),
            sa.ForeignKey("articles.sku", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pending_quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("estimated_date", sa.Date, nullable=False),
        sa.Column("supplier", sa.String(100), nullable=False),
        sa.Column("order_status", sa.String(20), nullable=False),
    )
    op.create_index("ix_purchase_orders_sku", "purchase_orders", ["sku"])

    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("session_id", sa.Text, nullable=True),
        sa.Column("user_role", sa.Text, nullable=True),
        sa.Column("tool_called", sa.Text, nullable=False),
        sa.Column("input_params", JSONB, nullable=False),
        sa.Column("output_summary", sa.Text, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column(
            "has_overdue",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_audit_logs_tool_called", "audit_logs", ["tool_called"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_index("ix_purchase_orders_sku", table_name="purchase_orders")
    op.drop_table("purchase_orders")
    op.drop_table("stocks")
    op.drop_table("articles")
