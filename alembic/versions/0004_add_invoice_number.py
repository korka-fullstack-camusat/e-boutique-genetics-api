"""Add sequential invoice_number to orders

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-23 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("invoice_number", sa.Integer(), nullable=True))
    op.create_unique_constraint("uq_orders_invoice_number", "orders", ["invoice_number"])


def downgrade() -> None:
    op.drop_constraint("uq_orders_invoice_number", "orders", type_="unique")
    op.drop_column("orders", "invoice_number")
