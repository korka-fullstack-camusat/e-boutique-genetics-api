"""Add delivery and payment fields to orders

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("delivery_method", sa.String(),  nullable=True))
    op.add_column("orders", sa.Column("delivery_fee",    sa.Float(),   nullable=True, server_default=sa.text("0")))
    op.add_column("orders", sa.Column("acompte_amount",  sa.Float(),   nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "acompte_amount")
    op.drop_column("orders", "delivery_fee")
    op.drop_column("orders", "delivery_method")
