"""Prix d'achat (bénéfice) et réglages globaux (mode maintenance)

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-27 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("cost_price", sa.Float(), nullable=True))
    op.add_column("order_items", sa.Column("unit_cost", sa.Float(), nullable=True))
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(), primary_key=True),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("app_settings")
    op.drop_column("order_items", "unit_cost")
    op.drop_column("products", "cost_price")
