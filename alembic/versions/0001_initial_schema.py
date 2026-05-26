"""Initial schema — products, orders, order_items, surveys

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── products ────────────────────────────────────────────────────────────
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("sous_category", sa.String(), nullable=True),
        sa.Column("stock", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("images", sa.JSON(), nullable=True),
        sa.Column("sizes", sa.JSON(), nullable=True),
        sa.Column("colors", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_id", "products", ["id"])
    op.create_index("ix_products_name", "products", ["name"])
    op.create_index("ix_products_category", "products", ["category"])
    op.create_index("ix_products_sous_category", "products", ["sous_category"])
    op.create_index("ix_products_created_at", "products", ["created_at"])

    # ── orders ──────────────────────────────────────────────────────────────
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_name", sa.String(), nullable=False),
        sa.Column("customer_email", sa.String(), nullable=False),
        sa.Column("customer_phone", sa.String(), nullable=True),
        sa.Column("customer_address", sa.Text(), nullable=True),
        sa.Column("payment_method", sa.String(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), server_default=sa.text("'pending'"), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_orders_id", "orders", ["id"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_created_at", "orders", ["created_at"])
    op.create_index("ix_orders_customer_email", "orders", ["customer_email"])

    # ── order_items ─────────────────────────────────────────────────────────
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("product_name", sa.String(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("size", sa.String(), nullable=True),
        sa.Column("color", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_items_id", "order_items", ["id"])
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])

    # ── surveys ─────────────────────────────────────────────────────────────
    op.create_table(
        "surveys",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("age", sa.String(), nullable=True),
        sa.Column("profession", sa.String(), nullable=True),
        sa.Column("style", sa.String(), nullable=True),
        sa.Column("brand", sa.String(), nullable=True),
        sa.Column("hobbies", sa.String(), nullable=True),
        sa.Column("monthly_budget", sa.String(), nullable=True),
        sa.Column("clothing_type", sa.String(), nullable=True),
        sa.Column("suggestions", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_surveys_id", "surveys", ["id"])
    op.create_index("ix_surveys_created_at", "surveys", ["created_at"])


def downgrade() -> None:
    op.drop_table("surveys")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("products")
