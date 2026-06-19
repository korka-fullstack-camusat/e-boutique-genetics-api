"""Add reference, marque, disponibilite to products

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-19 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("reference",     sa.String(), nullable=True))
    op.add_column("products", sa.Column("marque",        sa.String(), nullable=True))
    op.add_column("products", sa.Column("disponibilite", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "disponibilite")
    op.drop_column("products", "marque")
    op.drop_column("products", "reference")
